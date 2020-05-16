# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from caravaggio_rest_api.caravaggio_paginator import CaravaggioSearchPaginator
from haystack.backends import EmptyResults


class DSEPaginator(CaravaggioSearchPaginator):
    def __init__(self, **kwargs):
        self.query_string = kwargs.pop("query_string", None)
        assert self.query_string is not None, "query_string is a required field"

        self.backend = kwargs.pop("backend", None)
        assert self.backend is not None, "backend is a required field"

        self.has_more_pages = False
        self.paging_state = None

        self.using = kwargs.pop("using", None)
        self.limit = kwargs.pop("limit", None)
        self.max_limit = kwargs.pop("max_limit", None)

        self.search_kwargs = kwargs.copy()

        self.results = None
        self.loaded_docs = 0
        self.select_fields = None

    def reset(self):
        self.has_more_pages = False
        self.paging_state = False
        self.results = None
        self.loaded_docs = 0

    def has_next(self):
        # We cannot use CursorMarkets with Grouping. We will look if the
        # number of results is less than the informed limit
        return self.results is None or self.has_more_pages

    def next(self):
        if self.has_next():
            # Signaling the cursor mark
            if "start_offset" in self.search_kwargs:
                del self.search_kwargs[str("start_offset")]

            self.search_kwargs["end_offset"] = (
                self.limit if self.limit is not None and self.limit < self.max_limit else self.max_limit
            )

            # Do the search
            self.results, self.has_more_pages, self.paging_state = self.backend.search(
                query_string=self.query_string, has_paging=True, paging_state=self.paging_state, **self.search_kwargs
            )

            self.loaded_docs += len(self.results["results"])

            return self.results
        else:
            return EmptyResults()
