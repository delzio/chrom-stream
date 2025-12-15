{{ config(
    materialized = 'incremental',
    unique_key = 'trend_point_id',
    on_schema_change = 'append_new_columns'
) }}

SELECT
    {{ dbt_utils.generate_surrogate_key([
        "raw:chrom_unit::string",
        "raw:time_iso::string",
    ]) }} AS trend_point_id,

    raw:chrom_unit::string AS chrom_id,
    raw:time_sec::FLOAT AS totalized_batch_time_sec,
    TO_TIMESTAMP(raw:time_iso::STRING) AS reading_ts,
    raw:flow_mL_min::FLOAT / 1000 AS flow_rate_lpm,
    raw:pressure_bar::FLOAT AS pressure_bar,
    raw:ph::FLOAT AS ph,
    raw:uv_mau::FLOAT AS uv_mau,
    raw:cond_mScm::FLOAT AS cond_ms_cm,
    raw:totalized_volume_ml::FLOAT / 1000 AS totalized_vol_l,
    raw:totalized_column_volumes::FLOAT AS totalized_cv,
    source_file,
    load_time
FROM {{ source('bronze', 'trend_raw') }}
{% if is_incremental() %}
WHERE load_time > (SELECT MAX(load_time) FROM {{ this }})
{% endif %}