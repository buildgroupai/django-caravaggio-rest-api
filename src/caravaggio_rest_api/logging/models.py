# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from __future__ import unicode_literals
import logging
import uuid
from datetime import datetime

from django.utils import timezone

from caravaggio_rest_api.dse.models import \
    CustomDjangoCassandraModel

from caravaggio_rest_api.dse.columns import \
    InetAddress, KeyEncodedMap

from django.dispatch import receiver
from django.db.models.signals import pre_save

try:
    from dse.cqlengine import columns, ValidationError
    from dse.cqlengine.columns import UserDefinedType
    from dse.cqlengine.usertype import UserType
except ImportError:
    from cassandra.cqlengine import columns, ValidationError
    from cassandra.cqlengine.columns import UserDefinedType
    from cassandra.cqlengine.usertype import UserType

LOGGER = logging.getLogger(__name__)


class ApiAccess(CustomDjangoCassandraModel):
    """ A model to persist all the access made through the API

    """

    __table_name__ = "caravaggio_api_access"

    year_month = columns.Text(partition_key=True)
    """ The combination of year and month for the timestamp associated
    with the request. Ex. 201901.
    We use this field as row keys. Each row will contain the
    access logs made during the month

    """

    time_ms = columns.Integer(primary_key=True, clustering_order="DESC")
    """ Microseconds (to sort data within one row).
    
    """

    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    """ Monotonous UUID(NOT time - based UUID1)

    """

    user = columns.UUID(required=True)
    """ The user that made the request. 
    
    """

    created_at = columns.DateTime(default=timezone.now)
    """ When was created the entity and the last modification date"""

    remote_address = InetAddress(required=True, index=True)
    """ The IP address of the user doing the request 

    """

    server_hostname = columns.Text(required=True)
    """ The name of the host that is processing the request 

    """

    request_method = columns.Text(required=True)
    """ The method of the request 

    """

    request_path = columns.Text(required=True)
    """ The absolute path of the request
     
    """

    request_query_params = KeyEncodedMap(
        key_type=columns.Text, value_type=columns.Text)
    """ We save all the query params informed in the request as a map.
    
    We use caravaggio KeyEncodedMap that appends the field name to each of
    the keys in order to make them indexable by the Search Indexer.
    """

    request_body = columns.Bytes(required=True)
    """ The body of the request made by the user"""

    response_status = columns.SmallInt(required=True)

    response_body = columns.Text(required=True)
    """ The JSON the server responded to the client. If the response is not 
    a JSON response, the body will be replaced by a <<<Streaming>>> text if
    the request is in steamming, or  <<<Not JSON>>> in other case.
    
    """

    run_time = columns.Integer(required=True)

    latitude = columns.Float()
    longitude = columns.Float()

    coordinates = columns.Text()

    class Meta:
        get_pk_field = 'year_month'

    def validate(self):
        super(ApiAccess, self).validate()


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=ApiAccess)
def pre_save_company(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    instance.year_month = \
        datetime.utcfromtimestamp(instance.time_ms).strftime("%Y%m")

    if instance.longitude and instance.latitude:
        instance.coordinates = "{0},{1}".format(
            instance.latitude, instance.longitude)
