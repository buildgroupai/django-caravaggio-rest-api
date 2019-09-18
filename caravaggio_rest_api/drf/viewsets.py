# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging

from django.conf import settings

from rest_framework import viewsets
from rest_framework import filters
from rest_framework_filters.backends import \
    ComplexFilterBackend

LOGGER = logging.getLogger("caravaggio_rest_api")


class CaravaggioThrottledViewSet:
    """ One of the hidden functionalities is the ability to automatically
    register the default Throttle configurations for all the default
    operations.

    See `settings.THROTTLE_OPERATIONS`

    Methods
    -------
    add_throttle(self, operation, rate)
        This method provides a way for register Throttle configurations for
        non-standard actions in the ViewSet.

        It's specially useful when you are prepending urls for custom
        actions to a ViewSet. For instance, in the class
       `caravaggio_rest_api.users.OrganizationViewSet` we have added multiple
        custom actions to manage the members of the organization, for instance
        the `add_member` POST action.

    """
    throttle_scope = ""

    def __init__(self, *args, **kwargs):
        # Registering throttle operations
        for operation in settings.THROTTLE_OPERATIONS.keys():
            scope = "{0}.{1}".format(self.__class__.__name__, operation)
            if scope not in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]:
                settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = \
                    settings.THROTTLE_OPERATIONS[operation]

    def add_throttle(self, operation, rate):
        scope = "{}.{}".format(self.__class__.__name__, operation)
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] = rate

    def get_throttles(self):
        # Only if the scope is not already set we can do that overwriting
        # the method in a subclass
        if not self.throttle_scope:
            if self.action:
                self.throttle_scope = "{0}.{1}". \
                    format(self.__class__.__name__, self.action)
            else:
                # If there is no action we use the DESTROY by default)
                # It can happen if we define a detail_route in the ViewSet
                # and the method (POST, DELETE, etc) used is not the one
                # associated to the detail method.
                self.throttle_scope = "{0}.{1}". \
                    format(self.__class__.__name__, "destroy")

            LOGGER.debug("Throttling Scope: {}".format(self.throttle_scope))
        return super().get_throttles()


class CaravaggioDjangoModelViewSet(
    viewsets.ModelViewSet, CaravaggioThrottledViewSet):
    """ We need to use this class when we work with normal Django Model
    classes, that is, not with Cassandra or Cassandra/Solr configurations.

    It provides basic filtering and ordering capabilities. If you are using
    a Cassandra model, we careful defining the fields you wnat to use for
    query in the `filter_fields` viewset class attribute.

    Methods
    -------
    get_query_fields(self)
        Provides to our endpoints the ability to select the fields we want to
        get back as a response of a request, through the use of the `fields`
        query parameter our the requests.

    We need to use this class when we work with normal Django Model
    classes, that is, not with Cassandra or Cassandra/Solr configurations.

    Some constants are shortcuts to define the available filtering operations
     for each type of potential field.

    Attributes
    ----------
    RELATIONSHIP_OPERATORS_ALL : operations that applies to relationship fields
     in our model. Operations: in, exact

    NUMERIC_OPERATORS_ALL : operations that applies to numeric fields
     in our model. Operations: exact, range, gt, gte, lt, lte

    DATE_OPERATORS_ALL : operations that applies to date/datetime fields
     in our model. Operations: exact, range, gt, gte, lt, lte, in,
     year, month, day, week_day, hour, minute, second

    STRING_OPERATORS_ALL : operations that applies to string fields
     in our model. Operations: exact, iexact, contains, icontains,
     startswith, istartswith, endswith, iendswith, regex, iregex, in

    PK_OPERATORS_ALL : operations that applies to primary key fields
     in our model. Operations: exact, in

    BOOL_OPERATORS_ALL: operations that applies to boolean fields
     in our model. Operations: exact
    """
    RELATIONSHIP_OPERATORS_ALL = ["in", "exact"]
    NUMERIC_OPERATORS_ALL = ['exact', 'range', 'gt', 'gte', 'lt', 'lte']
    DATE_OPERATORS_ALL = ['exact', 'range', 'gt', 'gte', 'lt', 'lte', 'in',
                          'year', 'month', 'day', 'week_day',
                          'hour', 'minute', 'second']
    STRING_OPERATORS_ALL = ['exact', 'iexact', 'contains', 'icontains',
                            'startswith', 'istartswith', 'endswith',
                            'iendswith',
                            'regex', 'iregex', 'in']
    PK_OPERATORS_ALL = ['exact', 'in']
    BOOL_OPERATORS_ALL = ['exact']

    """We use this field to inform about the fields we want to make it 
    filterable.

    For each field, we need to enumerate the list of operations that we make
    available. For instance:

    filterset_fields = {
        "name": STRING_OPERATORS_ALL,
        "date_of_birth": DATE_OPERATORS_ALL,
        "job": ["exact", "in"]
    }

    """
    filterset_fields = None

    filter_backends = [ComplexFilterBackend, filters.OrderingFilter]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Checking if the base class has defined some required attributes in
        # the class
        if not hasattr(self, 'serializer_class'):
            raise AttributeError(
                'You need to define the attribute "serializer_class"')

    def get_query_fields(self):
        custom_query_fields = set()
        raw_fields = self.request.query_params.getlist('fields')

        for item in raw_fields:
            custom_query_fields.update(item.split(','))

        return custom_query_fields

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(
            *args, fields=self.get_query_fields(), **kwargs)
