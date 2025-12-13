resource "snowflake_pipe" "trend_pipe" {
  name                      = "TREND_PIPE"
  database                  = snowflake_database.chrom_stream_db.name
  schema                    = snowflake_schema.bronze.name
  auto_ingest               = true
  integration               = snowflake_notification_integration.gcs_trend_notify.name

  copy_statement = <<EOF
    COPY INTO chrom_stream_db.bronze.trend_raw(raw, load_time, source_file)
    FROM (
        SELECT
        $1 AS raw,
        METADATA$START_SCAN_TIME as load_time,
        METADATA$FILENAME AS source_file
        FROM @chrom_stream_db.bronze.trend_stage
    )
    FILE_FORMAT = (TYPE = PARQUET);
  EOF
}

resource "snowflake_pipe" "batch_pipe" {
  name                      = "BATCH_PIPE"
  database                  = snowflake_database.chrom_stream_db.name
  schema                    = snowflake_schema.bronze.name
  auto_ingest               = true
  integration               = snowflake_notification_integration.gcs_batch_notify.name

  copy_statement = <<EOF
    COPY INTO chrom_stream_db.bronze.batch_raw(raw, load_time, source_file)
    FROM (
        SELECT
        $1 AS raw,
        METADATA$START_SCAN_TIME as load_time,
        METADATA$FILENAME AS source_file
        FROM @chrom_stream_db.bronze.batch_stage
    )
    FILE_FORMAT = (TYPE = PARQUET);
  EOF
}

resource "snowflake_pipe" "sample_pipe" {
  name                      = "SAMPLE_PIPE"
  database                  = snowflake_database.chrom_stream_db.name
  schema                    = snowflake_schema.bronze.name
  auto_ingest               = true
  integration               = snowflake_notification_integration.gcs_sample_notify.name

  copy_statement = <<EOF
    COPY INTO chrom_stream_db.bronze.sample_raw(raw, load_time, source_file)
    FROM (
        SELECT
        $1 AS raw,
        METADATA$START_SCAN_TIME as load_time,
        METADATA$FILENAME AS source_file
        FROM @chrom_stream_db.bronze.sample_stage
    )
    FILE_FORMAT = (TYPE = JSON);
  EOF
}
