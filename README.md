# Background
This is a personal project created to develop skills with Snowflake, DBT and data streaming applied to the field of biotechnology. Google Cloud Platform services, Snowflake, InfluxDB, DBT, and Grafana are used together to collect, store, process, and visualize chromatography data and analyze live trend results against historic runs. This is a small project that uses a local python project to simulate chromatography trend, sample, and batch history data generation. The technologies used in this project were chosen because they are industry-leading in the field of data engineering and are designed for scalability. The intention behind this project was to demonstrate how these technologies can be applied to a real world biopharmaceutical use case and generate value for business stakeholders. 

# Data Flow Diagram
<image>

# Results
<video>

# Instructions to Recreate

## Create accounts:
1. Google Cloud Platform (free trial)
2. Snowflake (free trial)
3. InfluxDB (free tier)
4. Grafana Cloud (free trial)

## Initialize GCP APIs and Service Accounts:
1. Enable the following APIs:
- IAM API
- Service Management API
- Cloud Storage API
- Compute Engine API
- Artifact Registry API
- Container Registry API
- CloudBuild API
- Eventarc API
- CloudComposer API
- Cloud Pub/Sub API
- Cloud Resource Manager API
- Kubernetes Engine API
2. Create Service Account and grant the following roles:
- Storage Admin
- Service Account Admin
- Service Account User
- Pub/Sub Admin
- Project IAM Admin
- Composer Administrator
- Cloud Run Admin
- Artifact Registry Administrator
3. Create a key for your service account and store the credentials json in .google/credentials
"""bash
# from project home:
mkdir .google
mkdir .google/credentials
cd .google/credentials
# move your json key here and rename to gcp.json
"""

## Initialize Snowflake Service Accounts:
1. Generate snowflake service account key pairs
"""bash
# from project home:
mkdir .snowflake
mkdir .snowflake/credentials
cd .snowflake/credentials
"""
"""bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out snowflake_tf_key.p8
openssl rsa -in snowflake_tf_key.p8 -pubout -out snowflake_tf_key.pub
"""
"""bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -v2 aes-256-cbc -inform PEM -out snowflake_dbt_key.p8
openssl rsa -in snowflake_dbt_key.p8 -pubout -out snowflake_dbt_key.pub
"""
"""bash
openssl genrsa -out snowflake_gfna_key.pem 2048
openssl rsa -in snowflake_gfna_key.pem -pubout -out snowflake_gfna_key.pub
"""
2. Create terraform_srvc_account and assign public key
3. Create dbt_srvc_account and assign public key
4. Create grafana_srvc_account and assign public key

## Build resources:
1. update .env_example, rename to .env and source .env
2. apply artifactrepo terraform
"""bash
# from project home
cd terraform/artifactrepo
terraform init
terraform apply
"""
3. deploy gcs_consumer image
"""bash
# from project home
bash gcp_cloud_run/gcs_consumer/deploy_image.sh
"""
4. deploy influx_consumer image
"""bash
# from project home
bash gcp_cloud_run/influx_consumer/deploy_image.sh
"""
5. deploy dbt_docker image
"""bash
# from project home
bash dbt/dbt_docker/deploy_image.sh
"""
6. apply infra terraform
"""bash
# from project home
cd terraform/infra
terraform init
terraform apply
"""
7. build composer dbt secrets and deploy dags
"""bash
# from project home
bash dbt/build_secrets.sh
bash dbt/deploy_dbt_dags.sh
"""

## Start Data Generation:
1. Set data generation parameters if you want to change anything byt editing python_data_generation/src/config.yml
2. run src/main.py with config.yml
"""bash
# from project home
cd python_data_generation
PYTHONPATH=src python src/main.py --config src/config.yml
"""

## Visualize Data:
1. Data will start being streamed to InfluxDB and processed in batch from Google Cloud Storage through Snowflake tables via DBT
2. Connect to Snowflake and InfluxDB with Grafana and generate dashboards
3. The example dashboard in (ref: Results) was created using the queries in the grafana/ folder

