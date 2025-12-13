resource "snowflake_storage_integration" "gcs_integration" {
  name                      = "GCS_INTEGRATION"
  type                      = "EXTERNAL_STAGE"
  storage_provider          = "GCS"
  enabled                   = true

  storage_allowed_locations = [
    "gcs://${var.gcs_batch_bucket}/",
    "gcs://${var.gcs_trend_bucket}/",
    "gcs://${var.gcs_sample_bucket}/",
  ]
}

resource "snowflake_notification_integration" "gcs_trend_notify" {
  name = "GCS_TREND_NOTIFY"

  notification_provider = "GCP_PUBSUB"
  enabled               = true

  gcp_pubsub_subscription_name = "projects/${var.gcp_project_id}/subscriptions/${google_pubsub_subscription.trend_bucket_sub.name}"
}

resource "snowflake_notification_integration" "gcs_batch_notify" {
  name = "GCS_BATCH_NOTIFY"

  notification_provider = "GCP_PUBSUB"
  enabled               = true

  gcp_pubsub_subscription_name = "projects/${var.gcp_project_id}/subscriptions/${google_pubsub_subscription.batch_bucket_sub.name}"
}

resource "snowflake_notification_integration" "gcs_sample_notify" {
  name = "GCS_SAMPLE_NOTIFY"

  notification_provider = "GCP_PUBSUB"
  enabled               = true

  gcp_pubsub_subscription_name = "projects/${var.gcp_project_id}/subscriptions/${google_pubsub_subscription.sample_bucket_sub.name}"
}