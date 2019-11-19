# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import warnings
import operator
from itertools import chain
from dateutil import parser

from django.utils import six

from rest_framework.fields import UUIDField

from drf_haystack.query import FilterQueryBuilder, FacetQueryBuilder
from drf_haystack.utils import merge_dict
from drf_haystack import constants


class CaravaggioFacetQueryBuilder(FacetQueryBuilder):

    def build_query(self, **filters):
        """
        Creates a dict of dictionaries suitable for passing to the
        SearchQuerySet `facet`,
        `date_facet` or `query_facet` method. All key word arguments
        should be wrapped in a list.

        :param view: API View
        :param dict[str, list[str]] filters: is an expanded QueryDict or
         a mapping
        of keys to a list of parameters.
        """
        field_facets = {}
        date_facets = {}
        query_facets = {}
        range_facets = {}
        facet_serializer_cls = self.view.get_facet_serializer_class()

        if self.view.lookup_sep == ":":
            raise AttributeError(
                "The %(cls)s.lookup_sep attribute conflicts with the "
                "HaystackFacetFilter query parameter parser. Please choose "
                "another `lookup_sep` attribute for %(cls)s." %
                {"cls": self.view.__class__.__name__})

        fields = facet_serializer_cls.Meta.fields
        exclude = facet_serializer_cls.Meta.exclude
        field_options = facet_serializer_cls.Meta.field_options

        for field, options in filters.items():

            if field not in fields or field in exclude:
                continue

            field_options = merge_dict(
                field_options, {
                    field: self.parse_field_options(
                        self.view.lookup_sep, *options)})

        valid_gap = ("year", "month", "day", "hour", "minute", "second")
        for field, options in field_options.items():
            if any([k in options for k in (
                    "start_date", "end_date", "gap_by", "gap_amount")]):

                if not all(("start_date", "end_date", "gap_by" in options)):
                    raise ValueError(
                        "Date faceting requires at least 'start_date', "
                        "'end_date' and 'gap_by' to be set.")

                if not options["gap_by"] in valid_gap:
                    raise ValueError(
                        "The 'gap_by' parameter must be one of %s." %
                        ", ".join(valid_gap))

                options.setdefault("gap_amount", 1)
                date_facets[field] = field_options[field]
            elif any([k in options for k in (
                    "start", "end", "gap")]):

                if not all(("start", "end", "gap" in options)):
                    raise ValueError(
                        "Range faceting requires at least 'start', 'end' "
                        "and 'gap' to be set.")

                range_facets[field] = field_options[field]
            else:
                field_facets[field] = field_options[field]

        return {
            "date_facets": date_facets,
            "field_facets": field_facets,
            "query_facets": query_facets,
            "range_facets": range_facets
        }

    def parse_field_options(self, *options):
        """
        Parse the field options query string and return it as a dictionary.
        """
        defaults = {}
        for option in options:
            if isinstance(option, six.text_type):
                tokens = [token.strip()
                          for token in option.split(self.view.lookup_sep)]

                for token in tokens:
                    if not len(token.split(":")) == 2:
                        warnings.warn("The %s token is not properly formatted."
                                      " Tokens need to be formatted as "
                                      "'token:value' pairs." % token)
                        continue

                    param, value = token.split(":", 1)

                    if any([k == param for k in (
                            "start_date", "end_date", "gap_amount")]):

                        if param in ("start_date", "end_date"):
                            value = parser.parse(value)

                        if param == "gap_amount":
                            value = int(value)

                    if any([k == param for k in (
                            "start", "end", "gap", "mincount",
                            "hardend")]):

                        if param in ("start", "end"):
                            value = int(value)

                        if param == "gap":
                            value = int(value)

                        if param == "mincount":
                            value = int(value)

                        if param == "hardend":
                            value = bool(value)

                    defaults[param] = value

        return defaults


class CaravaggioFilterQueryBuilder(FilterQueryBuilder):
    """
    Query builder class suitable for doing basic filtering.
    """

    def build_query(self, **filters):
        """
        Creates a single SQ filter from querystring parameters that correspond
        to the SearchIndex fields that have been "registered" in `view.fields`.

        Default behavior is to `OR` terms for the same parameters, and `AND`
        between parameters. Any querystring parameters that are not registered
        in `view.fields` will be ignored.

        :param dict[str, list[str]] filters: is an expanded QueryDict or a
         mapping of keys to a list of parameters.
        """

        applicable_filters = []
        applicable_exclusions = []

        for param, value in filters.items():
            excluding_term = False
            param_parts = param.split("__")
            # only test against field without lookup
            base_param = param_parts[0]
            negation_keyword = constants.DRF_HAYSTACK_NEGATION_KEYWORD
            if len(param_parts) > 1 and param_parts[1] == negation_keyword:
                excluding_term = True
                # haystack wouldn't understand our negation
                param = param.replace("__%s" % negation_keyword, "")

            if self.view.serializer_class:
                if hasattr(self.view.serializer_class.Meta, 'field_aliases'):
                    old_base = base_param
                    base_param = self.view.serializer_class.Meta.\
                        field_aliases.get(base_param, base_param)
                    # need to replace the alias
                    param = param.replace(old_base, base_param)

                fields = getattr(
                    self.view.serializer_class.Meta, 'fields', [])
                exclude = getattr(
                    self.view.serializer_class.Meta, 'exclude', [])
                search_fields = getattr(
                    self.view.serializer_class.Meta, 'search_fields', [])

                # Skip if the parameter is not listed in the
                # serializer's `fields` or if it's in the `exclude` list.
                if ((fields or search_fields) and base_param not in
                        chain(fields, search_fields)) or (
                        base_param in exclude) or not value:
                    continue

            # START CARAVAGGIO (UUID fields)
            # There are fields that can be expressed in different format,
            # for instance the UUID, you can inform them using '-' or not.
            if hasattr(self.view, "results_serializer_class") and (
                    self.view.results_serializer_class):
                results_serializer = self.view.results_serializer_class()
                ser_fields = results_serializer.get_fields()
                if base_param in ser_fields:
                    field_repr = ser_fields[base_param]
                    if isinstance(field_repr, UUIDField):
                        value[0] = field_repr.to_representation(
                            field_repr.to_internal_value(value[0]))
            # END CARAVAGGIO

            field_queries = []
            if len(param_parts) > 1 and param_parts[-1] in ('in', 'range'):
                # `in` and `range` filters expects a list of values
                field_queries.append(self.view.query_object(
                    (param, list(self.tokenize(value, self.view.lookup_sep)))))
            else:
                for token in self.tokenize(value, self.view.lookup_sep):
                    field_queries.append(
                        self.view.query_object((param, token)))

            field_queries = [fq for fq in field_queries if fq]
            if len(field_queries) > 0:
                term = six.moves.reduce(operator.or_, field_queries)
                if excluding_term:
                    applicable_exclusions.append(term)
                else:
                    applicable_filters.append(term)

        applicable_filters = six.moves.reduce(
            self.default_operator,
            filter(
                lambda x: x, applicable_filters)) if applicable_filters else []

        applicable_exclusions = six.moves.reduce(
            self.default_operator,
            filter(
                lambda x: x, applicable_exclusions)) \
            if applicable_exclusions else []

        return applicable_filters, applicable_exclusions
