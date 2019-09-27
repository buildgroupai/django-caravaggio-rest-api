# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from django.conf import settings
from rest_framework.authentication import TokenAuthentication


class TokenAuthSupportQueryString(TokenAuthentication):
    """
    Extend the TokenAuthentication class to support querystring authentication
    in the form of "http://www.example.com/?auth_token=<token_key>"
    """
    def authenticate(self, request):
        # Check if 'token_auth' is in the request query params.
        # Give precedence to 'Authorization' header.
        if settings.REST_FRAMEWORK["QUERY_STRING_AUTH_TOKEN"] \
                in request.query_params and \
                'HTTP_AUTHORIZATION' not in request.META:
            return self.authenticate_credentials(
                    request.query_params.get(
                        settings.REST_FRAMEWORK["QUERY_STRING_AUTH_TOKEN"]))
        else:
            return super(
                TokenAuthSupportQueryString, self).authenticate(request)
