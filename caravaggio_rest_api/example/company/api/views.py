# -*- coding: utf-8 -*
from drf_haystack.filters import HaystackFilter, HaystackBoostFilter, \
    HaystackGEOSpatialFilter, HaystackFacetFilter


from caravaggio_rest_api.drf_haystack.filters import \
    HaystackOrderingFilter

from caravaggio_rest_api.drf_haystack.viewsets import \
    CustomModelViewSet, CustomHaystackViewSet

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from drf_haystack import mixins

from caravaggio_rest_api.example.company.api.serializers import \
    CompanyFacetSerializerV1, CompanyGEOSearchSerializerV1
from caravaggio_rest_api.example.company.models import Company
from .serializers import CompanySerializerV1, CompanySearchSerializerV1


class CompanyViewSet(CustomModelViewSet):
    queryset = Company.objects.all()

    # Defined in the settings as default authentication classes
    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    # Defined in the settings as default permission classes
    # permission_classes = (IsAuthenticated,)

    serializer_class = CompanySerializerV1

    filter_fields = ("_id", "created_at", "updated_at", "foundation_date",
                     "country_code", "stock_symbol")


class CompanySearchViewSet(mixins.FacetMixin, CustomHaystackViewSet):

    filter_backends = [
        HaystackFilter, HaystackBoostFilter,
        HaystackFacetFilter, HaystackOrderingFilter]

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

    document_uid_field = "id"

    ordering_fields = ("_id", "created_at", "updated_at", "foundation_date",
                       "country_code", "stock_symbol")


class CompanyGEOSearchViewSet(CustomHaystackViewSet):

    filter_backends = [
        HaystackFilter, HaystackBoostFilter,
        HaystackGEOSpatialFilter, HaystackOrderingFilter]

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

    document_uid_field = "id"

    ordering_fields = ("_id", "created_at", "updated_at", "foundation_date",
                       "country_code", "stock_symbol")
