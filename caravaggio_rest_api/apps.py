# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 PreSeries Tech, SL
# All rights reserved.

from django.apps import AppConfig


class CaravaggioRESTAPIConfig(AppConfig):
    name = 'caravaggio_rest_api'
    verbose_name = "Django Caravaggio REST API"

    def ready(self):
        pass
        # Add System checks
        # from .checks import pagination_system_check  # NOQA
