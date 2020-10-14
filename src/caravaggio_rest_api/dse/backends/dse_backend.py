# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import re
import json

from caravaggio_rest_api.dse.backends.utils import DSEPaginator

from caravaggio_rest_api.haystack.backends.utils import SolrSearchPaginator
from django.db import connections
from haystack.utils.app_loading import haystack_get_model

from haystack.backends import BaseEngine
from caravaggio_rest_api.haystack.backends.solr_backend import CassandraSolrSearchBackend, CassandraSolrSearchQuery
from haystack.constants import DJANGO_CT, DJANGO_ID, DEFAULT_ALIAS, ID
from haystack.exceptions import MissingDependency
from haystack.models import SearchResult

from caravaggio_rest_api.haystack.backends import SolrSearchNode

try:
    from dse.util import Date
    from dse.query import SimpleStatement
    from dse import ConsistencyLevel
except ImportError:
    from cassandra.util import Date
    from cassandra.query import SimpleStatement
    from cassandra import ConsistencyLevel

try:
    from pysolr import Solr, SolrError, force_unicode, IS_PY3, DATETIME_REGEX
except ImportError:
    raise MissingDependency(
        "The 'solr' backend requires the installation" " of 'pysolr'. Please refer to the documentation."
    )

VALID_JSON_FACET_TYPES = ["terms", "query"]

DEFAULT_FETCH_SIZE = 500


