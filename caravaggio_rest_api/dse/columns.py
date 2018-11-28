# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging

try:
    from dse.cqlengine import columns
except ImportError:
    from cassandra.cqlengine import columns


LOGGER = logging.getLogger(__name__)


class Decimal(columns.Decimal):
    """
    This field is to fix a problem in DRF-Haystack that needs a value
    for the fields `max_digits` and `decimal_places`

    - See: Fixed issues with picking kwargs for initializing fields.
            Fixes :drf-issue:`116`
    """

    def __init__(self, primary_key=False, partition_key=False, index=False,
                 db_field=None, default=None, required=False,
                 clustering_order=None, discriminator_column=False,
                 static=False, custom_index=False,
                 max_digits=None, decimal_places=None):
        super().__init__(primary_key, partition_key, index, db_field, default,
                         required, clustering_order, discriminator_column,
                         static, custom_index)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
