# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

from caravaggio_rest_api.users.models import \
    CaravaggioClient, CaravaggioUserManager, CaravaggioOrganization, \
    CaravaggioUser


class DynamicFieldsSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', set())
        super().__init__(*args, **kwargs)

        if fields and '__all__' not in fields:
            all_fields = set(self.fields.keys())
            for not_requested in all_fields - set(fields):
                self.fields.pop(not_requested)


class CaravaggioClientSerializerV1(DynamicFieldsSerializer):
    """
    CaravaggioClientSerializerV1 defines the API representation of the
     CaravaggioClient.
    """

    class Meta:
        model = CaravaggioClient
        fields = ('id', 'email', 'name',
                  'is_active', 'date_joined', 'date_deactivated')
        read_only_fields = ('id', 'date_joined', 'date_deactivated')


class CaravaggioOrganizationSerializerV1(DynamicFieldsSerializer):
    """
    CaravaggioClientSerializerV1 defines the API representation of the
     CaravaggioClient.
    """

    client = PrimaryKeyRelatedField(
        queryset=CaravaggioClient.objects.all(),
        required=True)

    owner = PrimaryKeyRelatedField(
        queryset=CaravaggioUser.objects.all(),
        required=True)

    administrators = PrimaryKeyRelatedField(
        queryset=CaravaggioUser.objects.all(),
        many=True, required=False)

    members = PrimaryKeyRelatedField(
        queryset=CaravaggioUser.objects.all(),
        many=True, required=False)

    restricted_members = PrimaryKeyRelatedField(
        queryset=CaravaggioUser.objects.all(),
        many=True, required=False)

    class Meta:
        model = CaravaggioOrganization
        fields = ('id', 'client',
                  'email', 'name',
                  'owner', 'administrators', 'members', 'restricted_members',
                  'number_of_total_members', 'number_of_members',
                  'number_of_administrators', 'number_of_restricted_members',
                  'all_members',
                  'created', 'updated')
        read_only_fields = ('id', 'client', 'created', 'updated',
                            'members', 'restricted_members',
                            'administrators', 'members', 'restricted_members',
                            'number_of_total_members', 'number_of_members',
                            'number_of_administrators',
                            'number_of_restricted_members')


class CaravaggioUserSerializerV1(DynamicFieldsSerializer):
    """
    CaravaggioUserSerializerV1 defines the API representation of the
     CaravaggioUser.
    """

    client = PrimaryKeyRelatedField(queryset=CaravaggioClient.objects.all(),
                                    required=True)

    email = serializers.CharField(
        write_only=False,
        required=True,
        help_text='Leave empty if no change needed',
        style={'input_type': 'email', 'placeholder': 'E-mail'}
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        help_text='Leave empty if no change needed',
        style={'input_type': 'password', 'placeholder': 'Password'}
    )

    class Meta:
        model = CaravaggioUser
        manager = CaravaggioUserManager

        fields = ('id', 'client', 'email', 'password', 'first_name',
                  'last_name', 'is_staff', 'is_client_staff',
                  'date_joined')
        read_only_fields = ('id', 'client', 'email', 'is_staff', 'date_joined')

    def create(self, validated_data):
        validated_data['password'] = make_password(
            validated_data.get('password'))
        return super(CaravaggioUserSerializerV1, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('password', None):
            validated_data['password'] = make_password(
                validated_data.get('password'))

        return super(CaravaggioUserSerializerV1, self).update(
            instance, validated_data)

    def validate_client(self, value):
        """
        Make sure the user being created/updated belongs to the same Client
        as the current user that is executing the operation.
        And the current user should be also an admin of the client
        (this is controlled by the ViewSet/permissions field)
        :param value: the client instance being assigned to the object
        :return: the client instance if is the same as the one associated
            with the current logged user
        """
        request = self.context.get("request")

        if request.user.client.id != value.id:
            raise serializers.ValidationError(
                "You can only create users in your own Client space.")

        return value


class UserTokenSerializer(serializers.Serializer):
    client_id = serializers.CharField(label=_("Client id"))
    email = serializers.CharField(label=_("Email"))

    def validate(self, attrs):
        client_id = attrs.get('client_id')
        email = attrs.get('email')

        if client_id and email:
            user = CaravaggioUser.objects.get(username="{}-{}".
                                              format(client_id, email))

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to get the user with '
                        'provided client id and email.')
                raise serializers.ValidationError(msg, code='badrequest')
        else:
            msg = _('Must include the "client id" and "email".')
            raise serializers.ValidationError(msg, code='badrequest')

        attrs['user'] = user
        return attrs
