resource "google_composer_environment" "chrom_batch_airflow" {
    name   = "chrom-batch-airflow"
    region = var.region

    config {
        environment_size = "ENVIRONMENT_SIZE_SMALL"

        node_config {
            service_account = google_service_account.composer_sa.email
        }

        software_config {
            image_version = "composer-3-airflow-2"

            pypi_packages = {
                dbt-core       = "==1.10.*"
                dbt-snowflake  = "==1.10.*"
            }

            env_variables = {
                AIRFLOW__CORE__LOAD_EXAMPLES    = "False"
                SNOWFLAKE_ACCOUNT               = var.sf_account_name
                SNOWFLAKE_USER                  = var.sf_user
                SNOWFLAKE_PASSWORD              = var.sf_password
                SNOWFLAKE_ROLE                  = var.sf_role
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
  project = var.project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_project_iam_member" "composer_gcs" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}
