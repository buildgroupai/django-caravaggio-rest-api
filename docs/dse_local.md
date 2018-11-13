# Getting started with Django on Google Cloud Platform on App Engine Flexible

[![Open in Cloud Shell][shell_img]][shell_link]


## Sources

1. [CCM Github project](https://github.com/riptano/ccm)
2. [CQL Solr Examples](https://docs.datastax.com/en/dse/6.0/cql/cql/cql_using/search_index/queryingCollectionSetExample.html)
3. [Install DSE with CCM](https://www.youtube.com/watch?v=A3iLRLSIIKM)

We are going to details how to install a local DSE cluster for development.

To prepare the local environment we are going to use CCM (Cassandra Cluster Management) 

This repository is an example of how to run a [Django](https://www.djangoproject.com/) 

## Prepare environment

We need to have install a compatible Java 8 interpreter.

DSE 6.0 requires Java 8 update 151 or later

```
$ brew tap caskroom/versions
$ brew cask search java
$ brew cask install java8
```

We also will install the required Python libraries in a custom/virtual environment using [Anaconda](https://www.anaconda.com).

```
$ conda create -n ccm python=2.7

$ source activate ccm
$ pip install cql
$ pip install pyyaml
```

Install the CCM package

```
$ git clone https://github.com/riptano/ccm.git
$ python setup.py install 
```

Prepare the loop networks for the 3 nodes

```
$ sudo ifconfig lo0 alias 127.0.0.2
$ sudo ifconfig lo0 alias 127.0.0.3
```

## Provision a new cluster

First of all we need to define the environment variables to inform about the DSE versions and our DataStax credentials

```
# Datastax Enterprise versio: 6.0.1
export DSE_VERSION=6.0.1

# Opscenter versio: 6.5.0
export OPSCENTER_VERSION=6.5.0

# Credentials
export DSE_USERNAME=xxxx@xxxx.com
export DSE_PASSWORD=xxxxxxx

```

The following lines will setup a DSE cluster of 3 nodes with support for Solr, Graph and Spark workloads.


```
$ ccm create -n 3 --dse --dse-username=$DSE_USERNAME --dse-password=$DSE_PASSWORD -v $DSE_VERSION -o $OPSCENTER_VERSION dse_cluster
$ ccm setworkload solr,graph,spark
$ ccm start [--verbose]
```

Check the cluster

```
$ ccm status
Cluster: 'dse_cluster'
----------------------
node1: UP
node3: UP
node2: UP
```

Open a Clqsh session

```
$ ccm node1 cqlsh
Connected to dse_cluster at 127.0.0.1:9042.
[cqlsh 5.0.1 | Cassandra 4.0.0.2284 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cqlsh> 
```

## Management of the cluster

Remove nodes

```
$ ccm node2 remove 
Cluster: 'dse_cluster'
----------------------
node1: UP
node3: UP
```

### Add nodes

To add new nodes we need to decide the loopback address we will be use, 
creating a loopback alias if needed.

That will start 2 nodes on IP 127.0.0.[2, 4] on port 9160 for thrift, 
port 7000 for the internal cluster communication and ports 7400, 7500 for JMX. 
You can check that the cluster is correctly set up with


```
$ sudo ifconfig lo0 alias 127.0.0.4
$ sudo ifconfig lo0 alias 127.0.0.5
$ ccm add --dse -i 127.0.0.4 -j 7400 -d dse_cluster node4
$ ccm add --dse -i 127.0.0.5 -j 7500 -d dse_cluster node5 
```

Set the workload of each node and start the nodes
```
$ ccm node4 setworkload solr
$ ccm node5 setworkload solr
$ ccm node4 start
$ ccm node5 start 
```

## Test the cluster - Example 1

Let's get the name of the datacenter associated to the cluster

```
$ $HOME/.ccm/dse_cluster/node1/bin/dsetool -h 127.0.0.1 -j 7100 status

DC: Solr            Workload: Search          Graph: no     
======================================================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--   Server ID          Address          Load             Owns                 Token                                        Rack         Health [0,1] 
                                                                               3074457345618258602                                                    
UN   68-A8-6D-37-28-84  127.0.0.1        87.99 KiB        ?                    -9223372036854775808                         rack1        0.10         
UN   68-A8-6D-37-28-84  127.0.0.2        84.27 KiB        ?                    -3074457345618258603                         rack1        0.10         
UN   68-A8-6D-37-28-84  127.0.0.3        137.98 KiB       ?                    3074457345618258602                          rack1        0.10         

Note: you must specify a keyspace to get ownership information.
```

We get the name: Solr

Let's open a clqsh window

```
$ ccm node1 cqlsh
Connected to dse_cluster at 127.0.0.1:9042.
[cqlsh 5.0.1 | Cassandra 4.0.0.2284 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cqlsh>
```

Create a keyspace in the datacenter

```
cqlsh> CREATE KEYSPACE mykeyspace WITH REPLICATION = {'class':'NetworkTopologyStrategy', 'Solr':1};
```

Create a table

```
cqlsh> USE mykeyspace;
cqlsh> CREATE TABLE mysolr (id text PRIMARY KEY, name text, title text, quotes set<text>);
```

Extract the [quotations.zip](quotations.zip) file, copy the insert commands, and paste each command on the cqlsh command line.

```
cqlsh> INSERT INTO mysolr (id, name, title, quotes) VALUES ('123', 'Christopher Morley', 'Life', {'Life is a foreign language; all men mispronounce it.', 'There are three ingredients in the good life: learning, earning and yearning.'});
cqlsh> INSERT INTO mysolr (id, name, title, quotes) VALUES ('124', 'Daniel Akst', 'Life', {'In matters of self-control as we shall see again and again, speed kills. But a little friction really can save lives.', 'We Have Met the Enemy: Self-Control in an Age of Excess.'});
cqlsh> INSERT INTO mysolr (id, name, title, quotes) VALUES ('125', 'Abraham Lincoln', 'Success', {'Always bear in mind that your own resolution to succeed is more important than any one thing.', 'Better to remain silent and be thought a fool than to speak out and remove all doubt.'});
cqlsh> INSERT INTO mysolr (id, name, title, quotes) VALUES ('126', 'Albert Einstein', 'Success', {'If A is success in life, then A equals x plus y plus z. Work is x; y is play; and z is keeping your mouth shut.'});
```

Create the Solr core associated to the new keyspace.table. We can do that in two ways:

1- Creating the core manually


```
$ $HOME/.ccm/dse_cluster/node1/bin/dsetool create_core mykeyspace.mysolr generateResources=true reindex=true
Please remember this operation is DC specific and should be repeated on each desired DC.
```

2- Creating an Index

```
cqlsh> CREATE SEARCH INDEX IF NOT EXISTS ON mykeyspace.mysolr;
```


If you are recreating the mykeyspace.mysolr core, use the __reload_core__ command instead of the __create_core__ command.
There is no output from this command. You can search data after indexing finishes.

We can check the Solr core accessing to [Solr Core]([http://127.0.0.1:8983/solr/#/mykeyspace.mysolr/query)

Querying the table using the browser:

```
curl 'http://127.0.0.1:8983/solr/mykeyspace.mysolr/select?q=quotes:*succ*&wt=json&indent=on&omitHeader=on'

{
  "response":{"numFound":2,"start":0,"maxScore":1.0,"docs":[
      {
        "id":"126",
        "name":"Albert Einstein",
        "title":"Success",
        "quotes":["If A is success in life, then A equals x plus y plus z. Work is x; y is play; and z is keeping your mouth shut."]},
      {
        "id":"125",
        "name":"Abraham Lincoln",
        "title":"Success",
        "quotes":["Always bear in mind that your own resolution to succeed is more important than any one thing.",
          "Better to remain silent and be thought a fool than to speak out and remove all doubt."]}]
  }}
```

Querying the table using the cqlsh terminal:

```
$ ccm node1 cqlsh
Connected to dse_cluster at 127.0.0.1:9042.
[cqlsh 5.0.1 | Cassandra 4.0.0.2284 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cqlsh> SELECT * FROM mykeyspace.mysolr WHERE solr_query='quotes:*succ*';

id  | name            | quotes                                                                                                                                                                                     | solr_query | title
-----+-----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------------+---------
 126 | Albert Einstein |                                                                        {'If A is success in life, then A equals x plus y plus z. Work is x; y is play; and z is keeping your mouth shut.'} |       null | Success
 125 | Abraham Lincoln | {'Always bear in mind that your own resolution to succeed is more important than any one thing.', 'Better to remain silent and be thought a fool than to speak out and remove all doubt.'} |       null | Success

(2 rows)
```

## Test the cluster - Example 2

Let's do something similar but creating the solr core using a cql INDEX sentence.

Create the table:

```
$ ccm node1 cqlsh
Connected to dse_cluster at 127.0.0.1:9042.
[cqlsh 5.0.1 | Cassandra 4.0.0.2284 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cqlsh> USE mykeyspace;
cqlsh> CREATE TABLE taxi_trips(id int PRIMARY KEY, pickup_dropoff_range 'DateRangeType');
cqlsh> CREATE TABLE weather_sensors(weatherstation_id text, event_time 'DateRangeType', temperature text, PRIMARY KEY (weatherstation_id,event_time));
```

Insert data:

```
cqlsh> INSERT INTO taxi_trips(id, pickup_dropoff_range) VALUES (1, '[2017-02-02T14:57:00 TO 2017-02-02T15:10:17]');
cqlsh> INSERT INTO taxi_trips(id, pickup_dropoff_range) VALUES (2, '[2017-02-01T09:00:03 TO 2017-02-01T09:32:00.001]');
cqlsh> INSERT INTO taxi_trips(id, pickup_dropoff_range) VALUES (3, '[2017-02-03T12:10:01.358 TO 2017-02-03T12:19:57]');
```

Check the table contents

```
cqlsh> SELECT * FROM taxi_trips;

 id | pickup_dropoff_range
----+----------------------------------------------------
  1 |     [2017-02-02T14:57:00Z TO 2017-02-02T15:10:17Z]
  2 | [2017-02-01T09:00:03Z TO 2017-02-01T09:32:00.001Z]
  3 | [2017-02-03T12:10:01.358Z TO 2017-02-03T12:19:57Z]

(3 rows)
```

Create search index:

```
cqlsh> CREATE SEARCH INDEX ON taxi_trips ;
```

Select all trips from February 2017:

```
cqlsh> SELECT * FROM taxi_trips WHERE solr_query = 'pickup_dropoff_range:2017-02';

id | pickup_dropoff_range                               | solr_query
----+----------------------------------------------------+------------
  3 | [2017-02-03T12:10:01.358Z TO 2017-02-03T12:19:57Z] |       null
  1 |     [2017-02-02T14:57:00Z TO 2017-02-02T15:10:17Z] |       null
  2 | [2017-02-01T09:00:03Z TO 2017-02-01T09:32:00.001Z] |       null

(3 rows)
```

Select all trips started after 2017-02-01 12:00 PM (inclusive) and ended before 2017-02-02 (inclusive):

```
cqlsh> SELECT * FROM taxi_trips WHERE solr_query = 'pickup_dropoff_range:[2017-02-01T12 TO 2017-02-02]';

 id | pickup_dropoff_range                           | solr_query
----+------------------------------------------------+------------
  1 | [2017-02-02T14:57:00Z TO 2017-02-02T15:10:17Z] |       null

(1 rows)
```

Select all trips started after 2017-02-01 9:00 AM (inclusive) and ended before 2017-02-01:23:59:59.999 (inclusive):

```
cqlsh> SELECT * FROM taxi_trips WHERE solr_query = 'pickup_dropoff_range:[2017-02-01T09 TO 2017-02-01]';

 id | pickup_dropoff_range                               | solr_query
----+----------------------------------------------------+------------
  2 | [2017-02-01T09:00:03Z TO 2017-02-01T09:32:00.001Z] |       null

(1 rows)
```

DateRangeField can represent a single point in time:

```
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '2017-10-02T00:00:05', '12C');
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '2017-10-02T00:00:10', '12C');
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '2017-10-02T00:00:15', '13C');
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '2017-10-02T00:00:20', '13C');
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '2017-10-02T00:00:25', '12C');
```

Select all from weather_sensors:

```
cqlsh> SELECT * FROM weather_sensors;


 weatherstation_id | event_time           | temperature
-------------------+----------------------+-------------
                A1 | 2017-10-02T00:00:05Z |         12C
                A1 | 2017-10-02T00:00:10Z |         12C
                A1 | 2017-10-02T00:00:15Z |         13C
                A1 | 2017-10-02T00:00:20Z |         13C
                A1 | 2017-10-02T00:00:25Z |         12C

(5 rows)
```

Create a search index on weather_sensors:

```
cqlsh> CREATE SEARCH INDEX ON weather_sensors ;
```

Select a specific point in time:

```
cqlsh> SELECT * FROM weather_sensors WHERE solr_query = 'event_time:[2017-10-02T00:00:10 TO 2017-10-02T00:00:20]';

weatherstation_id | event_time           | solr_query | temperature
-------------------+----------------------+------------+-------------
                A1 | 2017-10-02T00:00:25Z |       null |         12C
                A1 | 2017-10-02T00:00:10Z |       null |         12C
                A1 | 2017-10-02T00:00:15Z |       null |         13C
                A1 | 2017-10-02T00:00:20Z |       null |         13C

(4 rows)
```

Select from an open bound up to a point in time:

```
cqlsh> SELECT * FROM weather_sensors WHERE solr_query = 'event_time:[* TO 2017-10-02T00:00:15]';

 weatherstation_id | event_time           | solr_query | temperature
-------------------+----------------------+------------+-------------
                A1 | 2017-10-02T00:00:05Z |       null |         12C
                A1 | 2017-10-02T00:00:10Z |       null |         12C
                A1 | 2017-10-02T00:00:15Z |       null |         13C

(4 rows)
```

Select from all points in time:

```
cqlsh> SELECT * FROM weather_sensors WHERE solr_query = 'event_time:[* TO *]';


 weatherstation_id | event_time           | solr_query | temperature
-------------------+----------------------+------------+-------------
                A1 | 2017-10-02T00:00:05Z |       null |         12C
                A1 | 2017-10-02T00:00:10Z |       null |         12C
                A1 | 2017-10-02T00:00:15Z |       null |         13C
                A1 | 2017-10-02T00:00:20Z |       null |         13C
                A1 | 2017-10-02T00:00:25Z |       null |         12C

(5 rows)
```

Insert an open-bounded range into a table:

```
cqlsh> INSERT INTO weather_sensors (weatherstation_id, event_time, temperature) VALUES ('A1', '[2017-10-02T00:00:30 TO *]', '12C');
cqlsh> SELECT * FROM weather_sensors WHERE solr_query = 'event_time:[* TO *]';

 weatherstation_id | event_time                  | solr_query | temperature
-------------------+-----------------------------+------------+-------------
                A1 |        2017-10-02T00:00:05Z |       null |         12C
                A1 |        2017-10-02T00:00:10Z |       null |         12C
                A1 |        2017-10-02T00:00:15Z |       null |         13C
                A1 |        2017-10-02T00:00:20Z |       null |         13C
                A1 |        2017-10-02T00:00:25Z |       null |         12C
                A1 | [2017-10-02T00:00:25Z TO *] |       null |         12C

(6 rows)
```


## Troubleshooting

### Write timeout

Exception we get from the driver:

```
dse.WriteTimeout: Error from server: code=1100 [Coordinator node timed out waiting for replica nodes' responses] message="Operation timed out - received only 0 responses." info={'consistency': 'LOCAL_ONE', 'required_responses': 1, 'received_responses': 0, 'write_type': 'SIMPLE'}
```

This indicates that the replicas failed to respond to the coordinator node before the configured timeout. This timeout is configured in `cassandra.yaml` with the `write_request_timeout_in_ms` option.

If we depoyed a 3 nodes server, we should execute the following instructions to set a timeout of 10000:

```
sed -i -E "s/write_request_timeout_in_ms:.*[0-9]*/write_request_timeout_in_ms: 15000/g" $HOME/.ccm/dse_cluster/node1/resources/cassandra/conf/cassandra.yaml

sed -i -E "s/write_request_timeout_in_ms:.*[0-9]*/write_request_timeout_in_ms: 15000/g" $HOME/.ccm/dse_cluster/node2/resources/cassandra/conf/cassandra.yaml

sed -i -E "s/write_request_timeout_in_ms:.*[0-9]*/write_request_timeout_in_ms: 15000/g" $HOME/.ccm/dse_cluster/node3/resources/cassandra/conf/cassandra.yaml
```
