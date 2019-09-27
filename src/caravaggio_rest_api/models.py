# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
from __future__ import unicode_literals
import logging

from django.conf import settings
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

from django.dispatch import receiver


LOGGER = logging.getLogger(__name__)


# Create a token for every user we create
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
