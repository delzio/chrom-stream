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