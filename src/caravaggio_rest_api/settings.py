"""
Django settings for Caravaggio REST API project.

# Copyright (c) 2019 BuildGroup Data Services Inc.
# All rights reserved.
"""

import os
import sys
try:
    from dse import ConsistencyLevel
except ImportError:
    from cassandra import ConsistencyLevel

from configurations import Configuration


class Common(Configuration):

    CARAVAGGIO_API_TITLE = "Caravaggio API"
    CARAVAGGIO_API_VERSION = "v1"
    CARAVAGGIO_API_DESCRIPTION = \
        "Example API for Caravaggio RESTful applications"
    CARAVAGGIO_API_TERMS_URL = "https://www.google.com/policies/terms/"
    CARAVAGGIO_API_CONTACT = "contact@buildgroupai.com"
    CARAVAGGIO_API_LICENSE = "BSD License"

    # Build paths inside the project like this: os.path.join(BASE_DIR, ...)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "2w=es4^%3i4n2cya(0)ws&bq+@h)m1nepzkvd&pi+wvgsue%ms")

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = os.getenv("DEBUG", "False") == "True"

    ADMINS = (
        # ('Your Name', 'your_email@example.com'),
    )

    MANAGERS = ADMINS

    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "dev@domain.com")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "***")

    DSE_SUPPORT = os.getenv("DSE_SUPPORT", "True") == "True"

    # SECURITY WARNING: App Engine's security features ensure that it is
    # safe to have ALLOWED_HOSTS = ['*'] when the app is deployed. If you
    # deploy a Django app not on App Engine, make sure to set an appropriate
    # host here.
    # See https://docs.djangoproject.com/en/1.10/ref/settings/
    ALLOWED_HOSTS = ["*"]

    INTERNAL_IPS = []

    # Application definition
    INSTALLED_APPS = [
        'django_cassandra_engine',
        'django_cassandra_engine.sessions',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        # 'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Comment the next line to disable the admin:
        'django.contrib.admin',
        # Comment the next line to disable admin documentation:
        'django.contrib.admindocs',
        'rest_framework',
        'rest_framework_filters',
        'rest_framework.authtoken',
        'rest_framework_cache',
        'drf_yasg',
        'haystack',
        'caravaggio_rest_api',
        'caravaggio_rest_api.logging',
        'caravaggio_rest_api.users',
        'caravaggio_rest_api.example.company'
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    ROOT_URLCONF = 'caravaggio_rest_api.urls'

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(BASE_DIR, 'caravaggio_rest_api/templates'),
            ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.media',
                    'django.template.context_processors.static',
                    'django.template.context_processors.tz',
                    'django.template.context_processors.request',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    WSGI_APPLICATION = 'caravaggio_rest_api.wsgi.application'

    # A sample logging configuration. The only tangible logging
    # performed by this configuration is to send an email to
    # the site admins on every HTTP 500 error when DEBUG=False.
    # See http://docs.djangoproject.com/en/dev/topics/logging for
    # more details on how to customize your logging configuration.
    LOGGING_FILE = "/data/caravaggio_rest_api/" \
                   "log/caravaggio_rest_api-debug.log"

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
        'formatters': {
            'verbose': {
                'format':
                    '%(levelname)s %(asctime)s %(module)s %(process)d '
                    '%(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            },
            'debug_log': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOGGING_FILE,
                'maxBytes': 1024 * 1024 * 100,
                'backupCount': 1,
                'formatter': 'verbose'
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['mail_admins'],
                'level': 'ERROR',
                'propagate': True,
            },
            'django_cassandra_engine': {
                'handlers': ['console', 'debug_log', 'mail_admins'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'caravaggio_rest_api': {
                'handlers': ['console', 'mail_admins'],
                'level': 'DEBUG',
                'propagate': True,
            }
        }
    }

    # Database

    # Check to see if MySQLdb is available; if not, have pymysql masquerade as
    # MySQLdb. This is a convenience feature for developers who cannot install
    # MySQLdb locally; when running in production on Google App Engine Standard
    # Environment, MySQLdb will be used.
    # try:
    #    import MySQLdb  # noqa: F401
    # except ImportError:
    #    import pymysql
    #    pymysql.install_as_MySQLdb()

    # [START db_setup]
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "6543")
    DB_NAME = os.getenv("DB_NAME", "caravaggio")
    DB_USER = os.getenv("DB_USER", "caravaggio")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "caravaggio")

    CASSANDRA_DB_HOST = os.getenv(
        "CASSANDRA_DB_HOST", "127.0.0.1,127.0.0.2,127.0.0.3")
    CASSANDRA_DB_NAME = os.getenv("CASSANDRA_DB_NAME", "caravaggio")
    CASSANDRA_DB_USER = os.getenv("CASSANDRA_DB_USER", "caravaggio")
    CASSANDRA_DB_PASSWORD = os.getenv("CASSANDRA_DB_PASSWORD", "caravaggio")
    CASSANDRA_DB_REPLICATION = os.getenv("CASSANDRA_DB_REPLICATION", 1)

    try:
        from dse.cqlengine import models
    except ImportError:
        from cassandra.cqlengine import models

    models.DEFAULT_KEYSPACE = CASSANDRA_DB_NAME

    # Running on production App Engine, so connect to Google Cloud SQL using
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
        },
        'cassandra': {
            'ENGINE': 'django_cassandra_engine',
            'NAME': CASSANDRA_DB_NAME,
            'TEST': {
                'NAME': "test_{}".format(CASSANDRA_DB_NAME)
            },
            'HOST': CASSANDRA_DB_HOST,
            'USER': CASSANDRA_DB_USER,
            'PASSWORD': CASSANDRA_DB_PASSWORD,
            'OPTIONS': {
                'replication': {
                    'strategy_class': "SimpleStrategy",
                    'replication_factor': CASSANDRA_DB_REPLICATION
                },
                'connection': {
                    'consistency': ConsistencyLevel.LOCAL_ONE,
                    'retry_connect': True
                    # + All connection options for cassandra.cluster.Cluster()
                },
                'session': {
                    'default_timeout': 10,
                    'default_fetch_size': 10000
                    # + All options for cassandra.cluster.Session()
                }
            }
        }
    }
    # [END db_setup]

    # Password validation
    # https://docs.djangoproject.com/en/1.11/ref/settings/#
    # auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.'
                    'UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.'
                    'MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.'
                    'CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.'
                    'NumericPasswordValidator',
        },
    ]

    # Internationalization

    # Local time zone for this installation. Choices can be found here:
    # http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
    # although not all choices may be available on all operating systems.
    # In a Windows environment this must be set to your system time zone.
    TIME_ZONE = "UTC"

    # Language code for this installation. All choices can be found here:
    # http://www.i18nguy.com/unicode/language-identifiers.html
    LANGUAGE_CODE = "en-us"

    SITE_ID = 1

    # If you set this to False, Django will make some optimizations so as not
    # to load the internationalization machinery.
    USE_I18N = True

    # If you set this to False, Django will not format dates, numbers and
    # calendars according to the current locale.
    USE_L10N = True

    # If you set this to False, Django will not use timezone-aware datetimes.
    USE_TZ = True

    # Absolute filesystem path to the directory that will hold user-uploaded
    # files.
    # Example: "/home/media/media.lawrence.com/media/"
    MEDIA_ROOT = ''

    # URL that handles the media served from MEDIA_ROOT. Make sure to use a
    # trailing slash.
    # Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
    MEDIA_URL = ''

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.8/howto/static-files/
    STATIC_ROOT = os.path.join(BASE_DIR + '/caravaggio_rest_api/static')

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/1.8/howto/static-files/
    # STATIC_URL = '/static/'
    STATIC_URL = os.getenv('STATIC_URL', '/static/')

    STATICFILES_DIRS = (
        # Put strings here, like "/home/html/static" or "C:/www/django/static".
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
        # os.path.join(BASE_DIR + '/caravaggio_rest_api/static'),
    )

    # List of finder classes that know how to find static files in
    # various locations.
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
    )

    REST_FRAMEWORK = {
        'PAGE_SIZE': 10,
        'DEFAULT_PAGINATION_CLASS':
            'caravaggio_rest_api.pagination.CustomPageNumberPagination',

        'DEFAULT_THROTTLE_CLASSES': (
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
            'rest_framework.throttling.ScopedRateThrottle'
        ),

        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/day',
            'user': '60/minute'
        },

        # The name of the alternative query string  be can use for authenticate
        # users in each request
        # Ex. http://mydomain.com/users/user/?auth_token=<token_key>"
        'QUERY_STRING_AUTH_TOKEN': "auth_token",

        # Do we want to log any access made to the API?
        'LOG_ACCESSES': True,

        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.SessionAuthentication',
            'caravaggio_rest_api.drf.authentication.'
            'TokenAuthSupportQueryString',
        ),

        # Use Django's standard `django.contrib.auth` permissions,
        # or allow read-only access for unauthenticated users.
        'DEFAULT_PERMISSION_CLASSES': [
            # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
            'rest_framework.permissions.IsAuthenticated'
        ],
        # REST framework also includes support for generic filtering backends
        # that allow you to easily construct complex searches and filters
        'DEFAULT_FILTER_BACKENDS':
            ('drf_haystack.filters.HaystackFilter',
             'drf_haystack.filters.HaystackBoostFilter',
             'drf_haystack.filters.HaystackOrderingFilter',),

        'TEST_REQUEST_DEFAULT_FORMAT': 'json',

        'ORDERING_PARAM': 'order_by',

        # https://www.django-rest-framework.org/api-guide/fields/#decimalfield
        # To use decimal as representation by default
        'COERCE_DECIMAL_TO_STRING': False,

        'EXCEPTION_HANDLER':
            'caravaggio_rest_api.drf.exceptions.caravaggio_exception_handler'
    }

    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_AUTHENTICATION_METHOD = 'email'

    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_UNIQUE_EMAIL = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_USER_EMAIL_FIELD = 'email'
    ACCOUNT_LOGOUT_ON_GET = True

    AUTH_USER_MODEL = 'users.CaravaggioUser'

    REST_AUTH_SERIALIZERS = {
        "USER_DETAILS_SERIALIZER":
            "caravaggio_rest_api.users.serializers."
            "CaravaggioUserDetailsSerializer",
    }
    REST_AUTH_REGISTER_SERIALIZERS = {
        "REGISTER_SERIALIZER":
            "caravaggio_rest_api.users.serializers."
            "CaravaggioUserRegisterSerializer",
    }

    SESSION_ENGINE = 'django_cassandra_engine.sessions.backends.db'
    CASSANDRA_FALLBACK_ORDER_BY_PYTHON = True

    # Enable/Disable throttling
    THROTTLE_ENABLED = os.getenv("THROTTLE_ENABLED", "False") == "True"

    GET_THROTTLE_RATE = "6000/minute"
    LIST_THROTTLE_RATE = "200/minute"
    POST_THROTTLE_RATE = "100/minute"
    PUT_THROTTLE_RATE = "100/minute"
    DELETE_THROTTLE_RATE = "60/minute"
    VALIDATE_THROTTLE_RATE = "60/minute"
    PATCH_THROTTLE_RATE = "100/minute"
    METADATA_THROTTLE_RATE = "6000/minute"
    FACETS_THROTTLE_RATE = "6000/minute"

    THROTTLE_OPERATIONS = {
        'retrieve': GET_THROTTLE_RATE,
        'highlight': GET_THROTTLE_RATE,
        'list': LIST_THROTTLE_RATE,
        'create': POST_THROTTLE_RATE,
        'update': PUT_THROTTLE_RATE,
        'destroy': DELETE_THROTTLE_RATE,
        'validate': VALIDATE_THROTTLE_RATE,
        'partial_update': PATCH_THROTTLE_RATE,
        'metadata': METADATA_THROTTLE_RATE,
        'facets': FACETS_THROTTLE_RATE
    }

    HAYSTACK_DJANGO_ID_FIELD = "id"

    HAYSTACK_KEYSPACE = CASSANDRA_DB_NAME
    if 'test' in sys.argv:
        HAYSTACK_KEYSPACE = "test_{}".format(HAYSTACK_KEYSPACE)

    HAYSTACK_URL = os.getenv("HAYSTACK_URL", "http://127.0.0.1:8983/solr")
    HAYSTACK_ADMIN_URL = os.getenv(
        "HAYSTACK_ADMIN_URL", "http://127.0.0.1:8983/solr/admin/cores")

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE':
                'caravaggio_rest_api.haystack.backends.'
                'solr_backend.CassandraSolrEngine',
            'URL': HAYSTACK_URL,
            'KEYSPACE': HAYSTACK_KEYSPACE,
            'ADMIN_URL': HAYSTACK_ADMIN_URL,
            'BATCH_SIZE': 100,
            'INCLUDE_SPELLING': True,
            "DISTANCE_AVAILABLE": True,
        },
    }

    # Caching: Redis backend for caching
    REDIS_HOST_PRIMARY = os.getenv("REDIS_HOST_PRIMARY", "127.0.0.1")
    REDIS_PORT_PRIMARY = os.getenv("REDIS_PORT_PRIMARY", "6379")
    REDIS_PASS_PRIMARY = os.getenv("REDIS_PASS_PRIMARY", "")

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://{0}{1}:{2}/1".format(
                ":{0}@".format(REDIS_PASS_PRIMARY)
                if REDIS_PASS_PRIMARY else "",
                REDIS_HOST_PRIMARY, REDIS_PORT_PRIMARY),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "caravaggio_rest_api"
        },
        'disk_cache': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': '/var/tmp/caravaggio_rest_api_cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 10000
            },
            "KEY_PREFIX": "caravaggio_rest_api"
        },
        'mem_cache': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'caravaggio_rest_api_cache',
            "KEY_PREFIX": "caravaggio_rest_api"
        }
    }

    # DRF Caching
    REST_FRAMEWORK_CACHE = {
        # The caching system must be always a distributed cache if we plan
        # to start multiple instances of the application
        "DEFAULT_CACHE_BACKEND": 'default',
        "DEFAULT_CACHE_TIMEOUT": 86400,  # Default is 1 day
    }

    # Swagger Docs
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': {
            'api_key': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization'
            }
        },
        'LOGIN_URL': 'rest_framework:login',
        'LOGOUT_URL': 'rest_framework:logout',
        'DOC_EXPANSION': "none",
        'APIS_SORTER': 'alpha',
        'OPERATIONS_SORTER': None,
        'JSON_EDITOR': True,
        'USE_SESSION_AUTH': True,
        'SHOW_REQUEST_HEADERS': True,
        'SUPPORTED_SUBMIT_METHODS': [
            'get',
            'post',
            'put',
            'delete',
            'patch'
        ],
    }