class DSEBackend(CassandraSolrSearchBackend):
    def __init__(self, connection_alias, **connection_options):
        super(CassandraSolrSearchBackend, self).__init__(connection_alias, **connection_options)
        self.connection = connections["cassandra"]
        self.backup_implementation = CassandraSolrSearchBackend(connection_alias, **connection_options)

    def _process_results(
        self,
        raw_results,
        model=None,
        highlight=False,
        result_class=None,
        distance_point=None,
        percent_score=False,
        is_faceted=False,
    ):
        results = []
        if len(raw_results) == 1 and "rows_count" in raw_results[0]:
            hits = raw_results[0]["rows_count"]
        else:
            # we can't rely on the DSE response for the hits if we're not using the COUNT(*), that's why we set as 0 and
            # if we need the hits later we will do a COUNT(*) query.
            hits = 0
        facets = {}
        stats = {}
        spelling_suggestion = spelling_suggestions = None
        if is_faceted:
            assert len(raw_results) == 1, "Faceted searches should have only one result"
            raw_results = raw_results[0]

            facets["fields"] = json.loads(raw_results.get("facet_fields", "{}"))
            facets["dates"] = json.loads(raw_results.get("facet_dates", "{}"))
            facets["queries"] = json.loads(raw_results.get("facet_queries", "{}"))
            if "facet_heatmaps" in raw_results:
                facets["heatmaps"] = json.loads(raw_results.get("facet_heatmaps", "{}"))

        if result_class is None:
            result_class = SearchResult

        if hasattr(raw_results, "stats"):
            stats = raw_results.stats.get("stats_fields", {})

        if "facet_fields" in raw_results:
            for key in ["fields"]:
                for facet_field in facets[key]:
                    # Convert to a two-tuple, as Solr's json format returns a list of
                    # pairs.
                    facets[key][facet_field] = list(zip(facets[key][facet_field], facets[key][facet_field].values()))

        from haystack import connections

        unified_index = connections[self.connection_alias].get_unified_index()
        indexed_models = unified_index.get_indexed_models()

        if not is_faceted:
            for raw_result in raw_results:
                app_label, model_name = raw_result[DJANGO_CT].split(".")
                additional_fields = {}
                model = haystack_get_model(app_label, model_name)

                if model and model in indexed_models:
                    index = unified_index.get_index(model)
                    index_field_map = index.field_map
                    for key, value in raw_result.items():
                        string_key = str(key)
                        # re-map key if alternate name used
                        if string_key in index_field_map:
                            string_key = index_field_map[key]

                        if isinstance(value, Date):
                            value = str(value)

                        if string_key in index.fields and hasattr(index.fields[string_key], "convert"):
                            additional_fields[string_key] = index.fields[string_key].convert(value)
                        elif hasattr(model, string_key):
                            column = getattr(model, string_key)
                            if hasattr(column, "column"):
                                additional_fields[string_key] = column.column.to_python(value)
                            elif hasattr(column, "to_python"):
                                additional_fields[string_key] = column.to_python(value)
                            else:
                                additional_fields[string_key] = self.conn._to_python(value)
                        else:
                            additional_fields[string_key] = self.conn._to_python(value)

                    del additional_fields[DJANGO_CT]
                    del additional_fields[DJANGO_ID]
                    if "rows_count" in additional_fields:
                        del additional_fields["rows_count"]

                    if raw_result[ID] in getattr(raw_results, "highlighting", {}):
                        additional_fields["highlighted"] = raw_results.highlighting[raw_result[ID]]

                    if distance_point:
                        additional_fields["_point_of_origin"] = distance_point

                        if raw_result.get("__dist__"):
                            from haystack.utils.geo import Distance

                            additional_fields["_distance"] = Distance(km=float(raw_result["__dist__"]))
                        else:
                            additional_fields["_distance"] = None

                    additional_fields["already_loaded"] = True
                    if "score" not in additional_fields:
                        additional_fields["score"] = 1.0
                    result = result_class(app_label, model_name, raw_result[DJANGO_ID], **additional_fields)
                    results.append(result)

        results = {
            "results": results,
            "hits": hits,
            "stats": stats,
            "facets": facets,
            "spelling_suggestion": spelling_suggestion,
            "spelling_suggestions": spelling_suggestions,
        }

        if "facet_ranges" in raw_results:
            results["facets"]["ranges"] = {}
            ranges = json.loads(raw_results.get("facet_ranges", "{}"))

            if len(ranges):
                for field_name, range_data in ranges.items():
                    if field_name in self.date_facets:
                        results["facets"]["dates"][field_name] = tuple(
                            zip(range_data["counts"], range_data["counts"].values())
                        )
                    elif field_name in self.range_facets:
                        results["facets"]["ranges"][field_name] = tuple(
                            zip(range_data["counts"], range_data["counts"].values())
                        )

        return results

    def build_search_kwargs(
        self,
        query_string,
        sort_by=None,
        start_offset=0,
        end_offset=None,
        fields="",
        highlight=False,
        facets=None,
        date_facets=None,
        query_facets=None,
        range_facets=None,
        facets_options=None,
        narrow_queries=None,
        spelling_query=None,
        within=None,
        dwithin=None,
        distance_point=None,
        models=None,
        limit_to_registered_models=None,
        result_class=None,
        stats=None,
        collate=None,
        **extra_kwargs,
    ):

        if fields:
            # If we have fields that starts with _ we need to escape them for the CQL
            if isinstance(fields, (list, set)):
                fields = " ".join([f'"{field}"' for field in fields])

        kwargs = super().build_search_kwargs(
            query_string,
            sort_by=sort_by,
            start_offset=start_offset,
            end_offset=end_offset,
            fields=fields,
            highlight=highlight,
            facets=facets,
            date_facets=date_facets,
            query_facets=query_facets,
            narrow_queries=narrow_queries,
            spelling_query=spelling_query,
            within=within,
            dwithin=dwithin,
            distance_point=distance_point,
            models=models,
            limit_to_registered_models=limit_to_registered_models,
            result_class=result_class,
            stats=stats,
            collate=collate,
            **extra_kwargs,
        )

        if "heatmap_facets" in kwargs:
            heatmap_facets = kwargs.pop("heatmap_facets")
            kwargs["facet"] = "on"
            for field, options in heatmap_facets.items():
                if "facet.heatmap" not in kwargs:
                    kwargs["facet.heatmap"] = list(heatmap_facets.keys())

                for key, value in options.items():
                    kwargs["f.%s.facet.heatmap.%s" % (field, key)] = value

        if "facet.field" in kwargs:
            kwargs["facet.field"] = list(kwargs["facet.field"])

        if "facet.date" in kwargs:
            kwargs["facet.date"] = list(kwargs["facet.date"])

        return kwargs

    def mount_query(self, table_name, query_string, select_fields, rows, is_count, **search_kwargs):
        solr_query = dict(search_kwargs)
        if is_count:
            select_fields = "COUNT(*) as rows_count"
            # we need to get all the hits from the query, so we can't use start
            solr_query.pop("start", None)

        solr_query["q"] = query_string
        query = "SELECT %s FROM %s WHERE solr_query='%s'" % (select_fields, table_name, json.dumps(solr_query))

        if rows:
            query += " LIMIT %d" % rows

        return query

    def search(self, query_string, **kwargs):
        if self.has_group(**kwargs) or self.has_percent_score(**kwargs) or self.has_json_facets(**kwargs):
            return self.backup_implementation.search(query_string, **kwargs)
        # In cassandra we can only query one table at a time, then only one
        # model should be present in the list of models
        model = list(kwargs["models"])[0]

        if len(query_string) == 0:
            return {
                "results": [],
                "hits": 0,
            }

        search_kwargs = self.build_search_kwargs(query_string, **kwargs)
        select_fields, rows = self.kwargs_to_dse_format(search_kwargs)

        if "fq" in search_kwargs:
            for index, item in enumerate(search_kwargs["fq"]):
                if re.match(r"{}(.*)".format(DJANGO_CT), item):
                    del search_kwargs["fq"][index]
                    break

        is_count = search_kwargs.pop("is_count", False)
        is_result = search_kwargs.pop("is_result", False)
        has_paging = search_kwargs.pop("has_paging", False)
        paging_state = search_kwargs.pop("paging_state", None)
        if is_count or is_result:
            # we can't count with facets
            search_kwargs.pop("facet", None)
        fetch_size = DEFAULT_FETCH_SIZE
        if has_paging and rows and not search_kwargs.get("start", None):
            fetch_size = rows
            rows = None
            search_kwargs["paging"] = "driver"
        try:
            query = self.mount_query(model.__table_name__, query_string, select_fields, rows, is_count, **search_kwargs)
            self.log.debug(f"CQL Query: {query}")

            select_statement = SimpleStatement(query, fetch_size=fetch_size)
            with self.connection.cursor() as cursor:
                # we need the cursor from the django cassandra engine, not the wrappers
                normal_consumer_wrapper_available = True
                try:
                    from debug_toolbar.panels.sql.tracking import NormalCursorWrapper
                except:
                    normal_consumer_wrapper_available = False

                if normal_consumer_wrapper_available and isinstance(cursor, NormalCursorWrapper):
                    cursor = cursor.cursor.cursor
                else:
                    cursor = cursor.cursor

                raw_results = cursor.execute(select_statement, paging_state=paging_state, timeout=self.timeout)
        except Exception as e:
            if not self.silently_fail:
                raise

            self.log.error("Failed to query Solr using '%s': %s", query_string, e, exc_info=True)
            raw_results = []

        if has_paging and raw_results:
            has_more_pages = raw_results.has_more_pages
            paging_state = raw_results.paging_state
            raw_results = raw_results.current_rows
        else:
            has_more_pages = None
            paging_state = None
            raw_results = [raw_result for raw_result in raw_results]

        if is_count:
            if len(raw_results) == 1 and "rows_count" in raw_results[0]:
                return {
                    "results": [],
                    "hits": raw_results[0]["rows_count"],
                }

        app_model = model._meta.label_lower
        for index, raw_result in enumerate(raw_results):
            raw_result[DJANGO_CT] = app_model
            raw_result[DJANGO_ID] = index

        final_results = self._process_results(
            raw_results,
            model=model,
            highlight=kwargs.get("highlight"),
            result_class=kwargs.get("result_class", SearchResult),
            distance_point=kwargs.get("distance_point"),
            percent_score=kwargs.get("percent_score"),
            is_faceted=search_kwargs.get("facet", None) is not None,
        )

        if has_paging:
            if raw_results:
                final_results = final_results, has_more_pages, paging_state
            else:
                final_results = final_results, False, False

        return final_results

    def kwargs_to_dse_format(self, kwargs):
        fields = kwargs.pop("fl", None)
        if fields:
            if isinstance(fields, (list, tuple)):
                if isinstance(fields, tuple):
                    fields = list(fields)
                for i, field in enumerate(fields):
                    if not field.startswith('"') and not field == "score":
                        fields[i] = '"%s"' % field
                fields = " ".join(fields)

            fields = fields.replace(" score", "")
            fields = fields.replace("score ", "")
            fields = fields.replace(' "score"', "")
            fields = fields.replace('"score" ', "")
            fields = fields.replace(" ", ", ")

        rows = kwargs.pop("rows", None)
        kwargs.pop("df")

        if kwargs.pop("facet", None) == "on":
            facet = {}
            keys_to_remove = []
            for key, value in kwargs.items():
                remove = False
                if key.startswith("facet."):
                    key_split = key.split(".")
                    if len(key_split) == 2:
                        facet[key_split[1]] = value
                        remove = True
                    elif len(key_split) == 3:
                        if key_split[2] == "other":
                            key_name = key_split[1]
                            if not isinstance(value, list):
                                value = [value]

                            if key_name not in facet or not facet[key_name]:
                                facet[key_name] = []

                            for val in value:
                                if val != "none":
                                    facet[key_name].append(val)
                            remove = True
                elif re.match(r"^f(?:\.[a-zA-Z0-9_-]*)+$", key):
                    key_split = key.split(".")
                    new_key = ".".join(key_split[0:2]) + "." + ".".join(key_split[3:])
                    facet[new_key] = value
                    remove = True

                if remove:
                    keys_to_remove.append(key)

            for key_to_remove in keys_to_remove:
                del kwargs[key_to_remove]
            kwargs["facet"] = facet

        for key in list(kwargs):
            for to_remove in ["spellcheck", "percent_score", "cursorMark"]:
                if key.startswith(to_remove):
                    del kwargs[key]

        return fields, rows

    def has_group(self, **kwargs):
        return kwargs.get("group", "false") == "true"

    def has_json_facets(self, **kwargs):
        return kwargs.get("json_facets", None)

    def has_percent_score(self, **kwargs):
        return kwargs.get("percent_score", False)


