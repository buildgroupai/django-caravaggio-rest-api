# -*- coding: utf-8 -*-
import os
import json
import logging
import time
import math

from datetime import datetime, timedelta
from dateutil import relativedelta

from caravaggio_rest_api.utils import delete_all_records
from caravaggio_rest_api.example.company.models import Company

from rest_framework import status
from django.urls import reverse

from caravaggio_rest_api.utils import default

from caravaggio_rest_api.tests import CaravaggioBaseTest

# Create your tests here.
from caravaggio_rest_api.example.company.api.serializers import CompanySerializerV1

CONTENTTYPE_JON = "application/json"

_logger = logging.getLogger()


class GetAllCompanyTest(CaravaggioBaseTest):
    """ Test module for Company model """

    companies = []

    persisted_companies = []

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.crunchbase = cls.create_user(email="crunchbase@harvester.com", first_name="CrunchBase", last_name="Crawler")

        cls.manual_user_1 = cls.create_user(email="user@mycompany.com", first_name="Jorge", last_name="Clooney")

        delete_all_records(Company)

        current_path = os.path.dirname(os.path.abspath(__file__))
        cls.companies = GetAllCompanyTest.load_test_data("{}/companies.json".format(current_path), CompanySerializerV1)

    def step1_create_companies(self):
        for company in self.companies:
            _logger.info("POST Company: {}".format(company["name"]))
            response = self.api_client.post(
                reverse("company-list"), data=json.dumps(company, default=default), content_type=CONTENTTYPE_JON
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.persisted_companies.append(response.data["_id"])

        _logger.info("Persisted companies: {}".format(self.persisted_companies))

        # We need to wait until the data has been indexed (Cassandra-Solr)
        # We need to give time for the next search tests
        time.sleep(0.5)

    def step2_get_companies(self):
        for index, company_id in enumerate(self.persisted_companies):
            original_company = self.companies[index]
            path = "{0}{1}/".format(reverse("company-list"), company_id)
            _logger.info("Path: {}".format(path))
            response = self.api_client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["name"], original_company["name"])
            super(GetAllCompanyTest, self).assert_equal_dicts(
                response.data, original_company, ["_id", "created_at", "updated_at"]
            )

    def step3_search_text(self):
        """ We search any company that contains a text in the text field,
        that is a field that concentrates all the textual fields
        (corpus of the company)

        """
        path = "{0}?text=distributed".format(reverse("company-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        # BigML (position 2)
        self.assertEqual(response.data["results"][0]["name"], self.companies[1]["name"])
        super(GetAllCompanyTest, self).assert_equal_dicts(
            response.data["results"][0], self.companies[1], ["_id", "created_at", "updated_at", "score"]
        )

    def step4_search_specialties(self):
        """" Get companies that have "Internet" in their specialties.

        And get companies that have specialties that contains "*Internet*"
        in their name but do not have "Hardware"

        """
        path = "{0}?specialties=Internet".format(reverse("company-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 2)

        # Get companies that contains *Internet* in their specialties
        # but do not contains "Hardware"
        path = "{0}?specialties__contains=Internet&" "specialties__not=Hardware".format(reverse("company-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        # BigML (position 2)
        self.assertEqual(response.data["results"][0]["name"], self.companies[1]["name"])
        super(GetAllCompanyTest, self).assert_equal_dicts(
            response.data["results"][0], self.companies[1], ["_id", "created_at", "updated_at", "score"]
        )

    def step5_search_geo(self):
        """" Will get all the companies within 10 km from the point
             with longitude -123.25022 and latitude 44.59641.

        """
        path = "{0}?km=10&from=44.59641,-123.25022".format(reverse("company-geosearch-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.data["results"][0]["name"], self.companies[1]["name"])
        super(GetAllCompanyTest, self).assert_equal_dicts(
            response.data["results"][0], self.companies[1], ["_id", "created_at", "updated_at", "score"]
        )

    def step6_search_facets(self):
        """" Will get all the companies within 10 km from the point
             with longitude -123.25022 and latitude 44.59641.

        """
        path = "{0}facets/?country_code=limit:1".format(reverse("company-search-list"))
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["fields"]["country_code"]), 1)
        self.assertEqual(response.data["fields"]["country_code"][0]["text"], "USA")
        self.assertEqual(response.data["fields"]["country_code"][0]["count"], 2)

        self.assertEqual(len(response.data["fields"]["stock_symbol"]), 2)
        self.assertEqual(response.data["fields"]["stock_symbol"][0]["text"], "XXX")
        self.assertEqual(response.data["fields"]["stock_symbol"][0]["count"], 1)
        self.assertEqual(response.data["fields"]["stock_symbol"][1]["text"], "YYY")
        self.assertEqual(response.data["fields"]["stock_symbol"][1]["count"], 1)

        self.assertEqual(len(response.data["fields"]["founders"]), 6)

        self.assertEqual(len(response.data["fields"]["specialties"]), 5)
        self.assertEqual(response.data["fields"]["specialties"][0]["text"], "Internet")
        self.assertEqual(response.data["fields"]["specialties"][0]["count"], 2)
        self.assertEqual(response.data["fields"]["specialties"][1]["text"], "Hardware")
        self.assertEqual(response.data["fields"]["specialties"][1]["count"], 1)
        self.assertEqual(response.data["fields"]["specialties"][2]["text"], "Machine Learning")
        self.assertEqual(response.data["fields"]["specialties"][2]["count"], 1)
        self.assertEqual(response.data["fields"]["specialties"][3]["text"], "Predictive Analytics")
        self.assertEqual(response.data["fields"]["specialties"][3]["count"], 1)
        self.assertEqual(response.data["fields"]["specialties"][4]["text"], "Telecommunications")
        self.assertEqual(response.data["fields"]["specialties"][4]["count"], 1)

        start_date = datetime.now() - timedelta(days=50 * 365)
        end_date = datetime.now()
        r = relativedelta.relativedelta(end_date, start_date)
        expected_buckets = math.ceil((r.years * 12 + r.months) / 6)

        self.assertIn(len(response.data["dates"]["foundation_date"]), [expected_buckets, expected_buckets + 1])

        def get_date_bucket_text(start_date, bucket_num, months_bw_buckets):
            return (
                (start_date + relativedelta.relativedelta(months=+bucket_num * months_bw_buckets))
                .replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                .strftime("%Y-%m-%dT%H:%M:%SZ")
            )

        self.assertEqual(response.data["dates"]["foundation_date"][52]["text"], get_date_bucket_text(start_date, 52, 6))
        self.assertEqual(response.data["dates"]["foundation_date"][84]["text"], get_date_bucket_text(start_date, 84, 6))

    def step7_search_facets_ranges(self):
        """" Let's change the foundation_date facet range by all the years from
        1st Jan 2010 til today. Total: 8 years/buckets

        """
        path = (
            "{0}facets/?"
            "foundation_date=start_date:20th May 2010,"
            "end_date:10th Jun 2015,gap_by:year,gap_amount:1".format(reverse("company-search-list"))
        )
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["dates"]["foundation_date"]), 6)

        buckets = {bucket["text"]: bucket["count"] for bucket in response.data["dates"]["foundation_date"]}

        self.assertTrue("2011-01-01T00:00:00Z" in buckets)
        self.assertEqual(buckets["2011-01-01T00:00:00Z"], 1)

    def step8_search_facets_narrow(self):
        """" Drill down when selection facets

        """
        path = "{0}facets/?selected_facets=specialties_exact:Hardware&" "selected_facets=country_code_exact:USA".format(
            reverse("company-search-list")
        )
        _logger.info("Path: {}".format(path))
        response = self.api_client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data["fields"]["country_code"]), 1)
        self.assertEqual(response.data["fields"]["country_code"][0]["text"], "USA")
        self.assertEqual(response.data["fields"]["country_code"][0]["count"], 1)

        self.assertEqual(len(response.data["fields"]["specialties"]), 5)

        specialties = {specialty["text"]: specialty["count"] for specialty in response.data["fields"]["specialties"]}

        self.assertTrue("Hardware" in specialties)
        self.assertEqual(specialties["Hardware"], 1)

        self.assertTrue("Internet" in specialties)
        self.assertEqual(specialties["Internet"], 1)

        self.assertTrue("Machine Learning" in specialties)
        self.assertEqual(specialties["Machine Learning"], 0)

        self.assertTrue("Predictive Analytics" in specialties)
        self.assertEqual(specialties["Predictive Analytics"], 0)

        self.assertTrue("Telecommunications" in specialties)
        self.assertEqual(specialties["Telecommunications"], 1)
