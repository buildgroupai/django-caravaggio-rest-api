# -*- coding: utf-8 -*-
import logging
import uuid

from django.utils import timezone

try:
    from dse.cqlengine import columns, ValidationError
    from dse.cqlengine.columns import UserDefinedType
    from dse.cqlengine.usertype import UserType
except ImportError:
    from cassandra.cqlengine import columns, ValidationError
    from cassandra.cqlengine.columns import UserDefinedType
    from cassandra.cqlengine.usertype import UserType

from caravaggio_rest_api.dse.columns import \
    KeyEncodedMap

from caravaggio_rest_api.dse.models import \
    CustomDjangoCassandraModel

from django.dispatch import receiver
from django.db.models.signals import pre_save

LOGGER = logging.getLogger("caravaggio_rest_api.example.company")


class Address(UserType):
    """
    A User Defined type for model an Address, a unit value to be consolidated
    """
    __type_name__ = "address"

    street_type = columns.Text()
    street_name = columns.Text()
    street_number = columns.Integer()
    city = columns.Text()
    region = columns.Text()
    state = columns.Text()
    country_code = columns.Text(min_length=3, max_length=3)
    zipcode = columns.Text()


class Company(CustomDjangoCassandraModel):
    """
    A public traded company
    """
    __table_name__ = "company"

    # A unique identifier of the entity
    _id = columns.UUID(partition_key=True, default=uuid.uuid4)

    # The owner of the data. Who own's the company data persisted
    user = columns.Text(primary_key=True)

    # When was created the entity and the last modification date
    created_at = columns.DateTime(default=timezone.now)
    updated_at = columns.DateTime(default=timezone.now)

    # Controls if the entity is active or has been deleted
    is_deleted = columns.Boolean(default=False)
    deleted_reason = columns.Text()

    # The name of the company
    name = columns.Text(required=True)

    # A short description about the company
    short_description = columns.Text()

    # The company domain (e.g. buildgroupai.com)
    domain = columns.Text(max_length=50)

    # The date when the company was founded
    foundation_date = columns.Date()

    # The date of the latest funding round
    last_round = columns.Date()

    # The total number of funding rounds
    round_notes = columns.Text()

    # Country of the company
    # ISO 3166-1 alpha 3 code
    country_code = columns.Text(min_length=3, max_length=3)

    # The stock trading symbol
    stock_symbol = columns.Text()

    # Contact email of the company
    contact_email = columns.Text()

    # The number of employees
    headcount = columns.Integer()

    # The number of employees
    company_score = columns.Float()

    # The IDs of the founders of the company
    founders = columns.List(value_type=columns.UUID)

    # Address of the headquarters of the company
    address = UserDefinedType(Address)

    # A list of specialties of the company
    specialties = columns.List(value_type=columns.Text)

    # The counters of the latest followers in twitter
    #  (example of list of integers)
    latest_twitter_followers = columns.List(value_type=columns.Integer)

    # A field that represent a map of key-value
    # We use caravaggio KeyEncodedMap that appends the field name
    # to each of the keys in order to make them indexable by the
    # Search Indexer.
    websites = KeyEncodedMap(
        key_type=columns.Text, value_type=columns.Text)

    # A field that represents a raw JSON with the crawler configurations, each
    # key is a reference to a crawler
    crawler_config = columns.Text()

    # A field that represents a raw JSON content
    extra_data = columns.Text()

    latitude = columns.Float()
    longitude = columns.Float()

    coordinates = columns.Text()

    class Meta:
        get_pk_field = '_id'

    def validate(self):
        super(Company, self).validate()
        if self.name == "test":
            raise ValidationError('The company name cannot be test')


# We need to set the new value for the changed_at field
@receiver(pre_save, sender=Company)
def pre_save_company(
        sender, instance=None, using=None, update_fields=None, **kwargs):
    instance.updated_at = timezone.now()

    if instance.longitude and instance.latitude:
        instance.coordinates = "{0},{1}".format(
            instance.latitude, instance.longitude)
