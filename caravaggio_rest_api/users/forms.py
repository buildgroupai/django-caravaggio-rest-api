# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CaravaggioUser


class CaravaggioUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = CaravaggioUser
        fields = ('client', 'email')


class CaravaggioUserChangeForm(UserChangeForm):

    class Meta:
        model = CaravaggioUser
        fields = UserChangeForm.Meta.fields
