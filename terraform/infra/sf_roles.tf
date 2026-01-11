resource "snowflake_account_role" "dbt_role" {
  name = "DBT_TRANSFORMER"
}

resource "snowflake_grant_privileges_to_account_role" "warehouse_use" {
  account_role_name  = snowflake_account_role.dbt_role.name
  privileges = ["USAGE", "OPERATE", "MODIFY"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.chrom_stream_wh.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_database_privs" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["USAGE", "CREATE SCHEMA"]

  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.chrom_stream_db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_schema_usage" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["USAGE"]

  on_schema {
    all_schemas_in_database = snowflake_database.chrom_stream_db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_tables_dml" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database = snowflake_database.chrom_stream_db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_views_select" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["SELECT"]

  on_schema_object {
    all {
      object_type_plural = "VIEWS"
      in_database = snowflake_database.chrom_stream_db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_future_tables_dml" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]

  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_database = snowflake_database.chrom_stream_db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_future_views_select" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges        = ["SELECT"]

  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_database = snowflake_database.chrom_stream_db.name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_all_schema_privs" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges = ["ALL PRIVILEGES"]

  on_schema {
    all_schemas_in_database = snowflake_database.chrom_stream_db.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "dbt_future_schema_privs" {
  account_role_name = snowflake_account_role.dbt_role.name
  privileges = ["ALL PRIVILEGES"]

  on_schema {
    future_schemas_in_database = snowflake_database.chrom_stream_db.name
  }
}

resource "snowflake_grant_account_role" "dbt_account_role" {
  role_name = snowflake_account_role.dbt_role.name
  user_name = var.sf_dbt_user
}
