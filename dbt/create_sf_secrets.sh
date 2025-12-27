#!/usr/bin/env bash
set -eu

LOCAL_SNOWFLAKE_SECRET_DIR="${CHROM_STREAM_HOME}/.snowflake/credentials"

mkdir -p "${LOCAL_SNOWFLAKE_SECRET_DIR}"

echo "Publishing new secrets"

if gcloud secrets describe SNOWFLAKE_OAUTH_CLIENT >/dev/null 2>&1; then
  echo "Deleting existing secret: SNOWFLAKE_OAUTH_CLIENT"
  gcloud secrets delete SNOWFLAKE_OAUTH_CLIENT --quiet
fi

echo -n "${SF_OAUTH_CLIENT}" | \
gcloud secrets create SNOWFLAKE_OAUTH_CLIENT \
  --data-file=-

if gcloud secrets describe SNOWFLAKE_OAUTH_SECRET >/dev/null 2>&1; then
  echo "Deleting existing secret: SNOWFLAKE_OAUTH_SECRET"
  gcloud secrets delete SNOWFLAKE_OAUTH_SECRET --quiet
fi

echo -n "${SF_OAUTH_SECRET}" | \
gcloud secrets create SNOWFLAKE_OAUTH_SECRET \
  --data-file=-

echo "Secrets successfully published to GCP Secret Manager"