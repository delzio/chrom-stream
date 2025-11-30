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

resource "google_storage_bucket" "trend-bucket" {
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

resource "google_storage_bucket" "batch-bucket" {
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

resource "google_storage_bucket" "sample-bucket" {
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

resource "google_pubsub_topic" "chrom-stream-topic" {
  name = "chrom-sensor-readings"

  message_retention_duration = "86400s" # 24 hours
}

resource "google_pubsub_subscription" "chrom-stream-sub" {
  name  = "chrom-sensor-readings-sub"
  topic = google_pubsub_topic.chrom-stream-topic.name

  # Ensure order for consumer integration calculations
  enable_message_ordering = true

  ack_deadline_seconds       = 10
  message_retention_duration = "86400s"

  # pull-mode
  expiration_policy {
    ttl = "604800s" # 7 days
  }
}

