# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
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
