# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from haystack.backends import SearchNode
from haystack.constants import VALID_FILTERS, FILTER_SEPARATOR


class SolrSearchNode(SearchNode):
    def split_expression(self, expression):
        """Parses an expression and determines the field and filter type."""
        parts = expression.split(FILTER_SEPARATOR)
        field = parts[0]
        if len(parts) == 1 or parts[-1] not in set(list(VALID_FILTERS) + ["regex", "iregex"]):
            filter_type = "content"
        else:
            filter_type = parts.pop()

        return (field, filter_type)
