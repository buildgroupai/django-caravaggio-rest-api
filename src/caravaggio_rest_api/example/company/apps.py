# -*- coding: utf-8 -*-
from django.apps import AppConfig


class ExampleCompanyConfig(AppConfig):
    name = 'caravaggio_rest_api.example.company'

    def ready(self):
        from caravaggio_rest_api.example.company.api import serializers
