variable "credentials" {
    description = "My Project Credentials"
    default = "../../.google/credentials/gcp.json"
}

variable "gcp_project_id" {
    description = "My Project"
}

variable "gcp_region" {
    description = "My Project Region"
}

variable "gcp_service_account" {
    description = "My Service Account Email"
}

variable "gcs_trend_bucket" {
    description = "My Time-Series Trend Data Storage Bucket Name"
}

variable "gcs_batch_bucket" {
    description = "My Batch Context Data Storage Bucket Name"
}

variable "gcs_sample_bucket" {
    description = "My Sample Result File Storage Bucket Name"
}

variable "influxdb_bucket" {
    description = "My InfluxDB Database/Bucket Name"
}

variable "influxdb_write_token" {
    description = "My InfluxDB write token"
}

variable "pubsub_streaming_sub_id" {
    description = "My pubsub chrom sensor streaming subscription for InfluxDB"
}

variable "pubsub_batched_sub_id" {
    description = "My pubsub chrom sensor batched subscription for GCS"
}

variable "sf_organization_name" {
    description = "My snowflake organization name"
}

variable "sf_account_name" {
    description = "My snowflake account name"
}

variable "sf_user" {
    description = "My snowflake username"
}

variable "sf_password" {
    description = "My snowflake password"
}

variable "sf_role" {
    description = "My snowflake role"
}

