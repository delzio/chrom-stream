terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20.0"
    }
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = ">= 2.0.0"
    }
  }
}

provider "google" {
  credentials = file(var.gcp_credentials)
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "snowflake" {
  organization_name = var.sf_organization_name
  account_name      = var.sf_account_name
  user              = var.sf_user
  authenticator     = "SNOWFLAKE_JWT"
  private_key       = file(var.sf_credentials)
  role              = var.sf_role
  preview_features_enabled = [
    "snowflake_storage_integration_resource", 
    "snowflake_notification_integration_resource",
    "snowflake_table_resource",
    "snowflake_stage_resource",
    "snowflake_pipe_resource"
  ]
}

// Cloud Storage Buckets
resource "google_storage_bucket" "trend_bucket" {
  name          = var.gcs_trend_bucket
  location      = var.gcp_region
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1 #days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "batch_bucket" {
  name          = var.gcs_batch_bucket
  location      = var.gcp_region
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1 #days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "sample_bucket" {
  name          = var.gcs_sample_bucket
  location      = var.gcp_region
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1 #days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

// PubSub topics, subscriptions, notifications
resource "google_pubsub_topic" "chrom_stream_topic" {
  name = "chrom-sensor-readings"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_pubsub_subscription" "chrom_sensor_sub" {
  name  = "chrom-sensor-readings-sub"
  topic = google_pubsub_topic.chrom_stream_topic.name

  # Ensure order for consumer integration calculations
  enable_message_ordering = true

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # for pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }

  # set cloud run trigger
  push_config {
    push_endpoint = google_cloud_run_v2_service.influx_consumer.uri

    oidc_token {
      service_account_email = var.gcp_service_account
    }
  }
}

resource "google_pubsub_subscription" "chrom_batched_sub" {
  name  = "chrom-batched-readings-sub"
  topic = google_pubsub_topic.chrom_stream_topic.name

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # for pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }

  # set cloud run trigger
  push_config {
    push_endpoint = google_cloud_run_v2_service.gcs_consumer.uri

    oidc_token {
      service_account_email = var.gcp_service_account
    }
  }
}

// Pub/Sub for bucket notifications
resource "google_pubsub_topic" "trend_bucket_topic" {
  name = "trend-bucket-updates"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_pubsub_topic" "batch_bucket_topic" {
  name = "batch-bucket-updates"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_pubsub_topic" "sample_bucket_topic" {
  name = "sample-bucket-updates"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_storage_notification" "trend_bucket_notification" {
  provider       = google
  bucket         = google_storage_bucket.trend_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.trend_bucket_topic.id
  event_types    = ["OBJECT_FINALIZE"]
  depends_on     = [google_pubsub_topic_iam_binding.trend_binding]
}

resource "google_storage_notification" "batch_bucket_notification" {
  provider       = google
  bucket         = google_storage_bucket.batch_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.batch_bucket_topic.id
  event_types    = ["OBJECT_FINALIZE"]
  depends_on     = [google_pubsub_topic_iam_binding.batch_binding]
}

resource "google_storage_notification" "sample_bucket_notification" {
  provider       = google
  bucket         = google_storage_bucket.sample_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.sample_bucket_topic.id
  event_types    = ["OBJECT_FINALIZE"]
  depends_on     = [google_pubsub_topic_iam_binding.sample_binding]
}

// Enable notifications by giving the correct IAM permission to the unique service account
data "google_storage_project_service_account" "gcs_account" {
  provider = google
}

resource "google_pubsub_topic_iam_binding" "trend_binding" {
  provider = google
  topic    = google_pubsub_topic.trend_bucket_topic.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

resource "google_pubsub_topic_iam_binding" "batch_binding" {
  provider = google
  topic    = google_pubsub_topic.batch_bucket_topic.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

resource "google_pubsub_topic_iam_binding" "sample_binding" {
  provider = google
  topic    = google_pubsub_topic.sample_bucket_topic.id
  role     = "roles/pubsub.publisher"
  members  = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
}

resource "google_pubsub_subscription" "trend_bucket_sub" {
  name  = "trend-bucket-updates-sub"
  topic = google_pubsub_topic.trend_bucket_topic.name

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }
}

resource "google_pubsub_subscription" "batch_bucket_sub" {
  name  = "batch-bucket-updates-sub"
  topic = google_pubsub_topic.batch_bucket_topic.name

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }
}

resource "google_pubsub_subscription" "sample_bucket_sub" {
  name  = "sample-bucket-updates-sub"
  topic = google_pubsub_topic.sample_bucket_topic.name

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s" 


  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }
}

// Cloud Run Services
# influx consumer cloud run service
resource "google_cloud_run_v2_service" "influx_consumer" {
  name     = "influx-consumer"
  location = var.gcp_region
  deletion_protection = false

  template {
    service_account = var.gcp_service_account

    max_instance_request_concurrency = 10


    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/docker-repo/influx-consumer:latest"

      env {
        name  = "PUBSUB_STREAMING_SUB_ID"
        value = var.pubsub_streaming_sub_id
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
      }
      env {
        name  = "INFLUXDB_WRITE_TOKEN"
        value = var.influxdb_write_token
      }
      env {
        name  = "INFLUXDB_BUCKET"
        value = var.influxdb_bucket
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

  }
}

# gcs consumer cloud run service
resource "google_cloud_run_v2_service" "gcs_consumer" {
  name     = "gcs-consumer"
  location = var.gcp_region
  deletion_protection = false

  template {
    service_account = var.gcp_service_account

    max_instance_request_concurrency = 10


    containers {
      image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/docker-repo/gcs-consumer:latest"

      env {
        name  = "PUBSUB_BATCHED_SUB_ID"
        value = var.pubsub_batched_sub_id
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.gcp_project_id
      }
      env {
        name  = "GCS_TREND_BUCKET"
        value = var.gcs_trend_bucket
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

  }
}



