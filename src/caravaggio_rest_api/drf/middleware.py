# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import socket
import time
import logging
import json

from django.conf import settings

from caravaggio_rest_api.logging.models import ApiAccess

LOGGER = logging.getLogger(__name__)


class RequestLogMiddleware(object):
    """ A Generic RequestLogMiddleware that can be hooked into any
    Django View using decorator_from_middleware
    """
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if settings.REST_FRAMEWORK['LOG_ACCESSES']:
            if response['content-type'] == 'application/json':
                if getattr(response, 'streaming', False):
                    response_body = '<<<Streaming>>>'
                else:
                    content = json.loads(response.content)
                    response_body = json.dumps(
                        content, sort_keys=True, indent=4)
            else:
                response_body = '<<<Not JSON>>>'

            if request.GET:
                request_query_params = {}
                for key, value in request.GET.items():
                    request_query_params[key] = ",".join(value) \
                        if isinstance(value, list) else value
            else:
                request_query_params = None

            log_data = {
                'time_ms': int(request.start_time),

                'user': request.user.pk,

                'remote_address': request.META['REMOTE_ADDR'],
                'server_hostname': socket.gethostname(),

                'request_method': request.method,
                'request_path': request.get_full_path(),
                'request_body': request.body,
                'request_query_params': request_query_params,

                'response_status': response.status_code,
                'response_body': response_body,

                'run_time': time.time() - request.start_time,
            }

            ApiAccess.objects.create(**log_data)

            # save log_data in some way
            LOGGER.info(log_data)

        return response
