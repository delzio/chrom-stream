#!/usr/bin/env bash
set -eu

SF_PRIVATE_KEY="${CHROM_STREAM_HOME}/.snowflake/credentials/snowflake_dbt_key.p8"

TEMPLATE="${CHROM_STREAM_HOME}/dbt/sf-secrets.yaml.template"
OUTPUT="${CHROM_STREAM_HOME}/dbt/sf-secrets.yaml"

echo "Generating snowflake secrets config file from template..."

BASE64_KEY=$(base64 -w 0 "${SF_PRIVATE_KEY}")
BASE64_PASSPHRASE=$(printf "%s" "${SF_PRIVATE_KEY_PASSPHRASE}" | base64 -w 0)

sed \
  -e "s|__BASE64_PRIVATE_KEY__|${BASE64_KEY}|g" \
  -e "s|__BASE64_KEY_PASSPHRASE__|${BASE64_PASSPHRASE}|g" \
  "$TEMPLATE" > "$OUTPUT"

echo "Generated $OUTPUT"

echo "Creating kubernetes secret in composer environment..."

if gcloud beta composer environments user-workloads-secrets list \
    --environment chrom-batch-airflow \
    --location "${GCP_REGION}" \
    --format="value(name)" | grep -qx "sf-secrets"; then

    echo "Existing secret found. Deleting..."
    
    gcloud beta composer environments user-workloads-secrets delete \
      --environment chrom-batch-airflow \
      --location "${GCP_REGION}" \
      "sf-secrets"
fi

gcloud beta composer environments user-workloads-secrets create \
  --environment chrom-batch-airflow \
  --location "${GCP_REGION}" \
  --secret-file-path "${OUTPUT}"

echo "Secrets created in composer environment."