terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.13.0"
    }
  }
}


provider "google" {
  credentials = file(var.credentials)
  project = var.project
  region  = var.region
}

resource "google_storage_bucket" "trend_bucket" {
  name          = var.trend-bucket
  location      = var.location
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
  name          = var.batch-bucket
  location      = var.location
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
  name          = var.sample-bucket
  location      = var.location
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

// Pub/Sub For Streaming Sensor Data to InfluxDB and batching data to GCS
resource "google_pubsub_topic" "chrom_stream_topic" {
  name = "chrom-sensor-readings"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_pubsub_subscription" "chrom_stream_sub" {
  name  = "chrom-sensor-readings-sub"
  topic = google_pubsub_topic.chrom_stream_topic.name

  # Ensure order for consumer integration calculations
  enable_message_ordering = true

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }
}

resource "google_pubsub_subscription" "chrom_stream_sub" {
  name  = "chrom-batched-readings-sub"
  topic = google_pubsub_topic.chrom_stream_topic.name

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
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

// Enable notifications by giving the correct IAM permission to the unique service account.
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