# Amazon Iam Source

This is the repository for the Amazon Iam source connector, written in Python.
For information about how to use this connector within Airbyte, see [the documentation](https://docs.airbyte.io/integrations/sources/amazon-iam).

#### Building docker image for the source connector and pushing to the Dockerhub

```
cd source-amazon-iam
docker build . -t <repo_owner>/source-amazon-iam:0.1.0
docker login
docker push <repo_owner>/source-amazon-iam:0.1.0
```


## Setup the connection

#### Adding the source connector to Airbyte instance

From the root of the repo, run the following command to start airbyte instance:
```
docker-compose up
```

Next, go to: Settings -> Sources, and press the button + New connector, it will open a custom connector adding form
see [custom connector form](https://lh6.googleusercontent.com/UfEol2AKAR-7pKtJnzPNRoEDgOlEfoi9cA3SzB1NboENOZnniaJFfUGcCcVxYtzC8R97tnLwOh28Er5wS_aNujfXCSKUh0K7lhu7xUFYm4oiVCDlFdsdJNvgVihWp0u13ZNyzFuA)
1. Give the connector display name: Amazon IAM (for example)
2. Enter Docker repository name: <repo_owner>/source-amazon-iam
3. Enter Docker image tag: 0.1.0
4. Enter Connector Documentation URL
5. Press the Add button


#### Setup the source connector

After adding our connector to the airbyte instance, we need to setup for our connection.
Go to: Sources and press the button +New source
In the search input, enter Amazon IAM to find our source connector.

In the form fill out the following fields:
1. **aws_access_key_id**      - access key for IAM user
2. **aws_secret_access_key**  - secret key for IAM user
3. **organization_id**        - Organization Id
4. **root_id**                - Root Id (Root is the parent organizational unit (OU) for all accounts and other OUs in your organization)

And click on the add button.

How to get aws access keys for IAM user read [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey)

#### Connecting a destination to the source
Next click on the Add destination button and choose desired destination (BigQuery) from already configured destinations list
or setup a new destination.

After choosing the destination, select required streams to replicate.

In **Replication frequency** select **manual**.

In **Normalization & Transformation** section choose **Normalized tabular data**. 

Press the **Set up connection**


### More about BigQuery

How to setup [BigQuery destination](https://assets-global.website-files.com/6064b31ff49a2d31e0493af1/62605be93d90b81761d850ed_C-iMe0k7C-NEKAmEx5v9SoBx7dH4DG3tyAHsXPL7u5oyfoJs_AK5Rc6X8VY_qE2YKA2Uj_msaf-zyMKkxIaTrFPFsiLK7TfLNhtmnPv6o4PCSak2eFxFWiYgP_s_qXwI7xwUNhRu.png)
and [here](https://assets-global.website-files.com/6064b31ff49a2d31e0493af1/62605be8e6e7c0d4e06ce983_Oy6pBxVrhiQmZciyM6DT8QDXrK2cEfVyAkgtZmrunNPuusO6e0aQLnIOJ6ltpRD1rLZ-WGwhHIKmLwQmya8E55Kfo0uMbwVTDRSgcnNH984t5ONW-2qVFOYcH0KhDYcfpIZ_Eh2W.png)

[BigQuery destination tutorial](https://airbyte.com/tutorials/export-google-analytics-to-bigquery)


More about BigQuery destination, [read here](https://docs.airbyte.com/integrations/destinations/bigquery)
