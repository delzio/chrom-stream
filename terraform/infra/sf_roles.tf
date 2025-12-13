resource "snowflake_account_role" "etl_role" {
  name = "ETL_ROLE"
}

resource "snowflake_grant_privileges_to_account_role" "bronze_usage" {
  account_role_name  = snowflake_account_role.etl_role.name
  privileges = ["USAGE", "CREATE TABLE"]
  on_schema {
    schema_name = "${snowflake_database.chrom_stream_db.name}.BRONZE"
  }
}

resource "snowflake_grant_privileges_to_account_role" "silver_usage" {
  account_role_name  = snowflake_account_role.etl_role.name
  privileges = ["USAGE", "CREATE TABLE"]
  on_schema {
    schema_name = "${snowflake_database.chrom_stream_db.name}.SILVER"
  }
}

resource "snowflake_grant_privileges_to_account_role" "gold_usage" {
  account_role_name  = snowflake_account_role.etl_role.name
  privileges = ["USAGE", "CREATE TABLE"]
  on_schema {
    schema_name = "${snowflake_database.chrom_stream_db.name}.GOLD"
  }
}

resource "snowflake_grant_privileges_to_account_role" "warehouse_use" {
  account_role_name  = snowflake_account_role.etl_role.name
  privileges = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.chrom_stream_wh.name
  }
}
