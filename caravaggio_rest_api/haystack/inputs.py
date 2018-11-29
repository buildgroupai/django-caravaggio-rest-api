# -*- coding: utf-8 -*
# Copyright (c) 2018 PreSeries Tech, SL
from haystack.inputs import BaseInput


class RegExp(BaseInput):
    """
    An input type for sanitizing user/untrusted regex input.
    """
    input_type_name = 'regex'

    def prepare(self, query_obj):
        query_string = super(RegExp, self).prepare(query_obj)
        return query_string
