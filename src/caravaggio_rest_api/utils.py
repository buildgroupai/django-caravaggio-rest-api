# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import dateutil
from datetime import datetime

try:
    from dse.cqlengine import columns
except ImportError:
    from cassandra.cqlengine import columns


from django.db import connections
from django_cassandra_engine.models import DjangoCassandraModel
from django_cassandra_engine.utils import get_engine_from_db_alias


def mk_datetime(datetime_str):
    """
    Process ISO 8661 date time formats https://en.wikipedia.org/wiki/ISO_8601
    """
    return dateutil.parser.parse(datetime_str)


def quarter(date):
    return (date.month - 1) // 3 + 1


def week_of_year(date):
    """
    Our weeks starts on Mondays

    %W - week number of the current year, starting with the first
         Monday as the first day of the first week

    :param date: a datetime object
    :return: the week of the year
    """
    return date.strftime("%W")


def default(o):
    """Used to dump objects into json when the objects have datetime members"""
    if type(o) is datetime:
        return o.isoformat()
    if isinstance(o, (columns.UUID, columns.TimeUUID)):
        return str(o)


def get_database(model, alias=None):
    if alias:
        return connections[alias]

    for alias in connections:
        engine = get_engine_from_db_alias(alias)
        if issubclass(model, DjangoCassandraModel):
            if engine == "django_cassandra_engine":
                return connections[alias]
        elif not engine == "django_cassandra_engine":
            return connections[alias]

    raise AttributeError("Database not found!")


def get_keyspace(alias=None):
    if alias:
        return connections[alias]

    for alias in connections:
        engine = get_engine_from_db_alias(alias)
        if engine == "django_cassandra_engine":
            return connections[alias].settings_dict.get('NAME', '')

    raise AttributeError("Database not found!")


def delete_all_records(model_clazz, database=None):
    if issubclass(model_clazz, DjangoCassandraModel):
        conn = get_database(model_clazz, database)
        conn.connection.execute(
            "TRUNCATE {};".format(model_clazz.objects.column_family_name))
    else:
        model_clazz.objects.all().delete()


def get_primary_keys_values(instance, model):
    return {pk: getattr(instance, pk)
            for pk in model._primary_keys.keys()}
