# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from caravaggio_rest_api.users.models import CaravaggioOrganization, CaravaggioClient, CaravaggioUser
from caravaggio_rest_api.users.forms import CaravaggioUserCreationForm, CaravaggioUserChangeForm
from django.utils.translation import gettext_lazy as _


class CaravaggioClientAdmin(admin.ModelAdmin):
    model = CaravaggioClient
    fieldsets = (
        (None, {"fields": ("id", "email")}),
        (_("Client info"), {"fields": ("name",)}),
        (_("Permissions"), {"fields": ("is_active",),}),
        (_("Important dates"), {"fields": ("date_joined", "date_deactivated")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("id", "email"),}),)

    list_display = ("id", "email", "name", "is_active")
    search_fields = ("id", "email", "name", "is_active")
    ordering = ("id", "email", "name")


class CaravaggioOrganizationAdmin(admin.ModelAdmin):
    model = CaravaggioOrganization
    fieldsets = (
        (None, {"fields": ("id", "email")}),
        (_("Organization info"), {"fields": ("name",)}),
        (_("Users"), {"fields": ("owner", "administrators", "members", "restricted_members"),}),
        (_("Permissions"), {"fields": ("is_active",),}),
        (_("Important dates"), {"fields": ("created", "updated")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("id", "email"),}),)

    list_display = ("id", "email", "name", "owner", "is_active")
    search_fields = ("id", "email", "name", "owner", "is_active", "created", "updated")
    ordering = ("id", "email", "name", "created", "updated")


class CaravaggioUserAdmin(UserAdmin):
    add_form = CaravaggioUserCreationForm
    form = CaravaggioUserChangeForm
    model = CaravaggioUser

    # (_('Organizations'), {
    #     'fields': ('owner_of', 'administrator_of', 'member_of',
    #                'restricted_member_of'),
    # }),

    fieldsets = (
        (None, {"fields": ("client", "email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("client", "email", "password1", "password2"),}),)

    list_display = ("client", "email", "first_name", "last_name", "is_staff")
    search_fields = ("client__id", "email", "first_name", "last_name")
    ordering = (
        "client__id",
        "email",
    )


admin.site.register(CaravaggioUser, CaravaggioUserAdmin)
admin.site.register(CaravaggioClient, CaravaggioClientAdmin)
admin.site.register(CaravaggioOrganization, CaravaggioOrganizationAdmin)
