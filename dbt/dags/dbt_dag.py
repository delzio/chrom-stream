from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret
from kubernetes.client import models as k8s

import os
from datetime import datetime, timedelta

# Kubernetes secret volume
sf_key_file = Secret(
    deploy_type="volume",
    deploy_target="/secrets",
    secret="sf-secrets",
    key="sf-private-key",
)

sf_passphrase = Secret(
    deploy_type="env",
    deploy_target="SF_PRIVATE_KEY_PASSPHRASE",
    secret="sf-secrets",
    key="sf-private-key-passphrase",
)

# Collect environment variables at task runtime
def get_env_vars() -> dict:
    dbt_env = {
        "SF_ORGANIZATION": os.environ["SF_ORGANIZATION"],
        "SF_ACCOUNT": os.environ["SF_ACCOUNT"],
        "SF_SCHEMA": "test_schema",
        "SF_DATABASE": "chrom_stream_db",
        "SF_WAREHOUSE": "chrom_stream_wh",
        "SF_USER": os.environ["SF_USER"],
        "SF_ROLE": os.environ["SF_ROLE"],
        "SF_PRIVATE_KEY_PATH": "/secrets/sf-private-key"
    }
    return dbt_env

def get_image() -> str:
    return f'{os.environ["DBT_IMAGE"]}:latest'

# DAG setup
default_args = {
    "owner": "chrom",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="chrom_dbt_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="*/15 * * * *",
    catchup=False,
    tags=["dbt", "snowflake"]
) as dag:

    dbt_silver = KubernetesPodOperator(
        task_id="dbt_silver",
        name="dbt-silver",
        image=get_image(),
        cmds=["dbt"],
        arguments=["run", "--select", "tag:silver"],
        env_vars=get_env_vars(),
        secrets=[sf_key_file, sf_passphrase],
        get_logs=True,
        is_delete_operator_pod=True,
    )

    dbt_gold = KubernetesPodOperator(
        task_id="dbt_gold",
        name="dbt-gold",
        image=get_image(),
        cmds=["dbt"],
        arguments=["run", "--select", "tag:gold"],
        env_vars=get_env_vars(),
        secrets=[sf_key_file, sf_passphrase],
        get_logs=True,
        is_delete_operator_pod=True,
    )

    dbt_tests = KubernetesPodOperator(
        task_id="dbt_tests",
        name="dbt-tests",
        image=get_image(),
        cmds=["dbt"],
        arguments=["test"],
        env_vars=get_env_vars(),
        secrets=[sf_key_file, sf_passphrase],
        get_logs=True,
        is_delete_operator_pod=True,
    )

    dbt_silver >> dbt_gold >> dbt_tests