class Development(Common):
    """
    The in-development settings and the default configuration.
    """
    DEBUG = os.getenv("DEBUG", "True") == "True"

    ALLOWED_HOSTS = []

    INTERNAL_IPS = [
        '127.0.0.1'
    ]

    INSTALLED_APPS = Common.INSTALLED_APPS + [
        'django_extensions', 'debug_toolbar'
    ]

    MIDDLEWARE = Common.MIDDLEWARE + [
        'debug_toolbar.middleware.DebugToolbarMiddleware'
    ]

    Common.REST_FRAMEWORK['LOG_ACCESSES'] = False


class Staging(Common):
    """
    The in-staging settings.
    """
    # Databases

    # The docker container starts a PGBouncer server in local to manage
    # the pool of connections. We need to connect to the local pgbounce
    # server
    CASSANDRA_DB_STRATEGY = os.getenv(
        "CASSANDRA_DB_STRATEGY", "NetworkTopologyStrategy")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            "HOST": Common.DB_HOST,
            "PORT": Common.DB_PORT,
            'NAME': Common.DB_NAME,
            'USER': Common.DB_USER,
            'PASSWORD': Common.DB_PASSWORD,
        },
        'cassandra': {
            'ENGINE': 'django_cassandra_engine',
            'NAME': Common.CASSANDRA_DB_NAME,
            'HOST': Common.CASSANDRA_DB_HOST,
            'USER': Common.CASSANDRA_DB_USER,
            'PASSWORD': Common.CASSANDRA_DB_PASSWORD,
            'OPTIONS': {
                'replication': {
                    'strategy_class': CASSANDRA_DB_STRATEGY,
                    'replication_factor': Common.CASSANDRA_DB_REPLICATION

                    # 'strategy_class': 'NetworkTopologyStrategy',
                    # 'datacenter1': N1,
                    # ...,
                    # 'datacenterN': Nn
                },
                'connection': {
                    'consistency': ConsistencyLevel.LOCAL_ONE,
                    'retry_connect': True
                    # + All connection options for cassandra.cluster.Cluster()
                },
                'session': {
                    'default_timeout': 10,
                    'default_fetch_size': 10000
                    # + All options for cassandra.cluster.Session()
                }
            }
        }
    }

    # Security
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', "False") == "True"
    USE_X_FORWARDED_HOST = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    SECURE_BROWSER_XSS_FILTER = SECURE_SSL_REDIRECT
    SECURE_CONTENT_TYPE_NOSNIFF = SECURE_SSL_REDIRECT
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL_REDIRECT
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_HOST = os.getenv('SECURE_SSL_HOST', None)
    SECURE_SSL_REDIRECT = SECURE_SSL_REDIRECT
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO',
                               "https" if SECURE_SSL_REDIRECT else "http")


class Production(Staging):
    """
    The in-production settings.
    """

    LOGGING_FILE = "/var/log/caravaggio_rest_api-debug.log"
