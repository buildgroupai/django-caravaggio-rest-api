# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
from uuid import UUID

from caravaggio_rest_api.caravaggio_paginator import CaravaggioSearchPaginator
from haystack.backends import EmptyResults


class SolrSearchPaginator(CaravaggioSearchPaginator):

    CURSORMARK_FIELD = "cursorMark"
    NEXT_CURSORMARK_FIELD = "nextCursorMark"

    def __init__(self, **kwargs):
        self.cursorMark = "*"
        self.query_string = kwargs.pop("query_string", None)
        assert self.query_string is not None, "query_string is a required field"

        self.backend = kwargs.pop("backend", None)
        assert self.backend is not None, "backend is a required field"

        self.using = kwargs.pop("using", None)
        self.limit = kwargs.pop("limit", None)
        self.max_limit = kwargs.pop("max_limit", None)
        self.percent_score = kwargs.pop("percent_score", None)
        self.models = kwargs.pop("models", None)
        self.max_results = kwargs.pop("max_results", None)

        self.search_kwargs = kwargs.copy()

        self.results = None
        self.loaded_docs = 0
        self.select_fields = None

    def reset(self):
        self.cursorMark = "*"
        self.results = None
        self.loaded_docs = 0

    def has_next(self):
        # We cannot use CursorMarkets with Grouping. We will look if the
        # number of results is less than the informed limit
        is_group = "group" in self.search_kwargs and "true" == self.search_kwargs[str("group")]

        if self.max_results and self.loaded_docs >= self.max_results:
            return False

        if is_group:
            valid_limit = self.limit if self.limit is not None and self.limit < self.max_limit else self.max_limit
            return self.results is None or (0 < len(self.results["groups"]) <= valid_limit)
        else:
            return self.results is None or self.cursorMark != self.results[SolrSearchPaginator.NEXT_CURSORMARK_FIELD]

    def next(self):
        if self.has_next():
            # We cannot use CursorMarkets with Grouping. We will look if the
            # number of results is less than the informed limit
            is_group = "group" in self.search_kwargs and "true" == self.search_kwargs[str("group")]

            if is_group:
                self.search_kwargs[str("start_offset")] = self.loaded_docs

                self.search_kwargs["end_offset"] = self.loaded_docs + (
                    self.limit if self.limit is not None and (self.limit < self.max_limit) else self.max_limit
                )
            else:

                # Save the next cursor mark as the actual cursor mark to send
                # to the server
                if self.results:
                    self.cursorMark = self.results[SolrSearchPaginator.NEXT_CURSORMARK_FIELD]

                # Signaling the cursor mark
                if "start_offset" in self.search_kwargs:
                    del self.search_kwargs[str("start_offset")]

                self.search_kwargs["end_offset"] = (
                    self.limit if self.limit is not None and self.limit < self.max_limit else self.max_limit
                )

                self.search_kwargs[SolrSearchPaginator.CURSORMARK_FIELD] = self.cursorMark

            # Do the search
            self.results = self.backend.search(
                query_string=self.query_string, percent_score=self.percent_score, **self.search_kwargs
            )

            if is_group:
                groups_size = len(self.results["groups"])
                self.loaded_docs += groups_size
                if self.max_results and self.loaded_docs > self.max_results:
                    extra_values = self.loaded_docs - self.max_results
                    if extra_values < groups_size:
                        new_groups = {}
                        for key in list(self.results["groups"])[: groups_size - extra_values]:
                            new_groups[key] = self.results["groups"][key]
                        self.results["groups"] = new_groups
            else:
                results_size = len(self.results["results"])
                self.loaded_docs += results_size
                if self.max_results and self.loaded_docs > self.max_results:
                    extra_values = self.loaded_docs - self.max_results
                    if extra_values < results_size:
                        self.results["results"] = self.results["results"][: results_size - extra_values]

            return self.results
        else:
            return EmptyResults()


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False

    return str(uuid_obj) == uuid_to_test
