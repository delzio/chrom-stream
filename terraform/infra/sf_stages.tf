resource "snowflake_stage" "trend_stage" {
  name                = "TREND_STAGE"
  database            = snowflake_database.chrom_stream_db.name
  schema              = snowflake_schema.bronze.name
  url                 = "gcs://${var.gcs_trend_bucket}/"
  storage_integration = snowflake_storage_integration.gcs_integration.name

  file_format = "type = PARQUET"
}

resource "snowflake_stage" "batch_stage" {
  name                = "BATCH_STAGE"
  database            = snowflake_database.chrom_stream_db.name
  schema              = snowflake_schema.bronze.name
  url                 = "gcs://${var.gcs_batch_bucket}/"
  storage_integration = snowflake_storage_integration.gcs_integration.name

  file_format = "TYPE = PARQUET"
}

resource "snowflake_stage" "sample_stage" {
  name                = "SAMPLE_STAGE"
  database            = snowflake_database.chrom_stream_db.name
  schema              = snowflake_schema.bronze.name
  url                 = "gcs://${var.gcs_sample_bucket}/"
  storage_integration = snowflake_storage_integration.gcs_integration.name

  file_format = "type = JSON"
}
