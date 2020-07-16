.. _caravaggio_index:

==========================
Django Caravaggio REST API
==========================

This is the documentation of **Caravaggio REST API**.

Caravaggio REST API is a Django library that integrates a set of libraries
and technologies to make easy the development of RESTful API for Big Data.

The main audience of Caravaggio is developers.

These are some of the features available in Caravaggio:

- A `Django 2.x`_ application. A mature and powerful framework to develop advanced web applications.
- `Django REST Framework`_ (DRF) to build RESTful APIs easily on top of Django.
- `DRF Token Authentication`_ (no username needed, Bearer token)
- `DSE ORM`_: using Cassandra to declare business models (DataStax)
- Support for JSONField in Cassandra (Text field)
- `DRF-Haystack-DSE`_ support to support fast searches (DSE-Solr) with model examples
- Custom field serializer to make possible the indexation and search of Map columns using `DSE Search`_-`Solr`_
- Support for spatial searches using Cassandra models and Solr (GDAL).
- Support for pre/post callbacks in CassandraModel (DRF cache clean actions)
- Advanced users subsystem based on Organizations, Users, Allowances/Permissions
- DRF Cache support (for rdb and cassandra models)
- DRF Throttle support by ViewSet and request action (retrieve, list, create, update, etc.)
- A Django management command to synchronize DSE-C* tables and DSE-Solr search indexes.
- Swagger view of the API documentation (OpenAPI 2.0) through DRF Yasg. Useful to assist on the development of REST clients.
- Docker container to allow the deployment of Caravaggio application on Google App Engine (GAE)
- PGBouncer Connection Pool supported in the Docker image
- PostgreSQL backend for miscellaneous models (Organizations, User, Token, etc.)

Contents
========

    :ref:`Authentication <caravaggio_authentication>`


.. _Django 2.x: https://www.djangoproject.com/start/overview/
.. _Django REST Framework: https://www.django-rest-framework.org/
.. _DRF Token Authentication: https://www.django-rest-framework.org/api-guide/authentication/
.. _DSE ORM: https://docs.datastax.com/en/developer/python-driver/3.19/object_mapper/
.. _DRF-Haystack-DSE: https://drf-haystack.readthedocs.io/en/latest/
.. _Solr: https://lucene.apache.org/solr/
.. _DSE Search: https://lucene.apache.org/solr/
.. _GDAL: https://gdal.org/
.. _DRF_Haystack_GEO: https://drf-haystack.readthedocs.io/en/latest/03_geospatial.html
.. _DRF_Throttling: https://www.django-rest-framework.org/api-guide/throttling/
.. _DRF_Yasg: https://github.com/axnsan12/drf-yasg
.. _Docker: https://www.docker.com/
.. _PGBouncer: https://pgbouncer.github.io/features.html
.. _PostgreSQL: https://www.postgresql.org/

