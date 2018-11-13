# -*- coding: utf-8 -*
# Copyright (c) 2018-2019 PreSeries Tech, SL
# All rights reserved.

from __future__ import unicode_literals

from rest_framework.authtoken.admin import TokenAdmin


TokenAdmin.raw_id_fields = ('user',)