class DSEQuery(CassandraSolrSearchQuery):
    def __init__(self, using=DEFAULT_ALIAS):
        super(DSEQuery, self).__init__(using=using)
        self.heatmap_facets = {}

    def get_count(self):
        """
        Returns the number of results the backend found for the query.

        If the query has not been run, this will execute the query and store
        the results.
        """
        if not self._hit_count:
            if self._more_like_this:
                # Special case for MLT.
                self.run_mlt()
            elif self._raw_query:
                # Special case for raw queries.
                self.run_raw()
            else:
                self.run(is_count=True)

        return self._hit_count

    def get_results(self, **kwargs):
        kwargs["is_result"] = True
        return super().get_results(**kwargs)

    def add_heatmap_facet(self, field, **options):
        self.heatmap_facets[field] = options

    def _clone(self, klass=None, using=None):
        clone = super()._clone(klass=klass, using=using)
        clone.heatmap_facets = self.heatmap_facets.copy()
        return clone

    def build_params(self, spelling_query=None, **kwargs):
        kwargs = super().build_params(spelling_query, **kwargs)

        if self.heatmap_facets:
            kwargs["heatmap_facets"] = self.heatmap_facets

        return kwargs


class DSEEngine(BaseEngine):
    backend = DSEBackend
    query = DSEQuery
    paginator = DSEPaginator
    solr_paginator = SolrSearchPaginator
