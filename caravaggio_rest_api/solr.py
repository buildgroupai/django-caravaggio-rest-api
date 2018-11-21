# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 PreSeries Tech, SL
# All rights reserved.
import logging
import re
import json

from django.core.exceptions import ImproperlyConfigured

from haystack import connection_router, connections
from haystack.backends import BaseEngine, EmptyResults
from haystack.backends.solr_backend import SolrSearchQuery, SolrSearchBackend
from haystack.constants import DJANGO_CT, DJANGO_ID, DEFAULT_ALIAS
from haystack.exceptions import MissingDependency, FacetingError, \
    MoreLikeThisError
from haystack.models import SearchResult

try:
    from pysolr import Solr, SolrError
except ImportError:
    raise MissingDependency("The 'solr' backend requires the installation"
                            " of 'pysolr'. Please refer to the documentation.")

VALID_JSON_FACET_TYPES = ["terms", "query"]


def group_facet_counts(lst, n):
    for i in range(0, len(lst), n):
        val = lst[i:i+n]
        if len(val) == n:
            yield tuple(val)


class CassandraSolrSearchBackend(SolrSearchBackend):

    def __init__(self, connection_alias, **connection_options):
        super(SolrSearchBackend, self).\
            __init__(connection_alias, **connection_options)

        if 'URL' not in connection_options:
            raise ImproperlyConfigured(
                "You must specify a 'URL' in your"
                " settings for connection '%s'." % connection_alias)

        if 'KEYSPACE' not in connection_options:
            raise ImproperlyConfigured(
                "You must specify a 'KEYSPACE' in your"
                " settings for connection '%s'." % connection_alias)

        self.collate = connection_options.get('COLLATE_SPELLING', True)

        self.connections = {}

        self.base_url = connection_options['URL']

        self.keyspace = connection_options['KEYSPACE']

        self.conn_kwargs = connection_options.get('KWARGS', {})

        self.conn = Solr(connection_options['URL'], timeout=self.timeout,
                         **connection_options.get('KWARGS', {}))

        self.log = logging.getLogger('haystack')

    def update(self, index, iterable, commit=True):
        raise NotImplemented("Update is not allowed in DSE")

    def remove(self, obj_or_string, commit=True):
        raise NotImplemented("Remove is not allowed in DSE")

    def clear(self, models=None, commit=True):
        raise NotImplemented("Clear is not allowed in DSE")

    def _process_results(self, raw_results, highlight=False,
                         result_class=None, distance_point=None):

        results = super()._process_results(
            raw_results, highlight, result_class, distance_point)

        if hasattr(raw_results, 'raw_response') and \
                'facets' in raw_results.raw_response:
            json_facets = results["facets"].setdefault("json_facets", {})

            raw_facets = raw_results.raw_response.get("facets", {})
            if len(raw_facets):
                for facet_name, buckets in raw_facets.items():
                    if facet_name == "count":
                        continue

                    fields_name = list(buckets["buckets"][0].keys())
                    fields_name.remove("val")

                    for field_name in fields_name:
                        json_facets["{0}_{1}".
                            format(facet_name, field_name)] = \
                            [(bucket["val"], bucket[field_name])
                             for bucket in buckets["buckets"]]

        if hasattr(raw_results, 'facets'):
            ranges = raw_results.facets.get('facet_ranges', {})
            if len(ranges):
                for field_name, range_data in ranges.items():
                    results["facets"]["dates"][field_name] = \
                        group_facet_counts(range_data["counts"], 2)

        if hasattr(raw_results, 'nextCursorMark'):
            results["nextCursorMark"] = raw_results.nextCursorMark

        return results

    def build_search_kwargs(self, query_string, sort_by=None,
                            start_offset=0, end_offset=None,
                            fields='', highlight=False, facets=None,
                            date_facets=None, query_facets=None,
                            narrow_queries=None, spelling_query=None,
                            within=None, dwithin=None, distance_point=None,
                            models=None, limit_to_registered_models=None,
                            result_class=None, stats=None, collate=None,
                            **extra_kwargs):

        kwargs = super().build_search_kwargs(
            query_string, sort_by=sort_by, start_offset=start_offset,
            end_offset=end_offset, fields=fields, highlight=highlight,
            facets=facets, date_facets=date_facets, query_facets=query_facets,
            narrow_queries=narrow_queries, spelling_query=spelling_query,
            within=within, dwithin=dwithin, distance_point=distance_point,
            models=models,
            limit_to_registered_models=limit_to_registered_models,
            result_class=result_class, stats=stats, collate=collate,
            **extra_kwargs)

        json_facets = extra_kwargs.get("json_facets", None)
        if json_facets:
            kwargs['facet'] = 'on'
            kwargs['json.facet'] = json.dumps(json_facets)

        # Must be treated as Ranges instead of dates
        if date_facets is not None:
            kwargs['facet'] = 'on'
            kwargs['facet.range'] = date_facets.keys()
            kwargs['facet.range.other'] = 'none'

            for key, value in date_facets.items():
                kwargs["f.%s.facet.range.start" % key] = \
                    self.conn._from_python(value.get('start_date'))
                kwargs["f.%s.facet.range.end" % key] = \
                    self.conn._from_python(value.get('end_date'))
                gap_by_string = value.get('gap_by').upper()
                gap_string = "%d%s" % (value.get('gap_amount'), gap_by_string)

                if value.get('gap_amount') != 1:
                    gap_string += "S"

                kwargs["f.%s.facet.range.gap" % key] = \
                    '+%s/%s' % (gap_string, gap_by_string)

        return kwargs

    def search(self, query_string, **kwargs):
        # In cassandra we can only query one table at a time, then only one
        # model should be present in the list of models
        model = list(kwargs["models"])[0]

        self.conn = self.prepare_conn(model)

        if len(query_string) == 0:
            return {
                'results': [],
                'hits': 0,
            }

        search_kwargs = self.build_search_kwargs(query_string, **kwargs)

        if "fq" in search_kwargs:
            for index, item in enumerate(search_kwargs["fq"]):
                if re.match(r"{}(.*)".format(DJANGO_CT), item):
                    del search_kwargs["fq"][index]
                    break

        try:
            raw_results = self.conn.search(query_string, **search_kwargs)
        except (IOError, SolrError) as e:
            if not self.silently_fail:
                raise

            self.log.error("Failed to query Solr using '%s': %s",
                           query_string, e, exc_info=True)
            raw_results = EmptyResults()

        app_model = model._meta.label_lower
        for index, raw_result in enumerate(raw_results.docs):
            raw_result[DJANGO_CT] = app_model
            raw_result[DJANGO_ID] = index

        return self._process_results(
            raw_results, highlight=kwargs.get('highlight'),
            result_class=kwargs.get('result_class', SearchResult),
            distance_point=kwargs.get('distance_point'))

    def prepare_conn(self, model):
        core_name = "{0}.{1}".format(self.keyspace,
                                     model._raw_column_family_name())

        conn = self.connections.get(core_name, None)
        if conn is None:
            url = "{0}/{1}".format(self.base_url, core_name)
            conn = Solr(url, timeout=self.timeout, **self.conn_kwargs)
            self.connections[core_name] = conn
        return conn


