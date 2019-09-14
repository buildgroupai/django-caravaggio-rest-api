# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging

from caravaggio_rest_api.drf_haystack.viewsets import CustomModelViewSet

LOGGER = logging.getLogger(__name__)


class DynamicFieldsViewSet(CustomModelViewSet):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_query_fields(self):
        custom_query_fields = set()
        raw_fields = self.request.query_params.getlist('fields')

        for item in raw_fields:
            custom_query_fields.update(item.split(','))

        return custom_query_fields

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(
            *args, fields=self.get_query_fields(), **kwargs)
