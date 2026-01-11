{{ config(
    materialized = 'incremental',
    unique_key = 'phase_event_id',
    on_schema_change = 'append_new_columns'
) }}

SELECT
    {{ dbt_utils.generate_surrogate_key([
        "raw:batch_id::number",
        "raw:phase::string",
        "raw:event::string"
    ]) }} AS phase_event_id,

    raw:batch_id::NUMBER AS batch_id,
    raw:phase::STRING AS phase_name,
    raw:event::STRING AS event_name,
    TO_TIMESTAMP(raw:event_ts::STRING) AS event_ts,
    source_file,
    load_time
FROM {{ source('bronze', 'batch_raw') }}
WHERE source_file LIKE 'raw/phase/%'
{% if is_incremental() %}
    AND load_time > (SELECT MAX(load_time) FROM {{ this }})
{% endif %}