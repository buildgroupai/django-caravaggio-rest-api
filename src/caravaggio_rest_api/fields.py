# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import json
import datetime
import inspect

from django.utils import six, timezone
from django.utils.timezone import utc

try:
    from dse.cqlengine.usertype import UserType
except ImportError:
    from cassandra.cqlengine.usertype import UserType

from django.contrib.gis.measure import Distance

from rest_framework import fields, serializers, ISO_8601
from rest_framework.settings import api_settings


class CurrentUserNameDefault(object):
    def set_context(self, serializer_field):
        self.user = serializer_field.context["request"].user

    def __call__(self):
        return self.user.username if self.user else None

    def __repr__(self):
        return repr("%s()" % self.__class__.__name__)


class CassandraDateTimeField(fields.DateTimeField):
    """
    Timestamps in Cassandra are timezone-naive timestamps
     encoded as milliseconds since UNIX epoch

    ref: https://datastax.github.io/python-driver/dates_and_times.html
    """

    def enforce_timezone(self, value):
        if timezone.is_aware(value):
            return timezone.make_naive(value, utc)
        else:
            return value


class CassandraDateField(fields.DateField):
    """
    Date object in Cassandra do not have isoformat method
     we need to override the to_representation method to extract the
     date from the cassandra Date first
    """

    def to_representation(self, value):
        if not value:
            return None

        output_format = getattr(self, "format", api_settings.DATE_FORMAT)

        if output_format is None or isinstance(value, six.string_types):
            return value

        # Applying a `DateField` to a datetime value is almost always
        # not a sensible thing to do, as it means naively dropping
        # any explicit or implicit timezone info.
        assert not isinstance(value, datetime.datetime), (
            "Expected a `date`, but got a `datetime`. Refusing to coerce, "
            "as this may mean losing timezone information. Use a custom "
            "read-only field and deal with timezone issues explicitly."
        )

        # We are using Cassandra Model serializers with non Cassandra
        #  objects when doing Solr Searches.
        # The results or Solr searches are SearchResult objects
        # and the dates fields in this case are objects of
        # type datetime.date

        if output_format.lower() == ISO_8601:
            if isinstance(value, datetime.date):
                return value.isoformat()
            return value.date().isoformat()

        return (
            value.strftime(output_format) if isinstance(value, datetime.date) else value.date().strftime(output_format)
        )


class CassandraJSONFieldAsText(fields.JSONField):
    """
    Cassandra do not have support for JSON fields, we need to manage as
    text fields but convert the values to dict objects when serializing them
    through the API.
    """

    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, "is_json_string", False):
                data = json.dumps(json.loads(data))
            else:
                data = json.dumps(data)
        except (TypeError, ValueError):
            self.fail("invalid")
        return data

    def to_representation(self, value):
        return json.loads(value)


class CassandraUDTField(fields.JSONField):
    """
    Cassandra do not have support for JSON fields, we need to manage as
    text fields but convert the values to dict objects when serializing them
    through the API.
    """

    udt = None

    def __init__(self, *args, **kwargs):
        self.udt = kwargs.pop("udt", self.udt)

        assert inspect.isclass(self.udt), "`udt` has been instantiated."
        assert issubclass(self.udt, UserType), (
            "The `child` argument must be an instance of `CharField`, "
            "as the hstore extension stores values as strings."
        )

        super(fields.JSONField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, "is_json_string", False):
                data = self.udt(**json.loads(data))
            else:
                data = self.udt(**data)
        except (TypeError, ValueError):
            self.fail("invalid")
        return data

    def to_representation(self, value):
        return json.loads(value)


class DistanceField(fields.FloatField):
    """
    When we use Spatial queries, a Distance object is generated for the
    distance field.
    """

    udt = None

    def __init__(self, *args, **kwargs):
        self.units = kwargs.pop("units", "m")

        assert isinstance(self.units, str), "The `units` argument must be an instance of `str`."
        assert self.units in Distance.UNITS.keys(), "`{}` invalid units.".format(self.units)

        super(fields.FloatField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            params = {"{}".format(self.units): data}
            data = Distance(**params)
        except (TypeError, ValueError):
            self.fail("invalid")
        return data

    def to_representation(self, value):
        return getattr(value, self.units)
