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


## Development Setup

Once we have cloned Caravaggio into our local environment, the first thing
 we'll need to do is to setup a new python environment using the conda
 program:

```shell script
# Create the anaconda environment for the project
$ conda create -y -n caravaggio_rest_api pip python=3.6

# Activate the environment
$ conda activate caravaggio_rest_api
(caravaggio_rest_api) $
```

If we are going to need Spatial support for our models, then we will need to
install binary GDAL too:

```shell script
# To avoid problems installing binary GDAL we better use conda
(caravaggio_rest_api) $ conda install -y gdal
```

Now we are ready to install the dependencies of the Caravaggio project:

```shell script
# Install dependencies
(caravaggio_rest_api) $ python setup.py develop

# If we need GDAL 
(caravaggio_rest_api) $ pip install caravaggio_rest_api[spatial]

# And the development dependencies
(caravaggio_rest_api) $ pip install -r requirements_test.txt
``` 

The logging system is generating our log file in the following folder 
`/data/caravaggio_rest_api/log` and we need to prepare the fs in accordance:

```shell script
(caravaggio_rest_api) $ sudo mkdir -p /data/caravaggio_rest_api/log
(caravaggio_rest_api) $ sudo chown -R `whoami`:staff /data/caravaggio_rest_api
```

### Setup of Databases

In Caravaggio we have 3 backend dependencies:

- PostgreSQL: to manage all the Django sessions and users persistence
- DataStax Enterprise (DSE): to manage all our Big Data entities
- Redis: to cache data in a distributed environment

We are going to rely on Docker to manage our PostgreSQL and Redis services.

```shell script
# Provision the Redis instance using Docker
(caravaggio_rest_api) $ docker run --name caravaggio-redis -p 6379:6379 -d redis:3.0

# Provision the PostgreSQL instance using Docker
(caravaggio_rest_api) $ docker run --name caravaggio-db -e POSTGRES_PASSWORD=XXXXXXXXXX -p 6543:5432 -d postgres:9.6
```

And we will need to prepare our PostgreSQL database as follows:

```shell script
$ docker run -it --rm --link caravaggio-db:postgres postgres:9.6 psql -h postgres -U postgres
Password for user postgres: XXXXXXXXXX
psql (9.6.1)
Type "help" for help.

postgres= \c template1;
postgres= CREATE EXTENSION IF NOT EXISTS plpgsql;
postgres= CREATE EXTENSION IF NOT EXISTS hstore;
postgres= \dx 
 hstore  | 1.4     | public     | data type for storing sets of (key, value) pairs
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language

postgres= CREATE ROLE caravaggio WITH LOGIN PASSWORD 'caravaggio';
postgres= CREATE DATABASE caravaggio WITH OWNER caravaggio ENCODING 'UTF8' TEMPLATE template1;
postgres= ALTER USER caravaggio WITH SUPERUSER;
postgres= \q 
```

And for __DSE__ we can follow the instructions here [DSE Install](./internal_docs/dse_local.md).

### Prepare the databases schemas

Now its time to prepare the schemas of our databases.

For our PostgreSQL database we execute the following instructions:
```shell script
(caravaggio_rest_api) $ python manage.py makemigrations
(caravaggio_rest_api) $ python manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, authtoken, contenttypes, crawler_test, sites, users
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying users.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying authtoken.0001_initial... OK
  Applying authtoken.0002_auto_20160226_1747... OK
  Applying caravaggio_rest_api.0001_initial... OK
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
```

And for our cassandra and solr databases we execute the following instructions:
```shell script
(caravaggio_rest_api) $ python manage.py sync_cassandra

Creating keyspace caravaggio [CONNECTION cassandra] ..
Syncing django_cassandra_engine.sessions.models.Session
Syncing caravaggio_rest_api.logging.models.ApiAccess

(caravaggio_rest_api) $ python manage.py sync_indexes

INFO Creating indexes in caravaggio [CONNECTION cassandra] ..
INFO Creating index %s.%s
INFO Index class associated to te model caravaggio_rest_api.logging.models.ApiAccess
INFO Creating SEARCH INDEX if not exists for model: <class 'django_cassandra_engine.models.ApiAccess'>
INFO Setting index parameters: realtime = true
INFO Setting index parameters: autoCommitTime = 100
INFO Setting index parameters: ramBufferSize = 2048
INFO Processing field field <class 'haystack.fields.CharField'>(user)
WARNING Maybe te field has been already defined in the schema. Cause: Error….
…
…
…

WARNING Maybe the copy field type has been already defined in the schema. Cause: Error from server: code=2200 [Invalid query] message="The search index schema is not valid because: Can't load schema schema.xml: copyField dest :'is_deleted_exact' is not an explicit field and doesn't match a dynamicField."
INFO Processing field field <class 'haystack.fields.CharField'>(deleted_reason)
WARNING Maybe te field has been already defined in the schema. Cause: Error from server: code=2200 [Invalid query] message="The search index schema is not valid because: Can't load schema schema.xml: [schema.xml] Duplicate field definition for 'deleted_reason' [[[deleted_reason{type=StrField,properties=indexed,omitNorms,omitTermFreqAndPositions}]]] and [[[deleted_reason{type=StrField,properties=indexed,omitNorms,omitTermFreqAndPositions}]]]”
```

## Users

Caravaggio is ready to work as a multi-system configuration. Multiple external
 systems, also called Clients, can be integrated with the API system and act
 as an independent solution with its own user management. The basic
 configuration will have one only system created: BGDS.
 
Caravaggio User Subsystem relies on the following entities:

- Client: represents an entire external system. Useful when we allow white
 brands and the management of its own users to these external systems.
    
- Organization: represents a group of users.

- User: the user itself. Each user belongs to one or more Organizations playing 
 different roles: owner, administrator, member, restricted member.
 
Our deployment needs at least one superadmin user, that also will be part of the
first Client instance of the solution.  

To create our super user we only need to execute the following instructions:

```shell script
# Creating the first (and maybe the only) Client of the system, ourselves.
# It will become the default client of the API (external system)
(caravaggio_rest_api) $ python manage.py createclient --email it@buildgroupai.com --name "BuildGroup Data Services Inc."
Client [932a9653-a630-4631-ab3f-d61418893d26] created successfully

$ export CLIENT_ID=932a9653-a630-4631-ab3f-d61418893d26
```

Setup the admin user, that will be also a super user of the default external system:
```shell script
(caravaggio_rest_api) $ python manage.py createsuperuser \
    --username ${CLIENT_ID}-xalperte@buildgroupai.com \
    --client $CLIENT_ID \
    --email xalperte@buildgroupai.com \
    --is_client_staff True \
    --first_name "Javier" \
    --last_name "Alperte" \
    --no-input

$ python manage.py changepassword ${CLIENT_ID}-xalperte@buildgroupai.com
Changing password for user '32a9653-a630-4631-ab3f-d61418893d26-xalperte@buildgroupai.com'
Password: [for instance: caravaggio]
```

## Tests

To run the tests we only need to run the following instruction:

```
$ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner
```

The output will be something like:

```
Creating test database for alias 'default'...
Creating test database for alias 'cassandra'...
Creating keyspace test_caravaggio [CONNECTION cassandra] ..
Syncing django_cassandra_engine.sessions.models.Session
Syncing caravaggio_rest_api.logging.models.ApiAccess
System check identified no issues (0 silenced).
...
...
```

Avoid the destruction of the database after the tests have finished and the indexes synchronization:

```
$ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner --keepdb --keep-indexes
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
