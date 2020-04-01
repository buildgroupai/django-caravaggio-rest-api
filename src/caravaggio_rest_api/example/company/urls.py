""" Company URL Configuration

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
from django.conf import settings
from django.conf.urls import url, include

from caravaggio_rest_api.example.company.api.views import CompanyViewSet, CompanySearchViewSet, CompanyGEOSearchViewSet
from caravaggio_rest_api.drf.routers import CaravaggioRouter

# API v1 Router. Provide an easy way of automatically determining the URL conf.

api_SEARCH_COMPANY = CaravaggioRouter(actions=["list"])

if settings.DSE_SUPPORT:
    api_SEARCH_COMPANY.register(r"company/search", CompanySearchViewSet, base_name="company-search")

    api_SEARCH_COMPANY.register(r"company/geosearch", CompanyGEOSearchViewSet, base_name="company-geosearch")

api_COMPANY = CaravaggioRouter()

api_COMPANY.register(r"company", CompanyViewSet, base_name="company")

urlpatterns = [
    # Company API version
    url(r"^", include(api_SEARCH_COMPANY.urls + api_COMPANY.urls), name="company-api"),
]
