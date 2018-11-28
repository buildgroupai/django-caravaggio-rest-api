# Caravaggio

API project template based on `Django 2.1 (and higher)`, and `DRF 3.8 (and higher)`.

Technologies:

- Django REST Framework (DRF)
- DRF Cache support (for rdb and cassandra models)
- DRF Throttle support by ViewSet and request action (retrieve, list, create, update, etc.)
- DRF Token Authentication (no username needed, Bearer token)
- PostgreSQL backend for miscellaneous models (User, Token, etc.)
- DSE Cassandra backend for business models
- Configuration of Cassandra-DRF serializers
- Support for JSONField in Cassandra (Text field)
- Support for pre/post callbacks in CassandraModel (DRF cache clean actions)
- DRF-Haystack-DSE support to support fast searches (DSE-Solr) with model examples
- Command to synchronize the DSE tables with the needed search indexes
- Swagger view of the API documentation 
- Google App Engine Flexible (Custom) support
- PGBouncer Connection Pool supported in the Docker image


## RESTFul Searches

Available operations:

```
    'content': u'%s',
    'contains': u'*%s*',
    'endswith': u'*%s',
    'startswith': u'%s*',
    'exact': u'%s',
    'gt': u'{%s TO *}',
    'gte': u'[%s TO *]',
    'lt': u'{* TO %s}',
    'lte': u'[* TO %s]',
    'fuzzy': u'%s~',		
    'in': u'("%s"... OR ... "%s")'
    'range': u'[%s TO %s]'
```    

Boosting term:

```
boost=alpha_2,5
```

Geo Spatial searches:

```
km=10&from=-123.25022,44.59641
```
