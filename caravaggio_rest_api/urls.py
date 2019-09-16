"""
Apian URL Configuration

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
from django.conf import urls, settings
from django.conf.urls import url, include
from django.urls import path

from rest_framework_cache.registry import cache_registry
from django.contrib import admin

from caravaggio_rest_api.users.api.views import \
    CustomAuthToken, AdminAuthToken

from caravaggio_rest_api.views import schema_view

from caravaggio_rest_api.users.api.urls import urlpatterns as users_urls

from caravaggio_rest_api.example.company.urls import \
    urlpatterns as company_urls

urls.handler500 = 'rest_framework.exceptions.server_error'
urls.handler400 = 'rest_framework.exceptions.bad_request'

urlpatterns = [
    # ## DO NOT TOUCH

    # API Swagger documentation
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    url(r'^redoc/$',
        schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Django REST Framework auth urls
    url(r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')),

    # Mechanism for clients to obtain a token given the username and password.
    url(r'^api-token-auth/', CustomAuthToken.as_view()),

    # Mechanism for administrator to obtain a token given
    # the client id and email.
    url(r'^admin-token-auth/', AdminAuthToken.as_view()),

    # Access to the admin site
    url(r'^admin/', admin.site.urls),

    # Users API version
    url(r'^users/', include(users_urls)),

    # ## END DO NOT TOUCH

    # API
    url(r'^companies/', include(company_urls)),

    # Default API version
    # url(r'^$', RedirectView.as_view(url='zion/')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns

cache_registry.autodiscover()
