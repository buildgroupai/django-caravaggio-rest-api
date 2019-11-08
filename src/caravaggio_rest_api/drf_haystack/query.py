# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import operator
from itertools import chain

from django.utils import six

from rest_framework.fields import UUIDField

from drf_haystack.query import FilterQueryBuilder
from drf_haystack import constants


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
                field_repr = results_serializer.get_fields()[base_param]
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
