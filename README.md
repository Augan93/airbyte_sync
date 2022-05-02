# airbyte_sync
A combination of Docker and scripts to fully automate Airbyte pre-configured data sync

## How to run
- If running on EC2, use `Amazon Linux 2 AMI (HVM) - Kernel 5.10, SSD Volume Type` image with t2.medium instance type and 30GB of disk space.
  Instance type and disk space is what Airbyte recommends. The scripts will probably run on other image types as well, but you need to make sure that bash and `envsubst` are available.
- Install Docker and docker-compose (see https://docs.airbyte.com/deploying-airbyte/on-aws-ec2#install-environment as an example)
- Download this repo
- Create config.yml to configure Github org/repository and BigQuery project and dataset ids (you can use sample_config.yml as an example)
- In one shell:
```shell
cd airbyte_sync
docker-compose up
```
  wait until the server is started on port 8000 (there will be fancy ascii art)

- In the other shell:
```shell
export GITHUB_PERSONAL_ACCESS_TOKEN=<your Github PAK>
export GCP_CREDENTIALS_JSON='<json auth file for GCP system account>'
cd airbyte_sync
bash ./configure_connection.sh config.yml
```
Once it finishes, run
```shell
bash ./sync_data.sh
```
It'll kick off data sync. Data sync may take a while - watch the logs in the docker-compose to see the progress.
