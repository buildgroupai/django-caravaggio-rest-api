# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers, fields
from drf_queryfields import QueryFieldsMixin

from haystack.models import SearchResult
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework_cache.serializers import CachedSerializerMixin
from rest_framework_cache.settings import api_settings

from caravaggio_rest_api import fields as dse_fields
from caravaggio_rest_api.dse.columns import Decimal, KeyEncodedMap
from caravaggio_rest_api.utils import get_primary_keys_values

try:
    from dse.cqlengine import columns
except ImportError:
    from cassandra.cqlengine import columns


def _is_nested_proxy_field(field):
    """Check if field is nested proxy field.
    :param field:
    :type field:
    :return: True or False
    :rtype: bool
    """
    return (
        isinstance(field, UserTypeSerializer)
    )


def extract_nested_serializers(serializer,
                               validated_data,
                               nested_serializers=None,
                               nested_serializers_data=None):
    """Extract nested serializers.
    :param serializer: Serializer instance.
    :param validated_data: Validated data.
    :param nested_serializers:
    :param nested_serializers_data:
    :type serializer: rest_framework.serializers.Serializer
    :type validated_data: dict
    :type nested_serializers: dict
    :type nested_serializers_data:
    :return:
    :rtype: tuple
    """
    if nested_serializers is None:
        nested_serializers = {}
    if nested_serializers_data is None:
        nested_serializers_data = {}

    for __field_name, __field in serializer.fields.items():
        if _is_nested_proxy_field(__field) \
                and __field_name in validated_data:
            __serializer_data = validated_data.pop(
                __field_name
            )
            nested_serializers[__field_name] = __field
            nested_serializers_data[__field_name] = __serializer_data

    return nested_serializers, nested_serializers_data


def set_instance_values(nested_serializers,
                        nested_serializers_data,
                        instance):
    """Set values on instance.
    Does not perform any save actions.
    :param nested_serializers: Nested serializers.
    :param nested_serializers_data: Nested serializers data.
    :param instance: Instance (not yet saved)
    :type nested_serializers:
    :type nested_serializers_data:
    :type instance:
    :return: Same instance with values set.
    :rtype:
    """
    for __serializer_name, __serializer in nested_serializers_data.items():
        for __field_name, __field_value in __serializer.items():
            if _is_nested_proxy_field(
                    nested_serializers[__serializer_name][__field_name]):
                set_instance_values({
                    __field_name: nested_serializers[
                        __serializer_name][__field_name]},
                    {__field_name: __field_value},
                    instance)
        userType = getattr(nested_serializers[
                               __serializer_name].Meta, '__type__', None)
        setattr(instance, __serializer_name, userType(**__serializer))


def deserialize_instance(serializer, model):
    # Collect information on nested serializers
    __nested_serializers, __nested_serializers_data = \
        extract_nested_serializers(
            serializer,
            serializer.validated_data,
        )

    # Create instance, but don't save it yet
    instance = model(**serializer.validated_data)

    # Assign fields to the `instance` one by one
    set_instance_values(
        __nested_serializers,
        __nested_serializers_data,
        instance
    )

    return instance


def get_haystack_cache_key(instance, serializer, protocol):
    """Get cache key of instance"""
    params = {"id": instance.pk,
              "app_label": instance.model._meta.app_label,
              "model_name": instance.model._meta.object_name,
              "serializer_name": serializer.__name__,
              "protocol": protocol}

    return api_settings.SERIALIZER_CACHE_KEY_FORMAT.format(**params)


def get_cache_key(instance, serializer, protocol):
    """Get cache key of instance"""
    _id = "|".join([
        "{0}:{1}".format(key, repr(value))
        for (key, value) in get_primary_keys_values(
            instance, instance).items()])

    params = {"id": _id,
              "app_label": instance._meta.app_label,
              "model_name": instance._meta.object_name,
              "serializer_name": serializer.__name__,
              "protocol": protocol}

    return api_settings.SERIALIZER_CACHE_KEY_FORMAT.format(**params)


class BaseCachedSerializerMixin(CachedSerializerMixin):

    def _get_cache_key(self, instance):
        request = self.context.get('request')
        protocol = request.scheme if request else 'http'
        return get_haystack_cache_key(instance, self.__class__, protocol) \
            if isinstance(instance, SearchResult) \
            else get_cache_key(instance, self.__class__, protocol)


class UserTypeSerializer(serializers.Serializer):
    pass


class CassandraModelSerializer(QueryFieldsMixin,
                               serializers.HyperlinkedModelSerializer):

    serializers.ModelSerializer.serializer_field_mapping[
        columns.UUID] = fields.UUIDField
    serializers.ModelSerializer.serializer_field_mapping[columns.Integer] = \
        fields.IntegerField
    serializers.ModelSerializer.serializer_field_mapping[columns.SmallInt] = \
        fields.IntegerField
    serializers.ModelSerializer.serializer_field_mapping[columns.BigInt] = \
        fields.IntegerField
    serializers.ModelSerializer.serializer_field_mapping[columns.DateTime] = \
        dse_fields.CassandraDateTimeField
    serializers.ModelSerializer.serializer_field_mapping[columns.Time] = \
        fields.TimeField
    serializers.ModelSerializer.serializer_field_mapping[columns.Date] = \
        dse_fields.CassandraDateField
    serializers.ModelSerializer.serializer_field_mapping[columns.Text] = \
        fields.CharField
    serializers.ModelSerializer.serializer_field_mapping[columns.Float] = \
        fields.FloatField
    serializers.ModelSerializer.serializer_field_mapping[columns.Double] = \
        fields.FloatField
    serializers.ModelSerializer.serializer_field_mapping[Decimal] = \
        fields.DecimalField
    serializers.ModelSerializer.serializer_field_mapping[columns.Boolean] = \
        fields.BooleanField
    serializers.ModelSerializer.serializer_field_mapping[columns.Blob] = \
        fields.FileField
    serializers.ModelSerializer.serializer_field_mapping[KeyEncodedMap] = \
        fields.DictField

    # The DSE/Cassandra Decimal column is not supported by the DRF-Haystack
    # fields.Decimal serializer, we need to use fields.CharField instead.
    # See: https://github.com/inonit/drf-haystack/issues/116
    serializers.ModelSerializer.serializer_field_mapping[columns.Decimal] = \
        fields.CharField

    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: "Bad Request"
        }

    def create(self, validated_data):
        """Create.
        :param validated_data:
        :return:
        """
        instance = deserialize_instance(self, self.Meta.model)

        # Save the instance and return
        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update.
        :param instance:
        :param validated_data:
        :return:
        """
        # Collect information on nested serializers
        __nested_serializers, __nested_serializers_data = \
            extract_nested_serializers(
                self,
                validated_data,
            )

        # Update the instance
        instance = super(CassandraModelSerializer, self).update(
            instance,
            validated_data
        )

        # Assign fields to the `instance` one by one
        set_instance_values(
            __nested_serializers,
            __nested_serializers_data,
            instance
        )

        # Save the instance and return
        instance.save()
        return instance


class CustomHaystackSerializer(HaystackSerializer):

    _abstract = True

    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: 'Bad Request'
        }
