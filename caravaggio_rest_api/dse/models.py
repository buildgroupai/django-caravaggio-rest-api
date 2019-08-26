# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import logging
import uuid
import six

try:
    from dse.cqlengine.operators import BaseWhereOperator
    from dse.cqlengine import columns
except ImportError:
    from cassandra.cqlengine.operators import BaseWhereOperator
    from cassandra.cqlengine import columns

from datetime import datetime

from django.dispatch import receiver
from django.db.models.signals import pre_init, post_init, \
    pre_delete, post_delete, pre_save, post_save

from django_cassandra_engine.models import DjangoCassandraModel, \
    DjangoCassandraModelMetaClass

from rest_framework_cache.utils import clear_for_instance

LOGGER = logging.getLogger(__name__)


class ExactOperator(BaseWhereOperator):
    """
    The UniqueValidator is filtering the Cassandra queryset using the _exact
    operation, which is an operation that was not defined.

    We need to define the operator here in order to be loaded at runtime
    by the cassandra libraries and register it to the available list of
    operations.

    This problem was caused in the Master classes, in the _id field when we
    POST a new master. This _id was an assigned ID.
    """
    symbol = "EXACT"
    cql_symbol = '='


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


class CustomDjangoCassandraModelMetaClass(DjangoCassandraModelMetaClass):
    """
    Fix of bug in the original DjangoCassandraModelMetaClass. They commented
    the lines that were registering the UserType and this was causing errors
    during the persistence of the entities that contains UserType fields
    """

    def __new__(cls, name, bases, attrs):
        klass = super().__new__(cls, name, bases, attrs)

        udts = []
        for col in attrs["_columns"].values():
            columns.resolve_udts(col, udts)

        for user_type in set(udts):
            user_type.register_for_keyspace(klass._get_keyspace())

        return klass


class CustomDjangoCassandraModel(
    six.with_metaclass(CustomDjangoCassandraModelMetaClass,
                       DjangoCassandraModel)):
    """
    The original DjangoCassandraModel does not implement the callback methods
    something we need, for instance, if we want to clean the DRF cache after
    and update/save/delete operation
    """

    __abstract__ = True

    def __init__(self, *args, **kwargs):
        cls = self.__class__

        pre_init.send(sender=cls, args=args, kwargs=kwargs)
        super().__init__(*args, **kwargs)
        post_init.send(sender=cls, instance=self)

    @classmethod
    def create(cls, **kwargs):
        result = super().create(**kwargs)

        post_save.send(
            sender=cls, instance=result, created=True, raw=False,
        )

        return result

    def save(self):
        pre_save.send(
            sender=self.__class__, instance=self, created=False)

        result = super().save()

        post_save.send(
            sender=self.__class__, instance=self, created=False,
            raw=False, update_fields=self.get_changed_columns(),
        )

        # We also clean the DRF cache
        clear_for_instance(result)

        return result

    def update(self, **values):
        pre_save.send(
            sender=self.__class__, instance=self, created=False)

        result = super().update(**values)

        post_save.send(
            sender=self.__class__, instance=self, created=False,
            raw=False, update_fields=self.get_changed_columns(),
        )

        # We also clean the DRF cache
        clear_for_instance(result)

        return result

    def delete(self):

        pre_delete.send(sender=self.__class__, instance=self)

        super().delete()

        post_delete.send(sender=self.__class__, instance=self)

        # We also clean the DRF cache
        clear_for_instance(self)


class BaseEntity(CustomDjangoCassandraModel):
    """
    The common field that will be shared between all the managed entities
    """
    __abstract__ = True

    # A unique identifier of the entity
    _id = columns.UUID(primary_key=True, default=uuid.uuid4)

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=datetime.utcnow)
    updated_at = columns.DateTime(default=datetime.utcnow)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    class Meta:
        get_pk_field = '_id'


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=BaseEntity)
def set_update_at(sender, instance=None, **kwargs):
    instance.updated_at = datetime.utcnow()
