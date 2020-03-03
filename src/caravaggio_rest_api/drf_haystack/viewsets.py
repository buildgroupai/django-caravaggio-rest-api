# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
"""
In this module we define the base classes we must use in our applications
to define ViewSets that are directly related to classes defined in our
persistence model.

We have 2 different kinds of ViewSets you can use when working with DSE models:

CaravaggioCassandraModelViewSet: our ViewSet is associated to a Cassandra
    model. This viewset doesn't provide searches capabilities, only basic CRUD
    operations.

CaravaggioHaystackModelViewSet: our ViewSet is associated to a Cassandra
    model that has an index associated to it defined in `search_indexes.py`.
    This viewset provides fast search capabilities, and facets.

We have also a custom paginator class `CaravaggioHaystackPageNumberPagination`
responsible for processing the results provided by the Solr search and read
the associated persistent objects from the Cassandra backend. It's also
responsible for the parsing of special Solr fields that we get from the search,
such as `distance` in spatial queries or `score` of each result.

"""

import logging

from collections import OrderedDict

from django.contrib.gis.measure import Distance

from caravaggio_rest_api.drf.mixins import RequestLogViewMixin
from caravaggio_rest_api.drf.viewsets import CaravaggioThrottledViewSet
from caravaggio_rest_api.utils import get_primary_keys_values

try:
    from dse.cqlengine.columns import UUID, TimeUUID
except ImportError:
    from cassandra.cqlengine.columns import UUID, TimeUUID


from drf_haystack import filters, mixins
from drf_haystack.viewsets import HaystackViewSet
from haystack.exceptions import SpatialError

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from caravaggio_rest_api.haystack.query import CaravaggioSearchQuerySet
from caravaggio_rest_api.pagination import CustomPageNumberPagination

from caravaggio_rest_api.drf_haystack.filters import \
    HaystackOrderingFilter, \
    CaravaggioHaystackFilter, \
    CaravaggioHaystackFacetFilter

LOGGER = logging.getLogger("caravaggio_rest_api")


