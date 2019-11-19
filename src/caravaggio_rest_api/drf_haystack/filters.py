# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
import operator

from haystack.utils.loading import UnifiedIndex

from drf_haystack.filters import \
    HaystackOrderingFilter as DRFHaystackOrderingFilter

from drf_haystack.filters import \
    HaystackFilter as DRFHaystackFilter

from drf_haystack.filters import \
    HaystackFacetFilter as DRFHaystackFacetFilter

from drf_haystack.viewsets import HaystackViewSet

from rest_framework.filters import ORDER_PATTERN

from caravaggio_rest_api.drf_haystack.query import \
    CaravaggioFilterQueryBuilder, CaravaggioFacetQueryBuilder
from caravaggio_rest_api.haystack.query import CaravaggioSearchQuerySet


class CaravaggioHaystackFilter(DRFHaystackFilter):
    """
    A filter backend that compiles a haystack compatible filtering query.
    """

    query_builder_class = CaravaggioFilterQueryBuilder
    default_operator = operator.and_


class CaravaggioHaystackFacetFilter(DRFHaystackFacetFilter):

    query_builder_class = CaravaggioFacetQueryBuilder

    def apply_filters(self, queryset,
                      applicable_filters=None, applicable_exclusions=None):
        """
        Apply faceting to the queryset
        """
        queryset = super().apply_filters(
            queryset,
            applicable_filters=applicable_filters,
            applicable_exclusions=applicable_exclusions)

        if isinstance(queryset, CaravaggioSearchQuerySet):
            for field, options in applicable_filters["range_facets"].items():
                queryset = queryset.range_facet(field, **options)

        return queryset


class HaystackOrderingFilter(DRFHaystackOrderingFilter):

    _index = None

    def get_indexes(self):
        if self._index is None:
            self._index = UnifiedIndex().get_indexes()
        return self._index

    def get_valid_fields(self, queryset, view, context={}):
        valid_fields = super().get_valid_fields(queryset, view, context)
        if isinstance(view, HaystackViewSet):
            model_clazz = view.get_serializer_class()(
                context=context).Meta.model
            try:
                processed_valid_fields = []
                index = self.get_indexes()[model_clazz]
                for field in valid_fields:
                    index_field = getattr(index, field[0], None)
                    if index_field and getattr(index_field, "faceted", False):
                        processed_valid_fields.append(
                            (field[0], "{}_exact".format(field[0])))
                    else:
                        processed_valid_fields.append(field)
                valid_fields = processed_valid_fields
            except KeyError:
                # There is no model with index
                pass

        return valid_fields

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = {item[0]: item[1] for item in self.get_valid_fields(
            queryset, view, {'request': request})}

        return [term.replace(term.lstrip('-'),
                             valid_fields[term.lstrip('-')])
                for term in fields
                if term.lstrip('-') in valid_fields.keys() and
                ORDER_PATTERN.match(term)]
