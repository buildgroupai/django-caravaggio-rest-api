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


### Run the tests

To run the tests we only need to run the following instruction:

```
$ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner
```

The output will be something like:

```
Creating test database for alias 'default'...
Creating test database for alias 'cassandra'...
Creating keyspace test_apian [CONNECTION cassandra] ..
Syncing davinci_crawling.example.models.BovespaCompany
Syncing davinci_crawling.example.models.BovespaCompanyFile
Syncing davinci_crawling.example.models.BovespaAccount
System check identified no issues (0 silenced).
...
...
```

Avoid the destruction of the database after the tests have finished and the indexes synchronization:

```
$ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner --keepdb --keep-indexes
```

# Install GDAL for Spatial queries

In Sierra/Mojave MAC OSX:

```
$ sudo chown -R $(whoami) $(brew --prefix)/*
$ sudo install -d -o $(whoami) -g admin /usr/local/Frameworks
$ brew install gdal

```

# Install Libev for Cassandra/DSE driver compilation

In Sierra/Mojave MAC OSX:

```
$ brew install libev

```

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

## For Development
In order to maintain a clean code, it's strongly recommended to install the
project pre-commit hook. Just execute the following commands in the root
directory:

```
$ chmod +x pre-commit.sh

$ ln -s ../../pre-commit.sh .git/hooks/pre-commit
```
