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

```
$ docker run --name caravaggio-db -e POSTGRES_PASSWORD=mysecretpassword -p 6543:5432 -d postgres:9.6
``` 


Activate the extensions:

```
$ docker run -it --rm --link caravaggio-db:postgres postgres:9.6 psql -h postgres -U postgres
Password for user postgres: 
psql (9.6.1)
Type "help" for help.

postgres= \c template1;
postgres= CREATE EXTENSION IF NOT EXISTS plpgsql;
postgres= CREATE EXTENSION IF NOT EXISTS hstore;
postgres= \dx 
 hstore  | 1.4     | public     | data type for storing sets of (key, value) pairs
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
```


Create the database (Gives rights to create databases - for the tests)

```
postgres= CREATE ROLE caravaggio WITH LOGIN PASSWORD 'caravaggio';
postgres= CREATE DATABASE caravaggio WITH OWNER caravaggio ENCODING 'UTF8' TEMPLATE template1;
postgres= ALTER USER caravaggio WITH SUPERUSER;
postgres= \q 
```

Let's test the caravaggio user:

```
$ docker run -it --rm --link caravaggio-db:postgres postgres:9.6 psql -h postgres -U caravaggio
Password for user caravaggio: 
```

### Redis 3 server

Now we start the redis server

```
$ docker run --name caravaggio-redis -p 6379:6379 -d redis:3.0
```

Test the server connection

```
$ docker run -it --rm --link caravaggio-redis:redis redis:3.0 redis-cli -h redis
redis:6379> get test
(nil)
redis:6379> quit
```

### DataStax Enterprise server

To install DataStax Enterprise in local we need to follow these instructions: [DSE Local](dse_local.md)

Once installed, we will need to create the database.

First we get the Datacenter name:

```
$ ccm node1 dsetool status
DC: SearchGraph     Workload: Search          Graph: yes    
=======================================================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--   Server ID          Address          Load             Owns                 Token                                        Rack         Health [0,1] 
                                                                               3074457345618258602                                                    
UN   68-A8-6D-37-28-84  127.0.0.1        322.98 KiB       ?                    -9223372036854775808                         rack1        0.80         
UN   68-A8-6D-37-28-84  127.0.0.2        312.34 KiB       ?                    -3074457345618258603                         rack1        0.80         
UN   68-A8-6D-37-28-84  127.0.0.3        328.6 KiB        ?                    3074457345618258602                          rack1        0.80         

Note: you must specify a keyspace to get ownership information.
```

Then we can create the database on the DC:

```
$ ccm node1 cqlsh
Connected to dse_cluster at 127.0.0.1:9042.
[cqlsh 5.0.1 | Cassandra 4.0.0.2284 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cqlsh> CREATE KEYSPACE caravaggio WITH REPLICATION = {'class':'NetworkTopologyStrategy', 'SearchGraph':1};
cqlsh> exit
```

## Run application with development server

First we need to populate the databases, the default and the DSE databases.

```
$ python manage.py migrate

Operations to perform:
  Apply all migrations: admin, auth, authtoken, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying authtoken.0001_initial... OK
  Applying authtoken.0002_auto_20160226_1747... OK  
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
  Applying sites.0001_initial... OK
  Applying sites.0002_alter_domain_unique... OK
  Applying sessions.0001_initial... OK
```

Now we can create the DSE model

```
$ python manage.py sync_cassandra

Creating keyspace caravaggio [CONNECTION cassandra] ..
Syncing example.models.ExampleModel
```

We can check if everything has been created well:

```
$ ccm node1 cqlsh

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

Let's create the admin user with its own auth token

```
$ python manage.py createsuperuser --username _caravaggio --email javier.alperte@gmail.com --noinput
$ python manage.py changepassword _caravaggio
Changing password for user '_caravaggio'
Password: 
```

A token will be created automatically for the user. We can get it back using the following request:

```
$ curl -H "Content-Type: application/json" -X POST \
    -d '{"username": "_caravaggio", "password": "MY_PASSWORD"}' \
    http://127.0.0.1:8001/api-token-auth/
    
{"token":"b10061d0b62867d0d9e3eb4a8c8cb6a068b2f14a","user_id":1,"email":"javier.alperte@gmail.com"}    
```