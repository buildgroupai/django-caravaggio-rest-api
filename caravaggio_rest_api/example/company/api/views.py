# -*- coding: utf-8 -*
from caravaggio_rest_api.drf_haystack.viewsets import \
    CaravaggioCassandraModelViewSet, \
    CaravaggioHaystackGEOSearchViewSet, \
    CaravaggioHaystackFacetSearchViewSet

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from caravaggio_rest_api.example.company.api.serializers import \
    CompanyFacetSerializerV1, CompanyGEOSearchSerializerV1
from caravaggio_rest_api.example.company.models import Company
from caravaggio_rest_api.example.company.api.serializers import \
    CompanySerializerV1, CompanySearchSerializerV1


class CompanyViewSet(CaravaggioCassandraModelViewSet):
    queryset = Company.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = CompanySerializerV1


class CompanySearchViewSet(CaravaggioHaystackFacetSearchViewSet):

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [Company]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = CompanySearchSerializerV1

    facet_serializer_class = CompanyFacetSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = CompanySerializerV1

    ordering_fields = ("_id",
                       "created_at", "updated_at", "foundation_date",
                       "country_code", "stock_symbol")


class CompanyGEOSearchViewSet(CaravaggioHaystackGEOSearchViewSet):

    # `index_models` is an optional list of which models you would like
    #  to include in the search result. You might have several models
    #  indexed, and this provides a way to filter out those of no interest
    #  for this particular view.
    # (Translates to `SearchQuerySet().models(*index_models)`
    # behind the scenes.
    index_models = [Company]

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #   TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = CompanyGEOSearchSerializerV1

    # The Search viewsets needs information about the serializer to be use
    # with the results. The previous serializer is used to parse
    # the search requests adding fields like text, autocomplete, score, etc.
    results_serializer_class = CompanySerializerV1

    ordering_fields = ("_id",
                       "created_at", "updated_at", "foundation_date",
                       "country_code", "stock_symbol")
