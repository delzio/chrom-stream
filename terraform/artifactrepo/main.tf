terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project = var.gcp_project_id
  region  = var.gcp_region
}

// CloudBuild Artifact Repo
resource "google_artifact_registry_repository" "cloudrun_repo" {
  provider        = google
  repository_id   = "cloudrun-repo"
  description     = "Container registry for Cloud Run services"
  format          = "DOCKER"
  location        = var.gcp_region
}