class CaravaggioHaystackPageNumberPagination(CustomPageNumberPagination):
    def get_paginated_response(self, data):

        if data and len(data):
            has_distance = False
            loaded_objects = []
            for instance in data.serializer.instance:
                model = instance.model

                try:
                    distance = getattr(instance, "distance", None)
                    if not has_distance and isinstance(distance, Distance):
                        has_distance = True
                except SpatialError as ex:
                    pass

                if "request" in data.serializer.context and (
                        "fields" in data.serializer.context["request"].GET):
                    filter_fields = list(model._primary_keys.keys())
                    selected_fields = data.serializer.context[
                        "request"].GET["fields"].split(",")
                    filter_fields.extend(list(selected_fields))
                    instance = model(**dict(zip(
                        filter_fields,
                        model.objects.all().filter(
                            **get_primary_keys_values(
                                instance, instance.model)).values_list(
                            *filter_fields, flat=False).first())))

                    # Used by the caching process
                    instance._caravaggio_fields = selected_fields
                    loaded_objects.append(instance)
                else:
                    loaded_objects.append(
                        model.objects.all().
                        filter(**get_primary_keys_values(
                            instance, instance.model)).
                        first())

            # Get the results serializer from the original View that originated
            # the current response
            results_serializer = \
                data.serializer.context['view'].results_serializer_class

            extra_args = {
                "context": data.serializer.context
            }

            if "request" in data.serializer.context and (
                    "fields" in data.serializer.context["request"].GET):
                extra_args["fields"] = data.serializer.context[
                    "request"].GET["fields"].split(",")

            serializer = results_serializer(
                loaded_objects, many=True, **extra_args)
            detail_data = serializer.data

            # Copy the relevance score into the model object
            for i_obj, obj in enumerate(detail_data):
                obj["score"] = data[i_obj].get("score", None)

            # Copy the distance field if it exists in the results
            if has_distance:
                for i_obj, obj in enumerate(detail_data):
                    obj["distance"] = data[i_obj].get("distance", None)

            data = detail_data

        return Response(OrderedDict([
            ('total', self.page.paginator.count),
            ('page', len(data)),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class CaravaggioCassandraModelViewSet(
        CaravaggioThrottledViewSet,
        viewsets.ModelViewSet,
        RequestLogViewMixin):
    """ We use this ViewSet as a base class when we are working with and
    endpoint that is directly connected with a Cassandra model class (DSE)

    Filters are not allowed here. If we need filtering support, we need
    to define a search index for the model in `search_indexes.py` and define
    the ViewSet as a specific class of CaravaggioHaystackViewSet.

    """
    filter_backends = []


class CaravaggioHaystackModelViewSet(
        CaravaggioThrottledViewSet,
        HaystackViewSet,
        RequestLogViewMixin):
    """ We use this ViewSet as a base class when we are working with and
    endpoint that is directly connected with a Cassandra model class and
    has an index defined in the `search_indexes.py` file for it, activating
    the support for Solr queries.

    By default this kind of ViewSet uses the following filters:

    HaystackFilter : allows normal searches using Solr as backend

    HaystackBoostFilter : activates the use of the term boosting in our
        queries. See `Term Boost <https://drf-haystack.readthedocs.io/en/
        latest/06_term_boost.html>`

        Examples:

        # Slight increase in relevance for documents that include "hood".
        /api/v1/search/?firstname=robin&boost=hood,1.1

        # Big decrease in relevance for documents that include "batman".
        /api/v1/search/?firstname=robin&boost=batman,0.8


    HaystackOrderingFilter : a custom implementation of the filter
        `drf_haystack.filters.HaystackOrderingFilter` support ordering by
         fields that have been defined as facet field. We do that because we
         need to prepend a "_exact" construct to the field name in order
         to work in Solr.

    See Also
    --------
    drf haystack filters:
        <https://drf-haystack.readthedocs.io/en/latest/index.html>

    """
    filter_backends = [CaravaggioHaystackFilter,
                       filters.HaystackBoostFilter,
                       HaystackOrderingFilter]

    # ordering_fields = None

    pagination_class = CaravaggioHaystackPageNumberPagination

    http_method_names = ['get']

    document_uid_field = "id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Checking if the base class has defined some required attributes in
        # the class
        if not hasattr(self, 'index_models'):
            raise AttributeError(
                'You need to define the attribute "index_models"')


class CaravaggioHaystackFacetSearchViewSet(
        CaravaggioThrottledViewSet,
        mixins.FacetMixin,
        RequestLogViewMixin,
        HaystackViewSet):
    """ This viewset extends the normal Haystack Search adding support for
    Facet queries through a new filter added to the list of `filter_backends`

    Extra filters:

    HaystackFacetFilter : allows facet searches. To do so, this filter
        is prepending the /facets endpoint to the base haystack search
        endpoing.

        Examples of facet searches:

        # Return all entries with zip_code 0351 within 10 kilometers from
        # the location with latitude 59.744076 and longitude 10.152045
        /api/v1/search/facets

    In our serializer we will need to declare a special Meta attribute
    `field_options` where we will inform about the special treatment we
    should be doing to each facet. This is specially necessary (or useful)
    when we want to create facets (bins) for specific fields, like date.
    """

    pagination_class = CaravaggioHaystackPageNumberPagination

    object_class = CaravaggioSearchQuerySet

    facet_filter_backends = [CaravaggioHaystackFilter,
                             filters.HaystackBoostFilter,
                             CaravaggioHaystackFacetFilter,
                             HaystackOrderingFilter]

    filter_backends = [CaravaggioHaystackFilter,
                       filters.HaystackBoostFilter,
                       CaravaggioHaystackFacetFilter,
                       HaystackOrderingFilter]

    http_method_names = ['get']

    document_uid_field = "id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Checking if the base class has defined some required attributes in
        # the class
        if not hasattr(self, 'index_models'):
            raise AttributeError(
                'You need to define the attribute "index_models"')

        # Checking if the base class has defined some required attributes in
        # the class
        if not hasattr(self, 'facet_serializer_class'):
            raise AttributeError(
                'You need to define the attribute "facet_serializer_class"')


class CaravaggioHaystackGEOSearchViewSet(CaravaggioHaystackModelViewSet):
    """ This viewset extends the normal Haystack Search adding support for
    spatial searches adding a new filter to the list of filter backends

    Extra filters:

    HaystackGEOSpatialFilter : allows spatial searches. To do so, this filter
        is expecting to find a LocationField in our index model with the name
        `coordinates`. We can change this redefining the viewset class
        attribute `point_field` to pointing to other field name.

        The following query paramters must be present in each request to this
         type of endpoint:
            unit : <https://docs.djangoproject.com/en/2.2/ref/contrib/
            gis/measure/#supported-units>
            from : must contain a `from` parameter which is a comma separated
             longitude and latitude value.

        Examples of searches:

        # Return all entries with zip_code 0351 within 10 kilometers from
        # the location with latitude 59.744076 and longitude 10.152045
        /api/v1/search/?zip_code=0351&km=10&from=59.744076,10.152045


    The viewsets needs information about the serializer to be use with the
    results, and we need to inform this on the `results_serializer_class` class
    attribute.

    The `serializer_class` attribute informs about the serializer used to parse
    the search requests adding fields like text, autocomplete, score, etc.

    """

    filter_backends = [CaravaggioHaystackFilter,
                       filters.HaystackBoostFilter,
                       filters.HaystackGEOSpatialFilter,
                       HaystackOrderingFilter]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Checking if the base class has defined some required attributes in
        # the class

        if not hasattr(self, 'results_serializer_class'):
            raise AttributeError(
                'You need to define the attribute "results_serializer_class"')
