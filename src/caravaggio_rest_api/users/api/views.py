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
from rest_framework import status

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas import ManualSchema

from caravaggio_rest_api.users.api.permissions import \
    OrganizationUserAdminPermission

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from caravaggio_rest_api.drf.viewsets import CaravaggioDjangoModelViewSet

from caravaggio_rest_api.users.models import \
    CaravaggioUser, CaravaggioClient, CaravaggioOrganization
from caravaggio_rest_api.users.api.serializers import \
    CaravaggioUserSerializerV1, CaravaggioClientSerializerV1, \
    CaravaggioOrganizationSerializerV1, UserTokenSerializer
from caravaggio_rest_api.users.api.permissions import \
    ClientAdminPermission, OrganizationAdminPermission

LOGGER = logging.getLogger(__name__)


# ViewSets define the view behavior.
class ClientViewSet(CaravaggioDjangoModelViewSet):
    queryset = CaravaggioClient.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (IsAdminUser,)

    serializer_class = CaravaggioClientSerializerV1

    filterset_fields = {
        'id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL,
        'email': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'date_joined': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL,
        'date_deactivated': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL
    }


# ViewSets define the view behavior of an Organization.
class OrganizationViewSet(CaravaggioDjangoModelViewSet):
    queryset = CaravaggioOrganization.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (OrganizationAdminPermission,)

    serializer_class = CaravaggioOrganizationSerializerV1

    filterset_fields = {
        'id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL,
        'email': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,

        'owner': CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,
        'owner__id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL,
        'owner__first_name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'owner__last_name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'owner__is_staff': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'owner__is_client_staff':
            CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,

        'number_of_total_members':
            CaravaggioDjangoModelViewSet.NUMERIC_OPERATORS_ALL,
        'number_of_administrators':
            CaravaggioDjangoModelViewSet.NUMERIC_OPERATORS_ALL,
        'number_of_members':
            CaravaggioDjangoModelViewSet.NUMERIC_OPERATORS_ALL,
        'number_of_restricted_members':
            CaravaggioDjangoModelViewSet.NUMERIC_OPERATORS_ALL,

        'is_active': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'created': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL,
        'updated': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL,
        'date_deactivated': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL,

        # 'all_members':
        #   CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,
        # 'members__user':
        #   CaravaggioDjangoModelViewSet.MULTIPLE_RELATIONSHIP_OPERATORS_ALL,
        # 'administrators':
        #    CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,
        # 'restricted_members':
        #    CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,

        'client': CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,
        'client__name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'client__id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        super().add_throttle(
            "add_administrator", settings.POST_THROTTLE_RATE)
        super().add_throttle(
            "remove_administrator", settings.DELETE_THROTTLE_RATE)
        super().add_throttle(
            "add_member", settings.POST_THROTTLE_RATE)
        super().add_throttle(
            "remove_member", settings.DELETE_THROTTLE_RATE)
        super().add_throttle(
            "add_restricted_member", settings.POST_THROTTLE_RATE)
        super().add_throttle(
            "remove_restricted_member", settings.DELETE_THROTTLE_RATE)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.all_members.count() > 1:
            return Response(
                data={'message': "The organization still has members"},
                status=status.HTTP_400_BAD_REQUEST)
        # elif obj.organizations.count() == 1:
        #     return Response(
        #         data={'message': "The owner of the organization doesn't "
        #                          "below to other organization, move it "
        #                          "first."},
        #         status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(obj)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _process_add_user(self, collection, users):
        if isinstance(users, (str,)):
            users = [users]

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

    @action(methods=['post'], detail=True)
    def remove_administrator(self, request, pk):
        return self._process_remove_user(
            "administrators", request.data['users'])

    @action(methods=['post'], detail=True)
    def add_administrator(self, request, pk):
        return self._process_add_user(
            "administrators", request.data['users'])

    @action(methods=['post'], detail=True)
    def remove_member(self, request, pk):
        return self._process_remove_user(
            "members", request.data['users'])

    @action(methods=['post'], detail=True)
    def add_member(self, request, pk):
        return self._process_add_user(
            "members", request.data['users'])

    @action(methods=['post'], detail=True)
    def remove_restricted_member(self, request, pk):
        return self._process_remove_user(
            "restricted_members", request.data['users'])

    @action(methods=['post'], detail=True)
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
                self.request.user.administrator_of.all())


# ViewSets define the view behavior.
class UserViewSet(CaravaggioDjangoModelViewSet):
    queryset = CaravaggioUser.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (OrganizationAdminPermission,)

    serializer_class = CaravaggioUserSerializerV1

    filterset_fields = {
        'id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL,
        'email': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'first_name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'last_name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'date_joined': CaravaggioDjangoModelViewSet.DATE_OPERATORS_ALL,
        'is_active': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'is_superuser': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'is_staff': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'is_client_staff': CaravaggioDjangoModelViewSet.BOOL_OPERATORS_ALL,
        'client': CaravaggioDjangoModelViewSet.RELATIONSHIP_OPERATORS_ALL,
        'client__name': CaravaggioDjangoModelViewSet.STRING_OPERATORS_ALL,
        'client__id': CaravaggioDjangoModelViewSet.PK_OPERATORS_ALL
    }

    # Example of query
    # http://localhost:8001/users/user/?
    #   first_name__regex=.*.vi*.
    #   &client__name__icontains=buil
    #   &date_joined__year=2019
    #   &client=62df90ca-ca50-4bb8-aab7-a2159409cf67
    #   &is_active=true

    def get_queryset(self):
        if self.request.user.is_staff:
            return CaravaggioUser.objects.all()
        elif self.request.user.is_client_staff:
            return CaravaggioUser.objects.filter(
                client=self.request.user.client.id)
        else:
            # Get the organizations from which the user is owner or admin
            user_organizations = CaravaggioOrganization.objects.filter(
                id__in=self.request.user.owner_of.union(
                    self.request.user.administrator_of.all()).values(
                    'id').all())
            return CaravaggioUser.objects.filter(
                client=self.request.user.client.id,
                id__in=user_organizations.values("all_members"))


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={'request': request})
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
