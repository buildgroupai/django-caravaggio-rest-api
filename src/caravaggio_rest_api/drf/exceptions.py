# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
from django.core.exceptions import ValidationError

from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import exception_handler


def caravaggio_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data["status"] = response.status_code
    elif isinstance(exc, ValidationError):
        return Response(data={'detail': exc.message, "status": HTTP_400_BAD_REQUEST},
                        status=HTTP_400_BAD_REQUEST)

    return response
