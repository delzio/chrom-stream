#!/bin/bash
set -eu

IMAGE_PATH="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/cloudrun-repo/influx-consumer:latest"

echo "Deploying Docker image to Google Cloud Artifact Registry"
echo "  PROJECT:     ${GCP_PROJECT_ID}"
echo "  REGION:      ${GCP_REGION}"
echo "  REPOSITORY:  cloudrun-repo"
echo "  IMAGE:       influx-consumer"
echo "  TAG:         latest"
echo ""

echo "Enabling Google Cloud APIs..."
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com

echo "Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev"

echo "Building via Google Cloud Build..."
gcloud builds submit "${CHROM_STREAM_HOME}/gcp_cloud_run/influx_consumer" --tag "${IMAGE_PATH}"

echo ""
echo "Successfully pushed image:"
echo "  ${IMAGE_PATH}"
echo ""