class CassandraSolrSearchQuery(SolrSearchQuery):


    def __init__(self, using=DEFAULT_ALIAS):
        super(CassandraSolrSearchQuery, self).\
            __init__(using=using)

        self.json_facets = {}

    def build_params(self, spelling_query=None, **kwargs):
        """Generates a list of params to use when searching."""
        kwargs = super().build_params(spelling_query=spelling_query, **kwargs)

        if self.json_facets:
            kwargs['json_facets'] = self.json_facets

        return kwargs

    def add_json_terms_facet(self, facet_name, field, facets, **kwargs):
        """
        Adds a json facet of type terms.

        :param facet_name: the name of the facet. It will be used to generate
            the final field name for the buckets, joining it each facet
            name (facets). It doesn't need to be any model field.
        :param facets: each of the facets to be calculated. A field name and
            the aggregation function to be applied to any of the fields of
            the model. Ex. {"avg_age": "avg(age)", "min_age": "min(age)"}
            You can find here the avaialble functions:
            http://yonik.com/solr-facet-functions/
        :param kwargs: more parameters to be added to the facet definition.
            These parameters could be any of the available here
            http://yonik.com/json-facet-api/. Ex. offset/limit for pagination
            mincount, sort, missing, numBuckets, allbuckets,
        """
        from haystack import connections

        details = {
            'type': "terms",
            'facet': facets,
        }

        if not field:
            raise FacetingError(
                "The JSON Facet of type ('terms') needs "
                "a ('field') parameter in kwargs pointing to a valid"
                " model field name")
        else:
            details["field"] = connections[self._using].\
                get_unified_index().get_facet_fieldname(field)

        details.update(kwargs)

        self.json_facets[facet_name] = details

    def add_json_query_facet(self, facet_name, q, facets, **kwargs):
        """
        Adds a json facet of type query.

        :param facet_name: the name of the facet. It will be used to generate
            the final field name for the buckets, joining it each facet
            name (facets). It doesn't need to be any model field.
        :param facets: each of the facets to be calculated. A field name and
            the aggregation function to be applied to any of the fields of
            the model. Ex. {"avg_age": "avg(age)", "min_age": "min(age)"}
            You can find here the avaialble functions:
            http://yonik.com/solr-facet-functions/
        :param kwargs: more parameters to be added to the facet definition.
            These parameters could be any of the available here
            http://yonik.com/json-facet-api/. Ex. offset/limit for pagination
            mincount, sort, missing, numBuckets, allbuckets,
        """
        from haystack import connections

        details = {
            'type': "query",
            'facet': facets,
        }

        if not q:
            raise FacetingError(
                "The JSON Facet of type ('query') needs "
                "a ('q') parameter in kwargs with a valid"
                " solr query")
        else:
            details["q"] = q

        details.update(kwargs)

        self.json_facets[facet_name] = details

    def _clone(self, klass=None, using=None):
        clone = super()._clone(klass=klass, using=using)
        clone.json_facets = self.json_facets.copy()
        return clone

    def run(self, spelling_query=None, **kwargs):
        """Builds and executes the query. Returns a list of search results."""
        final_query = self.build_query()
        search_kwargs = self.build_params(spelling_query, **kwargs)

        if kwargs:
            search_kwargs.update(kwargs)

        results = self.backend.search(final_query, **search_kwargs)

        self._results = results.get('results', [])
        self._hit_count = results.get('hits', 0)
        self._facet_counts = self.post_process_facets(results)
        self._stats = results.get('stats', {})
        self._spelling_suggestion = results.get('spelling_suggestion', None)

    def run_mlt(self, **kwargs):
        """Builds and executes the query. Returns a list of search results."""
        if self._more_like_this is False or self._mlt_instance is None:
            raise MoreLikeThisError("No instance was provided to determine 'More Like This' results.")

        additional_query_string = self.build_query()
        search_kwargs = {
            'start_offset': self.start_offset,
            'result_class': self.result_class,
            'models': self.models
        }

        if self.end_offset is not None:
            search_kwargs['end_offset'] = self.end_offset - self.start_offset

        results = self.backend.more_like_this(self._mlt_instance, additional_query_string, **search_kwargs)
        self._results = results.get('results', [])
        self._hit_count = results.get('hits', 0)


