# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from django.db import connections

from django.test.runner import DiscoverRunner

from django_cassandra_engine.utils import get_engine_from_db_alias

from caravaggio_rest_api.management.commands.sync_indexes import sync


class TestRunner(DiscoverRunner):
    def __init__(self, keep_indexes=None, **kwargs):
        super().__init__(**kwargs)

        self.keep_indexes = keep_indexes

    @classmethod
    def add_arguments(cls, parser):
        DiscoverRunner.add_arguments(parser)

        parser.add_argument(
            '-ki', '--keep-indexes', action='store_true', dest='keep_indexes',
            help='Preserves the test DB Indexes between runs.'
        )

    def setup_databases(self, **kwargs):
        old_config = super().setup_databases(**kwargs)

        if not self.keep_indexes:
            for alias in connections:
                engine = get_engine_from_db_alias(alias)
                if engine == 'django_cassandra_engine':
                    sync(alias)

        return old_config