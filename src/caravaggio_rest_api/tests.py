# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import json
import csv
import logging

from collections import OrderedDict
from decimal import Decimal

from caravaggio_rest_api.drf_haystack.serializers import deserialize_instance
from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.test import TestCase, modify_settings


# from django_cassandra_engine.test import TestCase
from spitslurp import slurp

from caravaggio_rest_api.users.models import CaravaggioClient, CaravaggioOrganization

TEST_AVOID_INDEX_SYNC = "CARAVAGGIO_AVOID_INDEX_SYNC"

FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT)


def _to_plain_dict(dictionary, parent=None):

    plain_dict = {}
    for key, value in dictionary.items():
        abs_key = key if not parent else "{0}|{1}".format(parent, key)
        if isinstance(value, (dict, OrderedDict)):
            plain_dict.update(_to_plain_dict(value, abs_key))
        else:
            plain_dict[abs_key] = value

    return plain_dict


class CaravaggioBaseTest(TestCase):
    """ Test module for all Caravaggio tests """

    databases = "__all__"

    api_client = APIClient()

    client = None
    super_user = None
    client_admin = None
    user = None
    organization = None

    @classmethod
    def force_authenticate(cls, user):
        token = Token.objects.get(user__username=user.username)
        cls.api_client.force_authenticate(user, token)
        cls.api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        if "client" not in globals():
            cls.client = cls.create_client(email="tests@buildgroupai.com", name="BuildGroup Data Services Inc.")

        if "user" not in globals():
            cls.super_user = cls.create_user(
                email="superuser@buildgroupai.ai",
                first_name="Superuser",
                last_name="BGDS IT",
                is_superuser=True,
                is_staff=True,
                is_client_staff=True,
            )

            cls.client_admin = cls.create_user(
                email="admin@buildgroupai.ai",
                first_name="Admin",
                last_name="BGDS App",
                is_superuser=False,
                is_staff=False,
                is_client_staff=True,
                client=cls.client,
            )

            cls.user = cls.create_user(
                email="user@buildgroupai.ai",
                first_name="User",
                last_name="BuildGroup LLC",
                is_superuser=False,
                is_staff=False,
                is_client_staff=False,
                client=cls.client,
            )

            cls.force_authenticate(cls.user)

        if "organization" not in globals():
            cls.organization = cls.create_organization(
                email="tests@buildgroupai.com",
                name="BuildGroup Data Services Inc.",
                is_active=True,
                client=cls.client,
                owner=cls.user
            )

    @classmethod
    def load_test_data(
        cls,
        file,
        serializer_class=None,
        username=None,
        type="JSON",
        return_pure_json=True,
        request=None,
        replace=None,
        serializer_action=None,
        context=None,
    ):

        logging.info("Loading data from file {}".format(file))

        if not username:
            username = cls.user.username

        if not request:
            request = RequestFactory().get("./fake_path")

        if not hasattr(request, "user") or not request.user:
            request.user = get_user_model().objects.get(username=username)

        if not context:
            context = {"request": request}

        if not hasattr(context, "request"):
            context["request"] = request

        if type == "JSON":
            file_content = slurp(file)
            if replace:
                for term, value in replace.items():
                    file_content = file_content.replace(f"@@{term}@@", value)
            data = json.loads(file_content)

            if serializer_class:
                logging.info("Validating data using serializer {}".format(serializer_class))
                has_errors = False
                errors_by_resource = {}
                object_json = []
                for index, resource in enumerate(data):
                    serializer = serializer_class(data=resource, context=context)
                    if not serializer.is_valid():
                        has_errors = True
                        errors_by_resource["{}".format(index)] = serializer.errors

                    elif not return_pure_json:
                        if not serializer_action:
                            instance = deserialize_instance(serializer, serializer.Meta.model)
                            object_json.append(instance)
                        else:
                            object_json.append(getattr(serializer, serializer_action)(serializer.validated_data))

                if has_errors:
                    raise AssertionError("There are some errors in the json data of the test", errors_by_resource)
                elif not return_pure_json:
                    return object_json

            if return_pure_json:
                return data
        elif type == "CSV":
            data = []
            with open(file, "r") as f:
                reader = csv.DictReader(f)
                for master_value in reader:
                    data.append(master_value)
            return data
        else:
            raise AssertionError(
                "Invalid file type '{0}'. Valid types are: [{1}]".format(type, ", ".join(["JSON", "CSV"]))
            )

    @classmethod
    def create_client(cls, email, name):
        default_client = {"email": email, "name": name}
        return CaravaggioClient.objects.create(**default_client)

    @classmethod
    def create_user(
        cls,
        email,
        first_name=None,
        last_name=None,
        client=None,
        is_superuser=False,
        is_staff=False,
        is_client_staff=False,
    ):

        client = client if client else cls.client

        user_data = {
            "username": "{}-{}".format(client.id, email),
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_superuser": is_superuser,
            "is_staff": is_superuser,
            "is_client_staff": is_client_staff,
            "client": client,
        }
        return get_user_model().objects.create(**user_data)

    @classmethod
    def create_organization(cls, email, name, is_active, client, owner):

        client = client if client else cls.client
        owner = owner if owner else cls.user

        organization_data = {"email": email, "name": name, "client": client, "is_active": is_active, "owner": owner}
        return CaravaggioOrganization.objects.create(**organization_data)

    def _steps(self):
        for name in dir(self):  # dir() result is implicitly sorted
            if name.startswith("step"):
                yield name, getattr(self, name)

    def assert_equal_dicts(self, dict1, dict2, exclude_keys=None):
        dict1 = _to_plain_dict(dict1)
        dict2 = _to_plain_dict(dict2)
        d1_keys = set([key for key in dict1.keys() if dict1[key]])
        d2_keys = set([key for key in dict2.keys() if dict2[key]])
        d1_keys = d1_keys.difference(set(exclude_keys))
        d2_keys = d2_keys.difference(set(exclude_keys))
        intersect_keys = d1_keys.intersection(d2_keys)
        added = d1_keys - d2_keys
        removed = d2_keys - d1_keys
        modified = {}
        for o in intersect_keys:
            val1 = dict1[o]
            val2 = dict2[o]

            if isinstance(val1, (float,)) or isinstance(val2, (float,)):
                dec1 = Decimal(val1)
                dec2 = Decimal(val2)

                dec1_exp = abs(dec1.as_tuple().exponent)
                dec2_exp = abs(dec2.as_tuple().exponent)

                val1 = round(dec1, min(dec1_exp, dec2_exp, 5))
                val2 = round(dec2, min(dec1_exp, dec2_exp, 5))

            if val1 != val2:
                modified[o] = (val1, val2)

        same = set(o for o in intersect_keys if dict1[o] == dict2[o])

        self.assertEqual(len(added), 0, "Keys were added! {}".format(added))
        self.assertEqual(len(removed), 0, "Keys were removed! {}".format(removed))
        self.assertEqual(len(modified), 0, "Values are not identical! {}".format(modified))

    @modify_settings(
        MIDDLEWARE={"append": "caravaggio_rest_api.drf.middleware.OrganizationMiddleware",}
    )
    def test_steps(self):
        for name, step in self._steps():
            try:
                logging.info("Starting step: {}".format(step))
                step()
                logging.info("Successfully ended step: {}".format(step))
            except Exception as e:
                self.fail("{} failed ({}: {})".format(step, type(e), e))
