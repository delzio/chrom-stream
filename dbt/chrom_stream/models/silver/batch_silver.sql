{{ config(
    materialized = 'incremental',
    unique_key = 'batch_event_id',
    on_schema_change = 'append_new_columns'
) }}

SELECT
    {{ dbt_utils.generate_surrogate_key([
        "raw:batch_id::number",
        "raw:chrom_id::string",
        "raw:event::string"
    ]) }} AS batch_event_id,

    raw:batch_id::NUMBER AS batch_id,
    raw:recipe_name::STRING AS recipe_name,
    raw:chrom_id::STRING AS chrom_id,
    raw:event::STRING AS event_name,
    TO_TIMESTAMP(raw:event_ts::STRING) AS event_ts,
    source_file,
    load_time
FROM {{ source('bronze', 'batch_raw') }}
WHERE source_file LIKE 'raw/batch/%'
{% if is_incremental() %}
    AND load_time > (SELECT MAX(load_time) FROM {{ this }})
{% endif %}
