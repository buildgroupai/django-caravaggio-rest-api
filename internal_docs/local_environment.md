# Local Environment

This file details all the steps we should do in order to execute the service in a local environment.

First we will need to prepare the required thirds services, like databases, and then we will start the local server with the application.

We will do it using different approaches:

- Running a development server
- Running the server in a Docker environment simulating production

## Required local services

We need to start the followins services:

- A PostgreSQL server (default database)
- A DSE instance (models database)
- A Redis server (cache database)

We will use docker to start the PostgreSQL and Redis serverm and CCM for DSE.

### PostgreSQL 9.6 server

Start the server:

```shell script
$ docker run --name caravaggio-db -e POSTGRES_PASSWORD=XXXXXXXX -p 6543:5432 -d postgres:9.6
``` 

Activate the extensions:

```shell script
$ docker run -it --rm --link caravaggio-db:postgres postgres:9.6 psql -h postgres -U postgres
Password for user postgres: [XXXXXXXX] 
psql (9.6.1)
Type "help" for help.
```
```sql
postgres= \c template1;
postgres= CREATE EXTENSION IF NOT EXISTS plpgsql;
postgres= CREATE EXTENSION IF NOT EXISTS hstore;
postgres= \dx 
 hstore  | 1.4     | public     | data type for storing sets of (key, value) pairs
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
```


Create the database (Gives rights to create databases - for the tests)

```sql
postgres= CREATE ROLE caravaggio WITH LOGIN PASSWORD 'caravaggio';
postgres= CREATE DATABASE caravaggio WITH OWNER caravaggio ENCODING 'UTF8' TEMPLATE template1;
postgres= ALTER USER caravaggio WITH SUPERUSER;
postgres= \q 
```

Let's test the caravaggio user:

```shell script
$ docker run -it --rm --link caravaggio-db:postgres postgres:9.6 psql -h postgres -U caravaggio
Password for user caravaggio: 
```

### Redis 3 server

Now we start the redis server

```shell script
$ docker run --name caravaggio-redis -p 6379:6379 -d redis:3.0
```

Test the server connection

```shell script
$ docker run -it --rm --link caravaggio-redis:redis redis:3.0 redis-cli -h redis
redis:6379> get test
(nil)
redis:6379> quit
```

### DataStax Enterprise server

To install DataStax Enterprise in local we need to follow these instructions: [DSE Local](dse_local.md)

## Run application with development server

First we need to populate the databases, the default and the DSE databases.

```shell script
$ python manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, authtoken, contenttypes, sites
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
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
  Applying authtoken.0001_initial... OK
  Applying authtoken.0002_auto_20160226_1747... OK
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
```

Now we can create the DSE model

```shell script
$ python manage.py sync_cassandra

Creating keyspace apian [CONNECTION cassandra] ..
Syncing django_cassandra_engine.sessions.models.Session
Syncing company.models.BalanceSheet
Syncing company.models.Company
```

And then the solr indexes

```shell script
$ python manage.py sync_indexes

INFO Creating indexes in apian [CONNECTION cassandra] ..
INFO Creating index %s.%s
INFO Index class associated to te model company.models.CompanyIndex
INFO Creating SEARCH INDEX if not exists for model: <class 'django_cassandra_engine.models.Company'>
INFO Setting index parameters: realtime = true
INFO Setting index parameters: autoCommitTime = 100
INFO Setting index parameters: ramBufferSize = 2048
INFO Processing field field <class 'haystack.fields.CharField'>(_id)
WARNING Maybe te field has been already defined in the schema. Cause: Error from server: code=2200….
….
…
….

WARNING Maybe te field has been already defined in the schema. Cause: Error from server: code=2200 [Invalid query] message="The search index schema is not valid because: Can't load schema schema.xml: [schema.xml] Duplicate field definition for 'crawler_config' [[[crawler_config{type=StrField,properties=indexed,omitNorms,omitTermFreqAndPositions}]]] and [[[crawler_config{type=StrField,properties=indexed,omitNorms,omitTermFreqAndPositions}]]]"
INFO Processing field field <class 'haystack.fields.CharField'>(extra_data)
WARNING Maybe te field has been already defined in the schema. Cause: Error from server: code=2200 [Invalid query] message="The search index schema is not valid because: Can't load schema schema.xml: [schema.xml] Duplicate field definition for 'extra_data' [[[extra_data{type=StrField,properties=indexed,omitNorms,omitTermFreqAndPositions}]]] and [[[extra_data{type=TextField,properties=indexed,tokenized}]]]"
INFO Changing SEARCH INDEX field extra_data to TextField
```

We can check if everything has been created well:

```shell script
$ ccm node1 cqlsh
```

```sql
cqlsh> use caravaggio
cqlsh:caravaggio> describe tables;

example_model

cqlsh:caravaggio> describe example_model

CREATE TABLE caravaggio.example_model (
    example_id uuid PRIMARY KEY,
    created_at timestamp,
    description text,
    example_json text,
    example_type int,
    example_values_list list<int>,
    example_values_map map<text, int>
) WITH bloom_filter_fp_chance = 0.01
    AND caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
    AND comment = ''
    AND compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy', 'max_threshold': '32', 'min_threshold': '4'}
    AND compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
    AND crc_check_chance = 1.0
    AND dclocal_read_repair_chance = 0.1
    AND default_time_to_live = 0
    AND gc_grace_seconds = 864000
    AND max_index_interval = 2048
    AND memtable_flush_period_in_ms = 0
    AND min_index_interval = 128
    AND read_repair_chance = 0.0
    AND speculative_retry = '99PERCENTILE';
CREATE INDEX example_model_example_type_idx ON caravaggio.example_model (example_type);
```

Let's create the admin user with its own auth token.

Caravaggio is ready to work as a multi-system configuration. Multiple external
systems, also called Clients, can be integrated with the API system and act 
as an independent solution with its own user management. The basic 
configuration will have one only system created: BGDS.

Create the default client of the API (external system):

```shell script
$ python manage.py createclient --email it@buildgroupai.com --name "BuildGroup Data Services Inc."
Client [932a9653-a630-4631-ab3f-d61418893d26] created successfully

$ export CLIENT_ID=932a9653-a630-4631-ab3f-d61418893d26
```

Setup the admin user, that will be also a super user of the default external system:

```shell script
$ python manage.py createsuperuser \ 
    --username ${CLIENT_ID}-xalperte@buildgroupai.com \
    --client $CLIENT_ID \ 
    --email "xalperte@buildgroupai.com" \
    --is_client_staff True \
    --first_name "Javier" \
    --last_name "Alperte" \
    --no-input

$ python manage.py changepassword ${CLIENT_ID}-xalperte@buildgroupai.com
Changing password for user '32a9653-a630-4631-ab3f-d61418893d26-xalperte@buildgroupai.com'
Password: [for instance: XXXXXXXX]
```

We can query the the postgres database to get the token (table: `authtoken_token`), or 
we can start the RESTful application and obtain the Token using the following request: 

```
$ curl -H "Content-Type: application/json" -X POST \
    -d '{"username": "32a9653-a630-4631-ab3f-d61418893d26-xalperte@buildgroupai.com", "password": "XXXXXXXX"}' \
    http://127.0.0.1:8001/api-token-auth/
    
{"token":"b10061d0b62867d0d9e3eb4a8c8cb6a068b2f14a",
 "id":"0c8d120b-c3de-4234-be68-67380d217638",
 "client_id":"32a9653-a630-4631-ab3f-d61418893d26",
 "client_name":"BuildGroup Data Services Inc.",
 "email":"xalperte@buildgroupai.com"}    
```