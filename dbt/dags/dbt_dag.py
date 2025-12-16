from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

DBT_DIR = "/home/airflow/gcs/dags/dbt"
PROFILE_DIR = "/home/airflow/.dbt"

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

    create_profiles = BashOperator(
        task_id="create_dbt_profile",
        bash_command="""
        mkdir -p ~/.dbt
        cat <<EOF > ~/.dbt/profiles.yml
        my_dbt_project:
          target: prod
          outputs:
            prod:
              type: snowflake
              account: "${SNOWFALKE_ACCOUNT}"
              user: "${SNOWFLAKE_USER}"
              password: "${SNOWFLAKE_PASSWORD}"
              role: "${SNOWFLAKE_ROLE}"
              database: "${SNOWFLAKE_DATABSE}"
              warehouse: "${SNOWFLAKE_WAREHOUSE}"
              schema: analytics
              threads: 8
        EOF
        """,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && dbt deps",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --fail-fast",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test",
    )

    create_profiles >> dbt_deps >> dbt_run >> dbt_test
