# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import json

from haystack import indexes


class BaseSearchIndex(indexes.SearchIndex):

    text = indexes.CharField(document=True, use_template=True)

    autocomplete = indexes.EdgeNgramField()

    class Meta:
        abstract = True

        text_fields = []

    @staticmethod
    def prepare_autocomplete(obj):
        # return " ".join((
        #    obj.name, obj.short_description,
        #    obj.foundation_date, obj.stock_symbol
        # ))
        pass


class CaravaggioListField(indexes.MultiValueField):

    def convert(self, value):
        value = super().convert(value)

        if not value:
            return value

        new_value = []
        for _value in value:
            new_value.append(json.loads(_value))

        return new_value
