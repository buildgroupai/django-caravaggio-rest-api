# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from django.contrib.auth.models import User
from rest_framework import serializers


# Serializers define the API representation.
class UserSerializerV1(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ("url", "username", "email", "is_staff")
