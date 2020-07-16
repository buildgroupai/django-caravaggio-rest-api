# Install DSE in Google Cloud Platform

This document describes how to install DataStax Enterprise in production.

## Sources

1. [Github project with DSE Deployment Scripts](https://github.com/DSPN/google-compute-engine-dse)

We are going to details how to install a local DSE cluster in production.

## Initial Requirements

Before deploy DSE in production we will need to have the following information at hand:

- GCP Project Name: `<PROJECT_NAME>`
- The deployment name: `<DEPLOYMENT_NAME>`. Ex. `buildgroupai-dse`
- The zones where we want to deploy the cluster nodes: `<GCP_NODES_ZONE_1>`, `<GCP_NODES_ZONE_2>`. Ex: `europe-west1-b`, `europe-west1-c`, `us-east1-b`, `us-east1-c`.
- The zone where we want to deploy the OpsCenter: `<GCP_OPSCENTER_ZONE>`. Ex: `europe-west1-b`
- The number of nodes that we want per zone: `<NODES_PER_ZONE>`. Ex. `4`
- The GCP machine type to use for the nodes and OpsCenter: `<GCP_INSTANCE_TYPE>`. Ex. `n1-highmem-4`.
- The size of the SSD Disk for the Nodes data: `<GCP_NODES_DISK_SIZE>`. Ex. `256`.
- The password for the `cassandra` user (needed to connect to Cassandra and Solr): `<CASSANDRA_PASS>` 
- The password fof the OpsCenter `admin` user: `<OPSCENTER_PASS>`.
- The version of DSE we want to deploy: `<DSE_VERSION>`. Ex. `6.7.0`.
- The user and password of your account at DataStax: `<DSA_USERNAME>`, `<DSA_PASSWORD>`.

## Deployment

We are going to use the scripts available in this [Github project](https://github.com/DSPN/google-compute-engine-dse).

1. First we set the default project to `<PROJECT_NAME>`, that `gcloud` will use with the command. 

    ```
    $ gcloud config set project <PROJECT_NAME>
    ```
    
2. Clone the github project.

    ```
    $ git clone https://github.com/DSPN/google-compute-engine-dse.git
    $ cd google-compute-engine-dse
    ```

3. Edit the `clusterParameters.yaml` file to configure the cluster. 

    ```
    $ vi clusterParameters.yaml
     
    imports:
    - path: datastax.py

    resources:
    - name: datastax
      type: datastax.py
      properties:
        zones:
        - <GCP_NODES_ZONE_1>
        - <GCP_NODES_ZONE_2>
        machineType: <GCP_INSTANCE_TYPE>
        nodesPerZone: <NODES_PER_ZONE>
        dataDiskType: pd-ssd
        diskSize: <GCP_NODES_DISK_SIZE>
        opsCenterZone: <GCP_OPSCENTER_ZONE>
        dseVersion: <DSE_VERSION>
        cassandraPwd: <CASSANDRA_PASS>
        dsa_username: <DSA_USERNAME>
        dsa_password: <DSA_PASSWORD>
        opsCenterAdminPwd: <OPSCENTER_PASS>
    ~                                                                                                                                                                                                         
    ~                                                                                                                                                                                                         
    ~                                                                                                                                                                                                         
    ~                                                                                                                                                                                                         
    "clusterParameters.yaml" 21L, 443C
    ```

    For development you can use the google credentials for __DataStax Account__. In this case, we could be restricted to older DSE versions, for instance: `6.0.0`:
      - dsa_username: datastax@google.com
      - dsa_password: 8GdeeVT2s7zi
      
4. Once the cluster is configured, we can start the deployment.

    ```
    $ ./deploy.sh <DEPLOYMENT_NAME>
    ```
    
    At this point, the physical resources on GCE have all provisioned. DataStax Enterprise OpsCenter LifeCycle Manager (LCM) will continue provisioning DSE nodes. That will typically take additional 20 minutes or more to deploy a 9-node DSE cluster spanning 3 GCE zones. The actual deployment time is subject to the size of your cluster.


## Inspect the cluster

To view OpsCenter, the DataStax admin interface, we will need to create an ssh tunnel. To do that, open a terminal on your local machine and run the command:

```
gcloud compute ssh --ssh-flag=-L8443:localhost:8443 --project=<PROJECT_NAME> --zone=<GCP_OPSCENTER_ZONE> <DEPLOYMENT_NAME>-opscenter-vm 
```

Now, we can open a web browser to [https://localhost:8443](https://localhost:8443) and log into OpsCenter using "admin" as Username and the value of `opsCenterAdminPwd` in `clusterParameters.yaml` as Password.


## Access the cluster from the local system

Data that we need to gather to setup the configuration:

- The <CASSANDRA_PASS> (it's also available at the details section of the OpsCenter VM instance. Parameter: cassandra_user_pwd)
- For each node in the DSE Cluster:
    - Its internal IP (ex. 10.154.0.1, 10.154.0.2,..., 10.154.0.16)
    - Its instance name (ex. buildgroupai-datastax-europe-west2-a-1-vm)

__NOTE__: The Internal IPs will be different for you, and could not be a perfect sequence. It will depends in the zones you are using and if you already have other instances started in your project. 

We define a new local network interfaces for each node in the cluster, using its internal IP addresses:

```
$ sudo ifconfig lo0 alias 10.154.0.1
$ sudo ifconfig lo0 alias 10.154.0.2
...
...
$ sudo ifconfig lo0 alias 10.154.0.16
``` 

We create a ssh tunneling to all nodes in the cluster:

```
$ gcloud compute ssh --ssh-flag="-L10.154.0.1:9042:10.154.0.1:9042 -L10.154.0.1:8983:10.154.0.1:8983" --project=<PROJECT_NAME> --zone=europe-west2-b buildgroupai-dse-europe-west2-b-1-vm
$ gcloud compute ssh --ssh-flag="-L10.154.0.2:9042:10.154.0.2:9042 -L10.154.0.2:8983:10.154.0.2:8983" --project=<PROJECT_NAME> --zone=europe-west2-b buildgroupai-dse-europe-west2-b-2-vm
$ gcloud compute ssh --ssh-flag="-L10.154.0.3:9042:10.154.0.3:9042 -L10.154.0.3:8983:10.154.0.3:8983" --project=<PROJECT_NAME> --zone=europe-west2-b buildgroupai-dse-europe-west2-b-3-vm
...
...
$ gcloud compute ssh --ssh-flag="-L10.154.0.14:9042:10.154.0.14:9042 -L10.154.0.14:8983:10.154.0.14:8983" --project=<PROJECT_NAME> --zone=us-east1-c buildgroupai-dse-us-east1-c-1-vm
$ gcloud compute ssh --ssh-flag="-L10.154.0.15:9042:10.154.0.15:9042 -L10.154.0.15:8983:10.154.0.15:8983" --project=<PROJECT_NAME> --zone=us-east1-c buildgroupai-dse-us-east1-c-2-vm
$ gcloud compute ssh --ssh-flag="-L10.154.0.16:9042:10.154.0.16:9042 -L10.154.0.16:8983:10.154.0.16:8983" --project=<PROJECT_NAME> --zone=us-east1-c buildgroupai-dse-us-east1-c-3-vm
```

At this point we can start up cqlsh, the command line interface to DataStax Enterprise:

```
$ cqlsh -u cassandra -p <CASSANDRA_PASS>
```


## Delete the deployment

Deployments can be deleted via the command line or the web UI. To use the command line type the command:

```
$ gcloud deployment-manager deployments delete <DEPLOYMENT_NAME>
```


## Configure your local project

Now we can configure our local project to connect to the production database instead the local one.

For instance, in case you are using a `dango-caravaggio-rest-api` based Django aplication, you can define the following environment variables:

```
export CASSANDRA_DB_HOST=10.154.0.1,10.154.0.2,10.154.0.3,.....,10.154.0.15,10.154.0.16
export CASSANDRA_DB_USER=cassandra
export CASSANDRA_DB_PASSWORD=<CASSANDRA_PASS>
export CASSANDRA_DB_STRATEGY=SimpleStrategy
export CASSANDRA_DB_REPLICATION=3
``` 

And now we can populate the database:

```
$ python manage.py sync_cassandra
$ python manage.py sync_indexes
```


## SSH Tunnel for third-party connectors

First, we need to make sure our instances or to our entire project have the metadata `enable-oslogin=TRUE`:

```
gcloud compute project-info add-metadata --metadata enable-oslogin=TRUE
```

or, if the instance exists

```
gcloud compute instances add-metadata [INSTANCE_NAME] --metadata enable-oslogin=TRUE
```

if the instance don't exists

```
gcloud compute instances create [INSTANCE_NAME] --metadata enable-oslogin=TRUE
```

Once we have our instances configured and ready, we can create our SSH private key.

```
ssh-keygen -t rsa -b 4096 -C "username@buildgroupai.com"
```

This creates a new ssh key, using the provided email as a label. We should give an specific name to the key files, for instance: 

```
Enter a file in which to save the key (/Users/you/.ssh/id_rsa): /Users/you/.ssh/[FILE_NAME]
```

Now it's time to upload our key to GCP and associate it to our Project-SSH Keys:

```
gcloud compute os-login ssh-keys add --project [PROJECT_NAME] \
    --key-file [KEY_FILE_PATH] \
    --ttl [EXPIRE_TIME]
```

where:

- [PROJECT_NAME] is the GCP project we want to register our SSH Key in.
- [KEY_FILE_PATH] is the path to the public SSH key on your local workstation. Ensure that the public SSH key is properly formatted. If you use PuTTYgen on Linux systems to generate your public keys, you must use the public-openssh format.
- [EXPIRE_TIME] is an optional flag to set an expiration time for the public SSH key. For example, you can specify 30m and the SSH key will expire after 30 minutes. Valid units for this flag are s for seconds, m for minutes, h for hours, or d for days. You can set the value to 0 to indicate no expiration time.

After you add your keys to your account, you can connect to instances using third-party tools and the username associated with your account:

```
gcloud compute os-login describe-profile

name: [ACCOUNT_EMAIL]
posixAccounts:
.
.
.
    username: [USER_NAME]
.
.
.
```

where:

- [ACCOUNT_EMAIL] is the email address that represents your managed user account.
- [USER_NAME] is the username for establishing SSH connections. By default, this is generated from your [ACCOUNT_EMAIL].


Now we can connect using the following syntax:

```
$ ssh -i /Users/you/.ssh/[FILE_NAME] [USER_NAME]@[HOST IP or NAME]


Welcome to Ubuntu 16.04.5 LTS (GNU/Linux 4.15.0-1017-gcp x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  Get cloud support with Ubuntu Advantage Cloud Guest:
    http://www.ubuntu.com/business/services/cloud

68 packages can be updated.
0 updates are security updates.

New release '18.04.1 LTS' available.
Run 'do-release-upgrade' to upgrade to it.


*** System restart required ***
Last login: Wed Feb 13 09:49:36 2019 from 95.19.55.120
groups: cannot find name for group ID 1288167292
xxxxxxxxxx@gasp-datastax-europe-west2-a-1-vm:~$ 
```

Once inside we can use the Cqlsh client

```
xxxxxxxxxx@gasp-datastax-europe-west2-a-1-vm:~$ cqlsh -u cassandra -p [CASSANDRA_PASSWORD]
```

where

- SSH private key file: __[FILE_NAME]__
- SSH Username: __[USER_NAME]__
- Hostname: __[HOST IP or NAME]
- DB Username: __cassandra__
- DB Password: __[CASSANDRA_PASSWORD]__ -> Should be informed in the DSE OpsCenter instance


### Example of tunneling a Cqlsh session:

- First we open a tunneling to the 9042 port using a terminal session

```
$ ssh -i /Users/you/.ssh/[FILE_NAME] [USER_NAME]@[HOST IP or NAME] -L 127.0.0.1:9042:127.0.0.1:9042 -N
```
  
- We open a new terminal session and type the following instruction (we need to have the `cqlsh` program in the `PATH`)
  
```
$ cqlsh -u cassandra -p [CASSANDRA_PASSWORD] localhost 9042

Connected to clusters-datastax at localhost:9042.
[cqlsh 5.0.1 | DSE 6.0.0 | CQL spec 3.4.5 | DSE protocol v2]
Use HELP for help.
cassandra@cqlsh> 
```

where  
  
- SSH private key file: __[FILE_NAME]__
- SSH Username: __[USER_NAME]__
- Hostname: __[HOST IP or NAME]
- DB Username: __cassandra__
- DB Password: __[CASSANDRA_PASSWORD]__ -> Should be informed in the DSE OpsCenter instance
- DB name: __[DB_NAME]__ -> for instance "bovespa"
- DB port: __9042__
