# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import logging
import re
import json
import datetime
import ast

from six import string_types
from django.utils import six

from django.core.exceptions import ImproperlyConfigured

from haystack.inputs import Clean, Exact, PythonData, Raw
from haystack.backends import BaseEngine, EmptyResults
from haystack.backends.solr_backend import SolrSearchQuery, SolrSearchBackend
from haystack.constants import DJANGO_CT, DJANGO_ID, DEFAULT_ALIAS
from haystack.exceptions import MissingDependency, FacetingError, \
    MoreLikeThisError
from haystack.models import SearchResult

from caravaggio_rest_api.haystack.backends import SolrSearchNode
from caravaggio_rest_api.haystack.backends.utils import is_valid_uuid
from caravaggio_rest_api.haystack.inputs import RegExp

try:
    from pysolr import Solr, SolrError, force_unicode, IS_PY3, DATETIME_REGEX
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

        self.date_facets = {}
        self.range_facets = {}

    def update(self, index, iterable, commit=True):
        raise NotImplemented("Update is not allowed in DSE")

    def remove(self, obj_or_string, commit=True):
        raise NotImplemented("Remove is not allowed in DSE")

    def clear(self, models=None, commit=True):
        raise NotImplemented("Clear is not allowed in DSE")

    def _process_results(self, raw_results, model=None, highlight=False,
                         result_class=None, distance_point=None):

        results = super()._process_results(
            raw_results, highlight, result_class, distance_point)

        if hasattr(raw_results, 'qtime'):
            results["qtime"] = raw_results.qtime

        if hasattr(raw_results, 'raw_response') and \
                "params" in raw_results.raw_response['responseHeader']:
            results["params"] = \
                raw_results.raw_response['responseHeader']['params']

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

        results["facets"]["ranges"] = {}

        if hasattr(raw_results, 'facets'):
            ranges = raw_results.facets.get('facet_ranges', {})
            if len(ranges):
                for field_name, range_data in ranges.items():
                    if field_name in self.date_facets:
                        results["facets"]["dates"][field_name] = \
                            group_facet_counts(range_data["counts"], 2)
                    elif field_name in self.range_facets:
                        results["facets"]["ranges"][field_name] = \
                            group_facet_counts(range_data["counts"], 2)

        if hasattr(raw_results, 'nextCursorMark'):
            results["nextCursorMark"] = raw_results.nextCursorMark

        if hasattr(raw_results, 'grouped'):
            groups = {}
            hits = raw_results.hits

            app_model = model._meta.label_lower

            index = 0

            for group_field in raw_results.grouped.keys():
                # Convert to a two-tuple, as Solr's json format returns a
                # list of pairs.
                for group in raw_results.grouped[group_field]['groups']:
                    group_data = groups.setdefault(group['groupValue'], [])
                    for doc in group['doclist']['docs']:
                        doc[DJANGO_CT] = app_model
                        doc[DJANGO_ID] = index

                        app_label, model_name = doc[DJANGO_CT].split('.')

                        # TODO: BGDS
                        additional_fields = {}

                        for key, value in doc.items():
                            string_key = str(key)

                            additional_fields[string_key] = \
                                self._to_python(value)

                        result = result_class(
                            app_label,
                            model_name,
                            doc[DJANGO_ID],
                            **additional_fields)

                        group_data.append(result)
                        hits += 1

            results["hits"] = hits
            results["groups"] = groups

        return results

    # TODO: BGDS.
    # Added because the ObjectId that only contains numbers were converted
    # into float -> Inf
    def _to_python(self, value):
        """
        Converts values from Solr to native Python values.
        """
        if value is None:
            return value

        if isinstance(value, (int, float, complex)):
            return value

        is_list = isinstance(value, (list, tuple))

        values_processed = []
        values_to_process = []

        if isinstance(value, (list, tuple)):
            # Clone the value
            values_to_process = value[:]
        else:
            values_to_process.append(value)

        for value in values_to_process:

            if value == 'true':
                values_processed.append(True)
                continue
            elif value == 'false':
                values_processed.append(False)
                continue

            is_string = False

            if IS_PY3:
                if isinstance(value, bytes):
                    value = force_unicode(value)

                if isinstance(value, str):
                    is_string = True
            else:
                if isinstance(value, str):
                    value = force_unicode(value)

                if isinstance(value, string_types):
                    is_string = True

            if is_string:
                possible_datetime = DATETIME_REGEX.search(value)

                if possible_datetime:
                    date_values = possible_datetime.groupdict()

                    for dk, dv in date_values.items():
                        date_values[dk] = int(dv)

                    values_processed.append(datetime.datetime(
                        date_values['year'], date_values['month'],
                        date_values['day'], date_values['hour'],
                        date_values['minute'], date_values['second']))
                    continue
                # elif ObjectId.is_valid(value):
                #    values_processed.append(value)
                #    continue
                elif is_valid_uuid(value, version=4):
                    values_processed.append(value)
                    continue
                elif is_valid_uuid(value, version=3):
                    values_processed.append(value)
                    continue
                elif is_valid_uuid(value, version=2):
                    values_processed.append(value)
                    continue
                elif is_valid_uuid(value, version=1):
                    values_processed.append(value)
                    continue
            try:
                # This is slightly gross but it's hard to tell otherwise what
                # the string's original type might have been.
                values_processed.append(ast.literal_eval(value))
            except (ValueError, SyntaxError):
                # If it fails, continue on.
                pass

            values_processed.append(value)

        return values_processed if is_list else values_processed[0]

    def build_search_kwargs(self, query_string, sort_by=None,
                            start_offset=0, end_offset=None,
                            fields='', highlight=False, facets=None,
                            date_facets=None, query_facets=None,
                            range_facets=None,
                            narrow_queries=None, spelling_query=None,
                            within=None, dwithin=None, distance_point=None,
                            models=None, limit_to_registered_models=None,
                            result_class=None, stats=None, collate=None,
                            **extra_kwargs):

        self.date_facets = date_facets.copy() if date_facets else {}
        self.range_facets = range_facets.copy() if range_facets else {}

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
            kwargs['facet.range'] = list(date_facets.keys())
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

        if range_facets is not None:
            kwargs['facet'] = 'on'
            for field, options in range_facets.items():
                if 'facet.range' in kwargs:
                    kwargs['facet.range'] = \
                        list(set(
                            list(kwargs['facet.range']) +
                            list(range_facets.keys())))
                else:
                    kwargs['facet.range'] = range_facets.keys()
                for key, value in options.items():
                    if key in ['start', 'end', 'gap', 'hardend', 'other',
                               'include'] or 1:
                        if key == 'hardend':
                            value = 'true' if value else ''
                        kwargs['f.%s.facet.range.%s' % (field, key)] = value

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
            raw_results,
            model=model,
            highlight=kwargs.get('highlight'),
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
        self.query_filter = SolrSearchNode()
        self.json_facets = {}
        self.range_facets = {}

    def build_query_fragment(self, field, filter_type, value):
        from haystack import connections
        query_frag = ''

        if not hasattr(value, 'input_type_name'):
            # Handle when we've got a ``ValuesListQuerySet``...
            if hasattr(value, 'values_list'):
                value = list(value)

            if filter_type in ["regex", "iregex"]:
                value = RegExp(value)
            elif isinstance(value, six.string_types):
                # It's not an ``InputType``. Assume ``Clean``.
                value = Clean(value)
            else:
                value = PythonData(value)

        # Prepare the query using the InputType.
        prepared_value = value.prepare(self)

        if not isinstance(prepared_value, (set, list, tuple)):
            # Then convert whatever we get back to what pysolr wants if needed.
            prepared_value = self.backend.conn._from_python(prepared_value)

        # 'content' is a special reserved word, much like 'pk' in
        # Django's ORM layer. It indicates 'no special field'.
        if field == 'content':
            index_fieldname = ''
        else:
            index_fieldname = \
                u'%s' % connections[self._using].\
                get_unified_index().get_index_fieldname(field)

        filter_types = {
            'content': u'%s',
            'contains': u'*%s*',
            'endswith': u'*%s',
            'startswith': u'%s*',
            'exact': u'%s',
            'gt': u'{%s TO *}',
            'gte': u'[%s TO *]',
            'lt': u'{* TO %s}',
            'lte': u'[* TO %s]',
            'fuzzy': u'%s~',
            'regex': u'/%s/',
            'iregex': u'/%s/',
        }

        if value.post_process is False:
            query_frag = prepared_value
        else:
            if filter_type in \
                    ['content', 'contains', 'startswith',
                     'endswith', 'fuzzy', 'regex', 'iregex']:
                if value.input_type_name == 'exact':
                    query_frag = prepared_value
                else:
                    # Iterate over terms & incorportate the converted
                    # form of each into the query.
                    terms = []

                    for possible_value in prepared_value.split(' '):
                        terms.append(
                            filter_types[filter_type] % (
                                self.backend.conn._from_python(possible_value)
                                if filter_type not in ['regex', 'iregex']
                                else possible_value))

                    if len(terms) == 1:
                        query_frag = terms[0]
                    else:
                        query_frag = u"(%s)" % " AND ".join(terms)
            elif filter_type == 'in':
                in_options = []

                if not prepared_value:
                    query_frag = u'(!*:*)'
                else:
                    for possible_value in prepared_value:
                        in_options.append(
                            u'"%s"' %
                            self.backend.conn._from_python(possible_value))

                    query_frag = u"(%s)" % " OR ".join(in_options)
            elif filter_type == 'range':
                start = self.backend.conn._from_python(prepared_value[0])
                end = self.backend.conn._from_python(prepared_value[1])
                query_frag = u'["%s" TO "%s"]' % (start, end)
            elif filter_type == 'exact':
                if value.input_type_name == 'exact':
                    query_frag = prepared_value
                else:
                    prepared_value = Exact(prepared_value).prepare(self)
                    query_frag = filter_types[filter_type] % prepared_value
            else:
                if value.input_type_name != 'exact':
                    prepared_value = Exact(prepared_value).prepare(self)

                query_frag = filter_types[filter_type] % prepared_value

        if len(query_frag) and not isinstance(value, Raw) and \
                filter_type not in ['regex', 'iregex']:
            if not query_frag.startswith('(') and not query_frag.endswith(')'):
                query_frag = "(%s)" % query_frag
        elif isinstance(value, Raw):
            return query_frag

        # Check if the field is making a reference to a Tuple/UDF object

        # Obtain the list of searchable fields available at the Index
        # class associated to the model
        searchable_fields = connections[self._using]. \
            get_unified_index().all_searchfields()

        # Get the model attribute that is connected to the current
        # index search field.
        model_attr = searchable_fields[index_fieldname].model_attr

        if model_attr and '.' in model_attr:
            return u"{{!tuple v='{field}:{value}'}}".format(
                field=model_attr, value=query_frag)
        else:
            return u"%s:%s" % (index_fieldname, query_frag)

    def build_params(self, spelling_query=None, **kwargs):
        """Generates a list of params to use when searching."""
        kwargs = super().build_params(spelling_query=spelling_query, **kwargs)

        if self.json_facets:
            kwargs['json_facets'] = self.json_facets

        if self.range_facets:
            kwargs['range_facets'] = self.range_facets

        return kwargs

    def _get_facet_fieldname(self, field):
        from haystack import connections
        return connections[
            self._using].get_unified_index().get_facet_fieldname(field)

    def add_range_facet(self, field, **options):
        self.range_facets[self._get_facet_fieldname(field)] = options

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
        clone.range_facets = self.range_facets.copy()
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
            raise MoreLikeThisError(
                "No instance was provided to determine"
                " 'More Like This' results.")

        additional_query_string = self.build_query()
        search_kwargs = {
            'start_offset': self.start_offset,
            'result_class': self.result_class,
            'models': self.models
        }

        if self.end_offset is not None:
            search_kwargs['end_offset'] = self.end_offset - self.start_offset

        results = self.backend.more_like_this(
            self._mlt_instance, additional_query_string, **search_kwargs)
        self._results = results.get('results', [])
        self._hit_count = results.get('hits', 0)


class CassandraSolrEngine(BaseEngine):
    backend = CassandraSolrSearchBackend
    query = CassandraSolrSearchQuery
