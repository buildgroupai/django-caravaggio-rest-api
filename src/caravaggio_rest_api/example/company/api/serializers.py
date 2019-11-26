# -*- coding: utf-8 -*
from datetime import datetime, timedelta

from caravaggio_rest_api.drf_haystack.serializers import \
    BaseCachedSerializerMixin, CustomHaystackSerializer, \
    CustomHaystackFacetSerializer

from rest_framework import fields, serializers
from rest_framework.status import HTTP_400_BAD_REQUEST

from rest_framework_cache.registry import cache_registry

from caravaggio_rest_api.drf_haystack import serializers as dse_serializers
from caravaggio_rest_api import fields as dse_fields

from caravaggio_rest_api.example.company.models import Company, Address
from caravaggio_rest_api.example.company.search_indexes import CompanyIndex


class AddressSerializerV1(dse_serializers.UserTypeSerializer):
    street_type = serializers.CharField(required=False, max_length=10)
    street_name = serializers.CharField(required=False, max_length=150)
    street_number = serializers.IntegerField(required=False, )
    city = serializers.CharField(required=False, max_length=150)
    region = serializers.CharField(required=False, max_length=150)
    state = serializers.CharField(required=False, max_length=150)
    country_code = serializers.CharField(required=False, max_length=3)
    zipcode = serializers.CharField(required=False, max_length=10)

    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta(object):
        """Meta options."""

        __type__ = Address


class CompanySerializerV1(dse_serializers.CassandraModelSerializer,
                          BaseCachedSerializerMixin):
    """
    Represents a Business Object API View with support for JSON, list, and map
    fields.
    """

    user = serializers.HiddenField(
        default=dse_fields.CurrentUserNameDefault())

    created_at = serializers.DateTimeField(
        default=serializers.CreateOnlyDefault(datetime.utcnow))

    address = AddressSerializerV1()

    founders = fields.ListField(required=False, child=fields.UUIDField())
    specialties = fields.ListField(required=False, child=fields.CharField())
    latest_twitter_followers = fields.ListField(
        required=False, child=fields.IntegerField())

    websites = fields.DictField(required=False, child=fields.CharField())

    crawler_config = dse_fields.CassandraJSONFieldAsText(required=False)
    extra_data = dse_fields.CassandraJSONFieldAsText(required=False)

    class Meta:
        error_status_codes = {
            HTTP_400_BAD_REQUEST: "Bad Request"
        }

        model = Company
        fields = ("_id", "user", "created_at", "updated_at",
                  "name", "short_description", "foundation_date",
                  "country_code", "stock_symbol", "domain", "last_round",
                  "round_notes",
                  "address", "latitude", "longitude",
                  "contact_email", "founders", "specialties",
                  "latest_twitter_followers", "websites", "crawler_config",
                  "extra_data")
        read_only_fields = ("_id", "user", "created_at", "updated_at")


class CompanySearchSerializerV1(CustomHaystackSerializer,
                                BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    """
    address = AddressSerializerV1()

    founders = fields.ListField(required=False, child=fields.UUIDField())
    specialties = fields.ListField(required=False, child=fields.CharField())
    latest_twitter_followers = fields.ListField(
        required=False, child=fields.IntegerField())

    websites = fields.DictField(required=False, child=fields.CharField())

    crawler_config = dse_fields.CassandraJSONFieldAsText(required=False)
    extra_data = dse_fields.CassandraJSONFieldAsText(required=False)

    score = fields.FloatField(required=False)

    class Meta(CustomHaystackSerializer.Meta):
        model = Company
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [CompanyIndex]

        # The `fields` contains all the fields we want to include.
        # NOTE: Make sure you don't confuse these with model attributes. These
        # fields belong to the search index!
        fields = [
            "_id", "created_at", "updated_at",
            "name", "short_description", "foundation_date",
            "last_round", "round_notes",
            "country_code", "stock_symbol", "domain",
            "address_street_type", "address_street_name",
            "address_street_number", "address_state", "address_region",
            "address_city", "address_country_code", "address_zipcode",
            "latitude", "longitude",
            "contact_email", "founders", "specialties",
            "latest_twitter_followers", "websites", "crawler_config",
            "extra_data",
            "text", "score"
        ]


class CompanyGEOSearchSerializerV1(CustomHaystackSerializer,
                                   BaseCachedSerializerMixin):
    """
    A Fast Searcher (Solr) version of the original Business Object API View
    to do GEO Spatial searches
    """
    address = AddressSerializerV1()

    founders = fields.ListField(required=False, child=fields.UUIDField())
    specialties = fields.ListField(required=False, child=fields.CharField())
    latest_twitter_followers = fields.ListField(
        required=False, child=fields.IntegerField())

    websites = fields.DictField(required=False, child=fields.CharField())

    crawler_config = dse_fields.CassandraJSONFieldAsText(required=False)
    extra_data = dse_fields.CassandraJSONFieldAsText(required=False)

    score = fields.FloatField(required=False)

    distance = dse_fields.DistanceField(required=False, units="m")

    class Meta(CustomHaystackSerializer.Meta):
        model = Company
        # The `index_classes` attribute is a list of which search indexes
        # we want to include in the search.
        index_classes = [CompanyIndex]

        fields = [
            "_id", "created_at", "updated_at",
            "name", "short_description", "foundation_date",
            "last_round", "round_notes",
            "country_code", "stock_symbol", "domain",
            "address_street_type", "address_street_name",
            "address_street_number", "address_state", "address_region",
            "address_city", "address_country_code", "address_zipcode",
            "latitude", "longitude",
            "contact_email", "founders", "specialties",
            "latest_twitter_followers", "websites", "crawler_config",
            "extra_data",
            "text", "score", "distance"
        ]


class CompanyFacetSerializerV1(CustomHaystackFacetSerializer):

    # Setting this to True will serialize the
    # queryset into an `objects` list. This
    # is useful if you need to display the faceted
    # results. Defaults to False.
    serialize_objects = True

    class Meta:
        index_classes = [CompanyIndex]
        fields = ["foundation_date", "country_code", "stock_symbol",
                  "founders", "specialties", "last_round", "headcount"]

        # IMPORTANT
        # Faceting on Tuple fields is not supported
        # "address_street_type", "address_state", "address_region",
        # "address_city", "address_country_code", "address_zipcode"

        # Example of queries:
        # http://localhost:8001/companies/company/search/facets/?
        # headcount=start:0,end:5000,gap:20&facet.mincount=1
        #
        # http://localhost:8001/companies/company/search/facets/?
        # foundation_date=start_date:2010-01-01,end_date:2019-11-30,
        # gap_by:month,gap_amount:3&facet.mincount=1

        field_options = {
            # "headcount": {
            #     "start": 0,
            #     "end": 5000,
            #     "gap": 20
            # },
            # "foundation_date": {
            #     "start_date": datetime.now() - timedelta(days=50 * 365),
            #     "end_date": datetime.now(),
            #     "gap_by": "month",
            #     "gap_amount": 6
            # },
            # "last_round": {
            #     "start_date": datetime.now() - timedelta(days=10 * 365),
            #     "end_date": datetime.now(),
            #     "gap_by": "month",
            #     "gap_amount": 3
            # }
        }


# Cache configuration
cache_registry.register(CompanySerializerV1)
cache_registry.register(CompanySearchSerializerV1)
cache_registry.register(CompanyGEOSearchSerializerV1)
