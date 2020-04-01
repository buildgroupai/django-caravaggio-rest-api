# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging

from rest_framework import serializers

LOGGER = logging.getLogger(__name__)


class DynamicFieldsSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", set())
        super().__init__(*args, **kwargs)

        if fields and "__all__" not in fields:
            all_fields = set(self.fields.keys())
            for not_requested in all_fields - set(fields):
                self.fields.pop(not_requested)
