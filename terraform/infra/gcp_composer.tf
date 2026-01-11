resource "google_composer_environment" "chrom_batch_airflow" {
  name   = "chrom-batch-airflow"
  region = var.gcp_region

  config {
    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      service_account = google_service_account.composer_sa.email
    }

    software_config {
      image_version = "composer-3-airflow-2"

      pypi_packages = {
        apache-airflow-providers-cncf-kubernetes = ">=7.0.0"
      }

      env_variables = {
        DBT_IMAGE = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/docker-repo/dbt-snowflake-pipeline"
        SF_ORGANIZATION          = var.sf_organization_name
        SF_ACCOUNT               = var.sf_account_name
        SF_USER                  = var.sf_dbt_user
        SF_ROLE                  = var.sf_dbt_role
      }
    }
  }
}

resource "google_service_account" "composer_sa" {
  account_id   = "chrom-batch-composer"
  display_name = "Chrom Batch Composer Service Account"
}

resource "google_project_iam_member" "composer_worker" {
  project = var.gcp_project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_project_iam_member" "composer_gcs" {
  project = var.gcp_project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_project_iam_member" "composer_container_developer" {
  project = var.gcp_project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_project_iam_member" "gke_secret_access" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_service_account_iam_member" "composer_service_agent_actas" {
  service_account_id = google_service_account.composer_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:service-${var.gcp_project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "terraform_actas_composer" {
  service_account_id = google_service_account.composer_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.gcp_service_account}"
}