# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.
from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions


class ClientAdminPermission(permissions.BasePermission):
    """
    Global permission check for blacklisted IPs.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        permission = bool((request.user and request.user.is_staff) or
                    (request.user and request.user.is_client_staff))

        return permission


class OrganizationAdminPermission(permissions.BasePermission):
    """
    Permission check for users that are owners of an organization
    or are part of the administrators list of an organization
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        permission = bool((request.user and request.user.is_staff) or
                          (request.user and request.user.is_client_staff) or
                          (request.user.owner_of.count()) or
                          (request.user.administrator_of.count()))

        return permission


class OrganizationUserAdminPermission(OrganizationAdminPermission):

    def has_object_permission(self, request, view, user):

        # Super user
        if request.user and request.user.is_staff:
            return True

        # The user are from different client (external system)
        if request.user.client.id != user.client.id:
            return False

        # Super user of the same organization
        if request.user and request.user.is_client_staff:
            return True

        # Let's see if the authenticated user is administrator of any of the
        # organizations the user object is a member of.
        admin_of = request.user.owner_of.all().union(
            request.user.administrator_of.all()).distinct()

        user_organizations = user.member_of.all().union(
            user.restricted_member_of.all()).union(
            user.administrator_of.all()).union(
            user.owner_of.all()).distinct()

        return bool(len(set(admin_of).intersection(user_organizations)))
