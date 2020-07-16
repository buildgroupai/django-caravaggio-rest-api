# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from __future__ import unicode_literals

from django.core.cache import caches
from rest_framework.throttling import UserRateThrottle


class CacheUserRateThrottle(UserRateThrottle):
    """
    Source:
    http://www.pedaldrivenprogramming.com/2017/05/
    throttling-django-rest-framwork-viewsets/
    """

    # Using the localmem cache
    cache = caches["deafult"]

    # Using a key similar to the one used in the old version (tastypie)
    cache_format = "%(scope)s_%(identifier)s_accesses"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            identifier = request.user.pk
        else:
            identifier = self.get_ident(request)

        bits = []

        for char in identifier:
            # Sky accepts alphanumeric plus ``@/./+/-/_`` characters
            if char.isalnum() or char in ["@", ".", "+", "-", "_"]:
                bits.append(char)

        safe_string = "".join(bits)

        return self.cache_format % {"scope": self.scope, "identifier": safe_string}

    def throttle_success(self):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        super(CacheUserRateThrottle, self).throttle_success()

        return True
