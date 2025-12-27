#!/usr/bin/env bash
set -eu

COMPOSER_ENV="chrom-batch-airflow"
LOCAL_DBT_DIR="${CHROM_STREAM_HOME}/dbt/chrom_stream"
LOCAL_DAGS_DIR="${CHROM_STREAM_HOME}/dbt/dags"

echo "Finding Composer GCS bucket..."

COMPOSER_BUCKET=$(gcloud composer environments describe "${COMPOSER_ENV}" \
  --location "${GCP_REGION}" \
  --project "${GCP_PROJECT_ID}" \
  --format="value(config.dagGcsPrefix)")

if [[ -z "${COMPOSER_BUCKET}" ]]; then
  echo "Failed to locate Composer GCS bucket"
  exit 1
fi

echo "Composer DAG bucket: ${COMPOSER_BUCKET}"

echo "Deploying airflow dags to Composer..."

gsutil -m rsync -r -d \
  "${LOCAL_DAGS_DIR}" \
  "${COMPOSER_BUCKET}"

echo "Deploying dbt files to Composer..."

gsutil -m rsync -r -d \
  "${LOCAL_DBT_DIR}" \
  "${COMPOSER_BUCKET}/dbt"

echo "dbt project deployed successfully"
