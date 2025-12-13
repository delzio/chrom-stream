resource "snowflake_table" "trend_raw" {
  name     = "TREND_RAW"
  database = snowflake_database.chrom_stream_db.name
  schema   = snowflake_schema.bronze.name

  column {
    name = "RAW"
    type = "VARIANT"
  }
  column {
    name = "SOURCE_FILE"
    type = "VARCHAR"
  }
  column {
    name = "LOAD_TIME"
    type = "TIMESTAMP_TZ"
  }
}

resource "snowflake_table" "batch_raw" {
  name     = "BATCH_RAW"
  database = snowflake_database.chrom_stream_db.name
  schema   = snowflake_schema.bronze.name

  column {
    name = "RAW"
    type = "VARIANT"
  }
  column {
    name = "SOURCE_FILE"
    type = "VARCHAR"
  }
  column {
    name = "LOAD_TIME"
    type = "TIMESTAMP_TZ"
  }
}
resource "snowflake_table" "sample_raw" {
  name     = "SAMPLE_RAW"
  database = snowflake_database.chrom_stream_db.name
  schema   = snowflake_schema.bronze.name

  column {
    name = "RAW"
    type = "VARIANT"
  }
  column {
    name = "SOURCE_FILE"
    type = "VARCHAR"
  }
  column {
    name = "LOAD_TIME"
    type = "TIMESTAMP_TZ"
  }
}