class CassandraSolrEngine(BaseEngine):
    backend = CassandraSolrSearchBackend
    query = CassandraSolrSearchQuery


class CaravaggioSearchPaginator(object):

    CURSORMARK_FIELD = 'cursorMark'
    NEXT_CURSORMARK_FIELD = 'nextCursorMark'

    def __init__(self, query_string, models=None, limit=None, using=None,
                 max_limit=200, **kwargs):

        self.using = using
        self.query_string = query_string
        self.limit = limit
        self.cursorMark = "*"
        self.max_limit = max_limit
        self.search_kwargs = kwargs.copy()
        if models:
            self.search_kwargs["models"] = models
        self.results = None
        self.loaded_docs = 0
        self.select_fields = None

        self._determine_backend()

    def reset(self):
        self.cursorMark = "*"
        self.results = None
        self.loaded_docs = 0

    def models(self, *models):
        if not models:
            if "models" in self.search_kwargs:
                del self.search_kwargs["models"]
        else:
            self.search_kwargs["models"] = models

        self._determine_backend()
        return self

    def select(self, *fields):
        self.select_fields = fields
        if not self.select_fields:
            if "fl" in self.search_kwargs:
                del self.search_kwargs["fl"]
        else:
            if "score" not in fields:
                fields = list(fields)
                fields.append("score")
            self.search_kwargs["fl"] = fields
        return self

    def _determine_backend(self):
        # A backend has been manually selected. Use it instead.
        if self.using is not None:
            self.backend = connections[self.using].get_backend()
            return

        # No backend, so rely on the routers to figure out what's right.
        hints = {'models': self.models}

        backend_alias = connection_router.for_read(**hints)

        self.backend = connections[backend_alias].get_backend()

    def get_hits(self):
        return self.results["hits"] if self.results is not None else None

    def get_results(self):
        return self.results["results"] if self.results is not None else None

    def get_raw_results(self):
        return self.results

    def get_loaded_docs(self):
        return self.loaded_docs

    def has_next(self):

        # We cannot use CursorMarkets with Grouping. We will look if the
        # number of results is less than the informed limit
        is_group = 'group' in self.search_kwargs and \
                   'true' == self.search_kwargs[str('group')]

        if is_group:
            valid_limit = self.limit \
                if self.limit is not None and self.limit < self.max_limit \
                else self.max_limit
            return self.results is None or \
                (0 < len(self.results['groups']) <= valid_limit)
        else:
            return self.results is None or self.cursorMark != \
                   self.results[
                       CaravaggioSearchPaginator.NEXT_CURSORMARK_FIELD]

    def next(self):

        if self.has_next():

            # We cannot use CursorMarkets with Grouping. We will look if the
            # number of results is less than the informed limit
            is_group = 'group' in self.search_kwargs and \
                       'true' == self.search_kwargs[str('group')]

            if is_group:
                self.search_kwargs[str('start_offset')] = self.loaded_docs

                self.search_kwargs['end_offset'] = self.loaded_docs + (
                    self.limit if self.limit is not None and
                    self.limit < self.max_limit
                    else self.max_limit)
            else:

                # Save the next cursor mark as the actual cursor mark to send
                # to the server
                if self.results:
                    self.cursorMark = self.results[
                        CaravaggioSearchPaginator.NEXT_CURSORMARK_FIELD]

                # Signaling the cursor mark
                if 'start_offset' in self.search_kwargs:
                    del self.search_kwargs[str('start_offset')]

                self.search_kwargs['end_offset'] = self.limit \
                    if self.limit is not None and \
                    self.limit < self.max_limit else self.max_limit

                self.search_kwargs[
                    CaravaggioSearchPaginator.CURSORMARK_FIELD] = \
                    self.cursorMark

            # Do the search
            self.results = self.backend.search(
                query_string=self.query_string, **self.search_kwargs)

            if is_group:
                self.loaded_docs += len(self.results['groups'])
            else:
                self.loaded_docs += len(self.results['results'])

            return self.results
        else:
            return EmptyResults()
