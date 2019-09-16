# -*- coding: utf-8 -*
# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
import json
import csv
import logging

from collections import OrderedDict

from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from django.test import TestCase
# from django_cassandra_engine.test import TestCase
from spitslurp import slurp

from caravaggio_rest_api.users.models import CaravaggioClient

TEST_AVOID_INDEX_SYNC = "CARAVAGGIO_AVOID_INDEX_SYNC"

FORMAT = '%(asctime)-15s %(message)s'
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

    databases = '__all__'

    api_client = APIClient()

    @classmethod
    def force_authenticate(cls, user):
        token = Token.objects.get(user__username=user.username)
        cls.api_client.force_authenticate(user, token)
        cls.api_client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.client = cls.create_client(
            email="tests@buildgroupai.com",
            name="BuildGroup Data Services Inc."
        )

        cls.user = cls.create_user(
            email="testuser@buildgroupai.ai",
            first_name="Monica",
            last_name="Bellucci",
            is_superuser=False,
            is_client_staff=True,
            client=cls.client
        )

        cls.force_authenticate(cls.user)

    @classmethod
    def load_test_data(cls, file, serializer_class=None,
                       username=None, type="JSON"):

        logging.info("Loading data from file {}".format(file))

        if not username:
            username = cls.user.username

        request = RequestFactory().get('./fake_path')
        request.user = get_user_model().objects.get(username=username)

        if type == "JSON":
            data = json.loads(slurp(file))

            if serializer_class:
                logging.info("Validating data using serializer {}".
                             format(serializer_class))
                has_errors = False
                errors_by_resource = {}
                for index, resource in enumerate(data):
                    serializer = serializer_class(
                        data=resource, context={'request': request})
                    if not serializer.is_valid():
                        has_errors = True
                        errors_by_resource["{}".format(index)] = \
                            serializer.errors

                if has_errors:
                    raise AssertionError(
                        "There are some errors in the json data of the test",
                        errors_by_resource)

            return data
        elif type == "CSV":
            data = []
            with open(file, 'r') as f:
                reader = csv.DictReader(f)
                for master_value in reader:
                    data.append(master_value)
            return data
        else:
            raise AssertionError(
                "Invalid file type '{0}'. Valid types are: [{1}]".
                format(type, ", ".join(["JSON", "CSV"])))

    @classmethod
    def create_client(cls, email, name):
        default_client = {
            "email": email,
            "name": name
        }
        return CaravaggioClient.objects.create(**default_client)

    @classmethod
    def create_user(cls, email,
                    first_name=None, last_name=None, client=None,
                    is_superuser=False, is_client_staff=False):

        client = client if client else cls.client

        user_data = {
            "username": "{}-{}".format(client.id, email),
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_superuser": is_superuser,
            "is_client_staff": is_client_staff,
            "client": client
        }
        return get_user_model().objects.create(**user_data)


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
        modified = {o: (dict1[o], dict2[o])
                    for o in intersect_keys if dict1[o] != dict2[o]}
        same = set(o for o in intersect_keys if dict1[o] == dict2[o])

        self.assertEqual(len(added), 0, "Keys were added! {}".format(added))
        self.assertEqual(len(removed), 0, "Keys were removed! {}".
                         format(removed))
        self.assertEqual(len(modified), 0, "Values are not identical! {}".
                         format(modified))
