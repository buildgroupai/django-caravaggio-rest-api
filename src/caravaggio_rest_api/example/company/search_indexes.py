# -*- coding: utf-8 -*
from django.utils import timezone

from haystack import indexes

from caravaggio_rest_api.haystack.indexes import BaseSearchIndex

from .models import Company


class CompanyIndex(BaseSearchIndex, indexes.Indexable):

    _id = indexes.CharField(model_attr="_id")

    user = indexes.CharField(model_attr="user")

    created_at = indexes.DateTimeField(model_attr="created_at")
    updated_at = indexes.DateTimeField(model_attr="updated_at")

    is_deleted = indexes.BooleanField(model_attr="is_deleted")

    name = indexes.CharField(model_attr="name")
    short_description = indexes.CharField(model_attr="short_description")

    round_notes = indexes.CharField(model_attr="round_notes")

    domain = indexes.CharField(model_attr="domain", faceted=True)

    foundation_date = indexes.DateField(model_attr="foundation_date", faceted=True)

    last_round = indexes.DateField(model_attr="last_round", faceted=True)

    country_code = indexes.CharField(model_attr="country_code", faceted=True)

    stock_symbol = indexes.CharField(model_attr="stock_symbol", faceted=True)

    contact_email = indexes.CharField(model_attr="stock_symbol")

    headcount = indexes.IntegerField(model_attr="headcount", faceted=True)

    company_score = indexes.FloatField(model_attr="company_score", faceted=True)

    # Address UDT fields
    address_street_type = indexes.CharField(model_attr="address.street_type", faceted=True)
    address_street_name = indexes.CharField(model_attr="address.street_name")
    address_street_number = indexes.IntegerField(model_attr="address.street_number")
    address_state = indexes.CharField(model_attr="address.state", faceted=True)
    address_region = indexes.CharField(model_attr="address.region", faceted=True)
    address_city = indexes.CharField(model_attr="address.city", faceted=True)
    address_country_code = indexes.CharField(model_attr="address.country_code", faceted=True)
    address_zipcode = indexes.CharField(model_attr="address.zipcode", faceted=True)

    coordinates = indexes.LocationField(model_attr="coordinates")

    founders = indexes.MultiValueField(null=True, model_attr="founders", faceted=True)
    specialties = indexes.MultiValueField(null=True, model_attr="specialties", faceted=True)
    latest_twitter_followers = indexes.MultiValueField(null=True, model_attr="latest_twitter_followers")
    websites = indexes.MultiValueField(null=True, model_attr="websites")

    crawler_config = indexes.CharField(model_attr="crawler_config")
    extra_data = indexes.CharField(model_attr="extra_data")

    class Meta:

        text_fields = ["short_description", "extra_data", "round_notes"]

        # Once the index has been created it cannot be changed
        # with sync_indexes. Changes should be made by hand.
        index_settings = {"realtime": "true", "autoCommitTime": "100", "ramBufferSize": "2048"}

    def get_model(self):
        return Company

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(created_at__lte=timezone.now(), is_deleted=False)

    @staticmethod
    def prepare_autocomplete(obj):
        return " ".join((obj.name, obj.address_city, obj.address_zipcode))
