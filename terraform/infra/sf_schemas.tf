resource "snowflake_warehouse" "chrom_stream_wh" {
  name            = "CHROM_STREAM_WH"
  warehouse_size  = "XSMALL"
  auto_suspend    = 60
  auto_resume     = true
  initially_suspended = true
}

resource "snowflake_database" "chrom_stream_db" {
  name = "CHROM_STREAM_DB"
}

resource "snowflake_schema" "bronze" {
  name     = "BRONZE"
  database = snowflake_database.chrom_stream_db.name
}

resource "snowflake_schema" "silver" {
  name     = "SILVER"
  database = snowflake_database.chrom_stream_db.name
}

resource "snowflake_schema" "gold" {
  name     = "GOLD"
  database = snowflake_database.chrom_stream_db.name
}