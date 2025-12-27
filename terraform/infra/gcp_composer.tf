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
                dbt-core       = "==1.10.8"
                dbt-snowflake  = "==1.10.0"
            }

            env_variables = {
                GCP_PROJECT_ID                  = var.gcp_project_id
                SNOWFLAKE_ORGANIZATION          = var.sf_organization_name
                SNOWFLAKE_ACCOUNT               = var.sf_account_name
                SNOWFLAKE_USER                  = snowflake_user.dbt_srvc_account.name
                SNOWFLAKE_ROLE                  = snowflake_account_role.dbt_role.name
                SNOWFLAKE_DATABASE              = "chrom_stream_db"
                SNOWFLAKE_WAREHOUSE             = "chrom_stream_wh"
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

resource "google_project_iam_member" "composer_secret_accessor" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

#resource "google_project_iam_member" "composer_v2_service_agent_ext" {
#  project = var.gcp_project_id
#  role    = "roles/composer.ServiceAgentV2Ext"
#  member  = "serviceAccount:service-${var.gcp_project_number}@cloudcomposer-accounts.iam.gserviceaccount.com"
#}

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
