# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

"""
Users URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2./topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers

from .views import UserViewSet, ClientViewSet, OrganizationViewSet

# API v1 Router. Provide an easy way of automatically determining the URL conf.

api_USERS = routers.DefaultRouter()

# Manage external systems
api_USERS.register(r"client", ClientViewSet, base_name="client")

# Manage organizations
api_USERS.register(r"organization", OrganizationViewSet, base_name="organization")

# Manage users organizations
api_USERS.register(r"user", UserViewSet, base_name="user")

urlpatterns = [
    # Users API version
    url(r"^", include(api_USERS.urls), name="users-api"),
]
