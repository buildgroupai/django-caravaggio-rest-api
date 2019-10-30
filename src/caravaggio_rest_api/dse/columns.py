# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging

try:
    from dse.cqlengine import columns, ValidationError
except ImportError:
    from cassandra.cqlengine import columns, ValidationError


LOGGER = logging.getLogger(__name__)


class KeyEncodedMap(columns.Map):
    """
    This type of Map is needed if we want to be able to index the Map columns
    into the Search index. The search index creates a dynamic field that
    looks for any value with name <db_field_name>_*
    """

    def __keyencode__(self, key):
        return "{0}_{1}".format(self.column_name, str(key))

    def __keydecode__(self, key):
        prefix = "{}_".format(self.column_name)
        if key.startswith(prefix):
            return key[len(prefix):]
        return key

    def to_python(self, value):
        if value is None:
            return {}
        if value is not None:
            return dict((self.key_col.to_python(self.__keydecode__(k)),
                         self.value_col.to_python(v))
                        for k, v in value.items())

    def to_database(self, value):
        if value is None:
            return None
        return dict((self.key_col.to_database(self.__keyencode__(k)),
                     self.value_col.to_database(v)) for k, v in value.items())


class InetAddress(columns.Inet):
    """ Inet column with validation

    """

    def validate(self, value):
        """
        Returns a cleaned and validated value. Raises a ValidationError
        if there's a problem
        """
        if value is None:
            import ipaddress
            try:
                ipaddress.ip_address(value)
            except ValueError:
                raise ValidationError(
                    '{0} - {1} does not appear to be an'
                    ' IPv4 or IPv6 address for field'.format(
                        (self.column_name or self.db_field), value))
        return value


class Decimal(columns.Decimal):
    """
    This field is to fix a problem in DRF-Haystack that needs a value
    for the fields `max_digits` and `decimal_places`
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
