# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services, Inc.
# All rights reserved.
# This software is proprietary and confidential and may not under
# any circumstances be used, copied, or distributed.

from rest_auth.registration.views import RegisterView

from .models import CaravaggioUser


class CustomRegisterView(RegisterView):

    queryset = CaravaggioUser.objects.all()
