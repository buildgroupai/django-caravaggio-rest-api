# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.

from __future__ import unicode_literals

from rest_framework.authtoken.admin import TokenAdmin


TokenAdmin.raw_id_fields = ('user',)
