# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

from haystack.utils.loading import UnifiedIndex

from drf_haystack.filters import \
    HaystackOrderingFilter as DRFHaystackOrderingFilter

from drf_haystack.viewsets import HaystackViewSet

from rest_framework.filters import ORDER_PATTERN


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
