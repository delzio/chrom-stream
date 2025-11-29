variable "credentials" {
    description = "My Project Credentials"
    default = "../.google/credentials/gcp.json"
}

variable "project" {
    description = "My Project"
}

variable "region" {
    description = "My Project Region"
}

variable "location" {
    description = "My Project Location"
}

variable "service_account_email" {
    description = "My Service Account Email"
}

variable "trend-bucket" {
    description = "My Time-Series Trend Data Storage Bucket Name"
}

variable "batch-bucket" {
    description = "My Batch Context Data Storage Bucket Name"
}

variable "sample-bucket" {
    description = "My Sample Result File Storage Bucket Name"
}

variable "gcs_storage" {
    description = "Bucket Storage Class"
    default = "STANDARD"
}

variable "cluster_name" {
    description = "My Dataproc Cluster"
    default = "spark-cluster"
}


