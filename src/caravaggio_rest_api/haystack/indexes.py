# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import json

from django.utils import six

try:
    from dse.util import Point, LineString
except ImportError:
    from cassandra.util import Point, LineString

from haystack import indexes
from haystack.fields import LocationField, SearchField, FacetCharField


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


class CaravaggioPointField(LocationField):
    def convert(self, value):
        if isinstance(value, Point):
            return value

        return super().convert(value)


class CaravaggioLineStringField(LocationField):
    def convert(self, value):
        if isinstance(value, LineString):
            return value

        return super().convert(value)


class TextField(SearchField):
    field_type = 'string'

    def __init__(self, **kwargs):
        if kwargs.get('facet_class') is None:
            kwargs['facet_class'] = FacetCharField

        super(TextField, self).__init__(**kwargs)

    def prepare(self, obj):
        return self.convert(super(TextField, self).prepare(obj))

    def convert(self, value):
        if value is None:
            return None

        return six.text_type(value)