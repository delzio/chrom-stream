{{ config(
    materialized = 'view',
    unique_key = 'trend_point_id',
    on_schema_change = 'append_new_columns'
) }}

SELECT *
FROM {{ ref('trend_base') }}