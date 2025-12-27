import requests
import os
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
from google.cloud import secretmanager

DBT_DIR = "/home/airflow/gcs/dags/dbt"
PROFILE_DIR = "/home/airflow/.dbt"
GCP_PROJECT_ID = os.environ['GCP_PROJECT_ID']
SNOWFLAKE_ACCOUNT = os.environ["SNOWFLAKE_ACCOUNT"]
SNOWFLAKE_USER = os.environ["SNOWFLAKE_USER"]
SNOWFLAKE_ROLE = os.environ["SNOWFLAKE_ROLE"]
SNOWFLAKE_DATABASE = os.environ["SNOWFLAKE_DATABASE"]
SNOWFLAKE_WAREHOUSE = os.environ["SNOWFLAKE_WAREHOUSE"]
SNOWFLAKE_ORGANIZATION = os.environ["SNOWFLAKE_ORGANIZATION"]

def fetch_token(**context):

    def load_secret(name):
        client = secretmanager.SecretManagerServiceClient()
        path = f"projects/{GCP_PROJECT_ID}/secrets/{name}/versions/latest"
        return client.access_secret_version(name=path).payload.data.decode()

    client_id = load_secret("SNOWFLAKE_OAUTH_CLIENT")
    client_secret = load_secret("SNOWFLAKE_OAUTH_SECRET")

    url = f"https://{SNOWFLAKE_ORGANIZATION}-{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/oauth/token-request"

    payload = {
        "grant_type": "password",
        "username": SNOWFLAKE_USER,
        "password": "",
        "scope": f"session:role:{SNOWFLAKE_ROLE}",
    }

    response = requests.post(url, auth=(client_id, client_secret), data=payload)
    response.raise_for_status()

    token = response.json()["access_token"]
    context["ti"].xcom_push(key="sf_token", value=token)


default_args = {
    "owner": "data",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval="*/15 * * * *",
    catchup=False,
    max_active_runs=1,
) as dag:

    fetch_sf_token = PythonOperator(
        task_id="fetch_sf_token",
        python_callable=fetch_token,
        provide_context=True,
    )

    create_profiles = BashOperator(
        task_id="create_dbt_profile",
        bash_command=f"""
        mkdir -p /home/airflow/.dbt

        cat <<'EOF' > /home/airflow/.dbt/profiles.yml
chrom_stream:
    target: prod
    outputs:
        prod:
            type: snowflake
            account: {SNOWFLAKE_ORGANIZATION}-{SNOWFLAKE_ACCOUNT}
            user: {SNOWFLAKE_USER}
            authenticator: oauth
            token: "{{ '{{' }} env_var('SNOWFLAKE_OAUTH_TOKEN') {{ '}}' }}"
            role: {SNOWFLAKE_ROLE}
            database: {SNOWFLAKE_DATABASE}
            warehouse: {SNOWFLAKE_WAREHOUSE}
            schema: test_schema
            threads: 2

EOF
        """
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && dbt deps",
        env={
            "HOME": "/home/airflow",
        }
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --fail-fast",
        env={
            "HOME": "/home/airflow",
            "SNOWFLAKE_OAUTH_TOKEN": "{{ ti.xcom_pull(key='sf_token', task_ids='fetch_sf_token') }}",
        },
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test",
        env={
            "HOME": "/home/airflow",
            "SNOWFLAKE_OAUTH_TOKEN": "{{ ti.xcom_pull(key='sf_token', task_ids='fetch_sf_token') }}",
        },
    )

    fetch_sf_token >> create_profiles >> dbt_deps >> dbt_run >> dbt_test
