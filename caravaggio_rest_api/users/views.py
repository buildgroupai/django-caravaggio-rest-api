# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

from django.contrib.auth.models import User
from rest_framework.permissions import IsAdminUser

# from rest_framework.authentication import \
#    TokenAuthentication, SessionAuthentication
# from rest_framework.permissions import IsAuthenticated

from caravaggio_rest_api.drf_haystack.viewsets import CustomModelViewSet

from .serializers import UserSerializerV1


# ViewSets define the view behavior.
class UserViewSet(CustomModelViewSet):
    queryset = User.objects.all()

    # authentication_classes = (
    #    TokenAuthentication, SessionAuthentication)

    permission_classes = (IsAdminUser,)

    serializer_class = UserSerializerV1
