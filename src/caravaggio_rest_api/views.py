# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from __future__ import unicode_literals

from django.conf import settings

from rest_framework.permissions import AllowAny

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    info=openapi.Info(
        title=settings.CARAVAGGIO_API_TITLE,
        default_version=settings.CARAVAGGIO_API_VERSION,
        description=settings.CARAVAGGIO_API_DESCRIPTION,
        terms_of_service=settings.CARAVAGGIO_API_TERMS_URL,
        contact=openapi.Contact(email=settings.CARAVAGGIO_API_CONTACT),
        license=openapi.License(name=settings.CARAVAGGIO_API_LICENSE),
    ),
    public=True,
    permission_classes=(AllowAny,),
)
