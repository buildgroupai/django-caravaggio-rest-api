# -*- coding: utf-8 -*
# Copyright (c) 2018 PreSeries Tech, SL
from haystack import connection_router, connections
from haystack.backends import EmptyResults


class CaravaggioSearchPaginator(object):

    CURSORMARK_FIELD = 'cursorMark'
    NEXT_CURSORMARK_FIELD = 'nextCursorMark'

    def __init__(self, query_string, models=None, limit=None, using=None,
                 max_limit=200, **kwargs):

        self.using = using
        self.query_string = query_string
        self.limit = limit
        self.cursorMark = "*"
        self.max_limit = max_limit
        self.search_kwargs = kwargs.copy()
        if models:
            self.search_kwargs["models"] = models
        self.results = None
        self.loaded_docs = 0
        self.select_fields = None

        self._determine_backend()

    def reset(self):
        self.cursorMark = "*"
        self.results = None
        self.loaded_docs = 0

    def models(self, *models):
        if not models:
            if "models" in self.search_kwargs:
                del self.search_kwargs["models"]
        else:
            self.search_kwargs["models"] = models

        self._determine_backend()
        return self

    def select(self, *fields):
        self.select_fields = fields
        if not self.select_fields:
            if "fl" in self.search_kwargs:
                del self.search_kwargs["fl"]
        else:
            if "score" not in fields:
                fields = list(fields)
                fields.append("score")
            self.search_kwargs["fl"] = fields
        return self

    def _determine_backend(self):
        # A backend has been manually selected. Use it instead.
        if self.using is not None:
            self.backend = connections[self.using].get_backend()
            return

        # No backend, so rely on the routers to figure out what's right.
        hints = {'models': self.models}

        backend_alias = connection_router.for_read(**hints)

        self.backend = connections[backend_alias].get_backend()

    def get_hits(self):
        return self.results["hits"] if self.results is not None else None

    def get_results(self):
        return self.results["results"] if self.results is not None else None

    def get_raw_results(self):
        return self.results

    def get_loaded_docs(self):
        return self.loaded_docs

    def has_next(self):

        # We cannot use CursorMarkets with Grouping. We will look if the
        # number of results is less than the informed limit
        is_group = 'group' in self.search_kwargs and \
                   'true' == self.search_kwargs[str('group')]

        if is_group:
            valid_limit = self.limit \
                if self.limit is not None and self.limit < self.max_limit \
                else self.max_limit
            return self.results is None or \
                (0 < len(self.results['groups']) <= valid_limit)
        else:
            return self.results is None or self.cursorMark != \
                   self.results[
                       CaravaggioSearchPaginator.NEXT_CURSORMARK_FIELD]

    def next(self):

        if self.has_next():

            # We cannot use CursorMarkets with Grouping. We will look if the
            # number of results is less than the informed limit
            is_group = 'group' in self.search_kwargs and \
                       'true' == self.search_kwargs[str('group')]

            if is_group:
                self.search_kwargs[str('start_offset')] = self.loaded_docs

                self.search_kwargs['end_offset'] = self.loaded_docs + (
                    self.limit if self.limit is not None and
                    self.limit < self.max_limit
                    else self.max_limit)
            else:

                # Save the next cursor mark as the actual cursor mark to send
                # to the server
                if self.results:
                    self.cursorMark = self.results[
                        CaravaggioSearchPaginator.NEXT_CURSORMARK_FIELD]

                # Signaling the cursor mark
                if 'start_offset' in self.search_kwargs:
                    del self.search_kwargs[str('start_offset')]

                self.search_kwargs['end_offset'] = self.limit \
                    if self.limit is not None and \
                    self.limit < self.max_limit else self.max_limit

                self.search_kwargs[
                    CaravaggioSearchPaginator.CURSORMARK_FIELD] = \
                    self.cursorMark

            # Do the search
            self.results = self.backend.search(
                query_string=self.query_string, **self.search_kwargs)

            if is_group:
                self.loaded_docs += len(self.results['groups'])
            else:
                self.loaded_docs += len(self.results['results'])

            return self.results
        else:
            return EmptyResults()
