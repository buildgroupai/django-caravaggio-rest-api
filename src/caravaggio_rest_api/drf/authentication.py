# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging

from django.contrib.auth.models import AnonymousUser

from caravaggio_rest_api.users.models import CaravaggioOrganization, CaravaggioUser
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from rest_framework.authentication import TokenAuthentication

_logger = logging.getLogger("caravaggio_rest_api.drf.authentication")


def get_organization(request):
    if request.user.is_superuser or isinstance(request.user, AnonymousUser):
        return None

    query_params = request.query_params if hasattr(request, "query_params") else request.GET
    if "_org_id" in query_params:
        _org_id = query_params["_org_id"]
        try:
            organization = CaravaggioOrganization.objects.get(id=_org_id)
            if organization in request.user.organizations.all():
                return organization
        except Exception:
            _logger.error(f"Unable to obtain the organization with id {_org_id}")
            return None

    else:
        organizations = request.user.organizations.all()
        if organizations:
            return organizations[0]

    return None


class TokenAuthSupportQueryString(TokenAuthentication):
    """
    Extend the TokenAuthentication class to support querystring authentication
    in the form of "http://www.example.com/?auth_token=<token_key>"
    """

    def authenticate(self, request):
        # Check if 'token_auth' is in the request query params.
        # Give precedence to 'Authorization' header.
        query_params = request.query_params if hasattr(request, "query_params") else request.GET
        if settings.REST_FRAMEWORK["QUERY_STRING_AUTH_TOKEN"] in query_params and (
            "HTTP_AUTHORIZATION" not in request.META
        ):
            user_auth_tuple = self.authenticate_credentials(
                query_params.get(settings.REST_FRAMEWORK["QUERY_STRING_AUTH_TOKEN"])
            )
        else:
            user_auth_tuple = super(TokenAuthSupportQueryString, self).authenticate(request)

        if user_auth_tuple is None:
            return None

        request.organization = SimpleLazyObject(lambda: get_organization(request))
        return user_auth_tuple
