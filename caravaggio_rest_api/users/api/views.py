# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
import logging
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser

from django.conf import settings

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas import ManualSchema

from caravaggio_rest_api.users.api.permissions import \
    OrganizationUserAdminPermission

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from caravaggio_rest_api.drf_haystack.viewsets import CustomModelViewSet

from caravaggio_rest_api.users.models import \
    CaravaggioUser, CaravaggioClient, CaravaggioOrganization
from caravaggio_rest_api.users.api.serializers import \
    CaravaggioUserSerializerV1, CaravaggioClientSerializerV1, \
    CaravaggioOrganizationSerializerV1, UserTokenSerializer
from caravaggio_rest_api.users.api.permissions import \
    ClientAdminPermission, OrganizationAdminPermission

LOGGER = logging.getLogger(__name__)


class DynamicFieldsViewSet(CustomModelViewSet):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_query_fields(self):
        custom_query_fields = set()
        raw_fields = self.request.query_params.getlist('fields')

        for item in raw_fields:
            custom_query_fields.update(item.split(','))

        return custom_query_fields

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(
            *args, fields=self.get_query_fields(), **kwargs)


# ViewSets define the view behavior.
class ClientViewSet(DynamicFieldsViewSet):
    queryset = CaravaggioClient.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (IsAdminUser,)

    serializer_class = CaravaggioClientSerializerV1


# ViewSets define the view behavior of an Organization.
class OrganizationViewSet(DynamicFieldsViewSet):
    queryset = CaravaggioOrganization.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (OrganizationAdminPermission,)

    serializer_class = CaravaggioOrganizationSerializerV1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        super().add_throttle("add_member", settings.POST_THROTTLE_RATE)
        super().add_throttle("remove_member", settings.DELETE_THROTTLE_RATE)

    def _process_add_user(self, collection, users):
        organization = self.get_object()
        getattr(organization, collection).add(*CaravaggioUser.objects.filter(
            email__in=users,
            client=organization.client).all())
        organization.save()
        serializer = self.get_serializer(organization)
        return Response(serializer.data)

    def _process_remove_user(self, collection, users):
        organization = self.get_object()
        getattr(organization, collection).remove(
            *CaravaggioUser.objects.filter(
                email__in=users,
                client=organization.client).all())
        organization.save()
        serializer = self.get_serializer(organization)
        return Response(serializer.data)

    @action(methods=['delete'], detail=True)
    def remove_administrator(self, request, pk):
        return self._process_remove_user(
            "administrators", request.data['users'])

    @action(methods=['get', 'post', 'put', 'patch'], detail=True)
    def add_administrator(self, request, pk):
        return self._process_add_user(
            "administrators", request.data['users'])

    @action(methods=['delete'], detail=True)
    def remove_member(self, request, pk):
        return self._process_remove_user(
            "members", request.data['users'])

    @action(methods=['get', 'post', 'put', 'patch'], detail=True)
    def add_member(self, request, pk):
        return self._process_add_user(
            "members", request.data['users'])

    @action(methods=['delete'], detail=True)
    def remove_restricted_member(self, request, pk):
        return self._process_remove_user(
            "restricted_members", request.data['users'])

    @action(methods=['get', 'post', 'put', 'patch'], detail=True)
    def add_restricted_member(self, request, pk):
        return self._process_add_user(
            "restricted_members", request.data['users'])

    def get_queryset(self):
        if self.request.user.is_staff:
            return CaravaggioOrganization.objects.all()
        elif self.request.user.is_client_staff:
           return CaravaggioOrganization.objects.filter(
               client=self.request.user.client.id)
        else:
            return self.request.user.owner_of.union(
                self.request.user.administrator_of)


# ViewSets define the view behavior.
class UserViewSet(DynamicFieldsViewSet):
    queryset = CaravaggioUser.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (ClientAdminPermission,)

    serializer_class = CaravaggioUserSerializerV1

    def get_queryset(self):
        if self.request.user.is_client_staff:
           return CaravaggioUser.objects.filter(
               client=self.request.user.client.id)

        return CaravaggioUser.objects.all()


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'id': user.id,
            'client_id': user.client.id,
            'client_name': user.client.name,
            'email': user.email
        })


class AdminAuthToken(ObtainAuthToken):
    permission_classes = (OrganizationUserAdminPermission,)
    serializer_class = UserTokenSerializer
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="client_id",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Client Id",
                        description="Valid client id",
                    ),
                ),
                coreapi.Field(
                    name="email",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Email",
                        description="Valid email",
                    ),
                ),
            ],
            encoding="application/json",
        )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        self.check_object_permissions(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'id': user.id,
            'client_id': user.client.id,
            'client_name': user.client.name,
            'email': user.email
        })
