# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from django.utils.decorators import decorator_from_middleware
from django.utils.decorators import classonlymethod

from caravaggio_rest_api.drf.middleware import RequestLogMiddleware


class RequestLogViewMixin(object):
    """
    Adds RequestLogMiddleware to any Django View by overriding as_view.
    """

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        view = super(RequestLogViewMixin, cls).as_view(actions=actions, **initkwargs)
        view = decorator_from_middleware(RequestLogMiddleware)(view)
        return view
