# -*- coding: utf-8 -*-
import os
import json
import logging
import time
import math

from datetime import datetime, timedelta
from dateutil import relativedelta

from caravaggio_rest_api.utils import delete_all_records
from caravaggio_rest_api.users.models import CaravaggioClient, CaravaggioUser

from rest_framework import status
from django.urls import reverse

from caravaggio_rest_api.utils import default

from caravaggio_rest_api.tests import CaravaggioBaseTest

# Create your tests here.
from caravaggio_rest_api.users.api.serializers import CaravaggioClientSerializerV1

CONTENTTYPE_JON = "application/json"

_logger = logging.getLogger()


class GetAllClientTest(CaravaggioBaseTest):
    """ Test module for Company model """

    clients = []

    persisted_clients = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.crunchbase = cls.create_user(email="crunchbase@harvester.com", first_name="CrunchBase", last_name="Crawler")

        cls.manual_user_1 = cls.create_user(email="george@mycompany.com", first_name="George", last_name="Clooney")

        cls.manual_user_2 = cls.create_user(email="monica@mycompany.com", first_name="Monica", last_name="Belluci")

        current_path = os.path.dirname(os.path.abspath(__file__))
        cls.clients = GetAllClientTest.load_test_data(
            "{}/clients.json".format(current_path), CaravaggioClientSerializerV1
        )

    def step1_create_clients(self):
        for client in self.clients:
            _logger.info("POST Client: {}".format(client["name"]))
            response = self.api_client.post(
                reverse("client-list"), data=json.dumps(client, default=default), content_type=CONTENTTYPE_JON
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.persisted_clients.append(response.data["id"])

        _logger.info("Persisted companies: {}".format(self.persisted_clients))

    def step2_get_clients(self):
        for index, client_id in enumerate(self.persisted_clients):
            original_client = self.clients[index]
            path = "{0}{1}/".format(reverse("client-list"), client_id)
            _logger.info("Path: {}".format(path))
            response = self.api_client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["name"], original_client["name"])
            super(GetAllClientTest, self).assert_equal_dicts(
                response.data, original_client, ["email", "id", "name", "is_active", "date_joined"]
            )

    def step3_search_name(self):
        """"
        Get clients that have "System" in their name. And other that have
        System 3
        """
        path = "{0}?name__icontains=system".format(reverse("client-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)

        # Get companies that contains *Internet* in their specialties
        # but do not contains "Hardware"
        path = "{0}?name__icontains=system 3".format(reverse("client-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        # System 3 (position 3)
        self.assertEqual(response.data["results"][0]["name"], self.clients[2]["name"])
        super(GetAllClientTest, self).assert_equal_dicts(
            response.data["results"][0], self.clients[2], ["email", "id", "name", "is_active", "date_joined"]
        )
