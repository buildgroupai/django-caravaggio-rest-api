# -*- coding: utf-8 -*
# Copyright (c) 2020 BuildGroup Data Services Inc.
from haystack import connection_router, connections


class CaravaggioSearchPaginator(object):
    def __init__(self, **kwargs):
        self.original_kwargs = kwargs

        if "max_limit" not in self.original_kwargs:
            self.original_kwargs["max_limit"] = 200

        self.implementation = None
        self.backend = None

        self._determine_backend()

    def _determine_backend(self):
        # A backend has been manually selected. Use it instead.
        using = self.original_kwargs.get("using", None)
        if using is not None:
            connection = connections[using]
        else:
            # No backend, so rely on the routers to figure out what's right.
            hints = {"models": self.original_kwargs.get("models", None)}

            backend_alias = connection_router.for_read(**hints)

            connection = connections[backend_alias]

        backend = connection.get_backend()

        if not self.implementation:
            if hasattr(connection, "solr_paginator") and self.original_kwargs.get("group", "false") == "true":
                self.implementation = connection.solr_paginator(backend=backend, **self.original_kwargs)
            elif hasattr(connection, "solr_paginator") and self.original_kwargs.get("percent_score", False):
                self.implementation = connection.solr_paginator(backend=backend, **self.original_kwargs)
            else:
                self.implementation = connection.paginator(backend=backend, **self.original_kwargs)
        self.backend = backend

    def reset(self):
        self.implementation.reset()

    def models(self, *models):
        if not models:
            if "models" in self.implementation.search_kwargs:
                del self.implementation.search_kwargs["models"]
        else:
            self.implementation.search_kwargs["models"] = models

        self._determine_backend()
        return self

    def select(self, *fields):
        self.implementation.select_fields = fields
        if not self.implementation.select_fields:
            if "fl" in self.implementation.search_kwargs:
                del self.implementation.search_kwargs["fl"]
        else:
            if "score" not in fields:
                fields = list(fields)
                fields.append("score")
            self.implementation.search_kwargs["fl"] = fields
        return self

    def get_hits(self):
        return self.implementation.results["hits"] if self.implementation.results is not None else None

    def get_results(self):
        is_group = (
            "group" in self.implementation.search_kwargs and "true" == self.implementation.search_kwargs[str("group")]
        )

        if is_group:
            return self.implementation.results["groups"] if self.implementation.results is not None else None
        else:
            return self.implementation.results["results"] if self.implementation.results is not None else None

    def get_raw_results(self):
        return self.implementation.results

    def get_loaded_docs(self):
        return self.implementation.loaded_docs

    def has_next(self):
        return self.implementation.has_next()

    def next(self):
        return self.implementation.next()
