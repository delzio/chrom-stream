{{ config(
    materialized = 'incremental',
    unique_key = 'test_id',
    on_schema_change = 'append_new_columns'
) }}

WITH base AS (
    SELECT *
    FROM {{ source('bronze', 'sample_raw') }}
    {% if is_incremental() %}
    WHERE load_time > (SELECT MAX(load_time) FROM {{ this }})
    {% endif %}
), 

flattened_messages as (
    SELECT
        raw:test_metadata:test_id::NUMBER AS test_id,
        f.value AS message,
        f.index AS message_index
    FROM base
    LEFT JOIN LATERAL FLATTEN(
        input => raw:system_status:messages
    ) f
),

flattened_errors as (
    SELECT
        raw:test_metadata:test_id::NUMBER AS test_id,
        f.value AS error,
        f.index AS error_index
    FROM base
    LEFT JOIN LATERAL FLATTEN(
        input => raw:system_status:errors
    ) f
),

concatenated_messages AS (
    SELECT 
        test_id,
        LISTAGG(flattened_messages.message::STRING, ' | ') WITHIN GROUP (ORDER BY flattened_messages.message_index) AS all_system_messages
    FROM flattened_messages
    GROUP BY test_id
),

concatenated_errors AS (
    SELECT 
        test_id,
        LISTAGG(flattened_errors.error::STRING, ' | ') WITHIN GROUP (ORDER BY flattened_errors.error_index) AS all_system_errors
    FROM flattened_errors
    GROUP BY test_id
)

SELECT
    raw:test_metadata:test_id::NUMBER AS test_id,
    TRY_TO_TIMESTAMP(raw:test_metadata:date::STRING) AS test_ts,
    raw:instrument:id::STRING AS instrument_id,
    raw:instrument:manufacturer::STRING AS manufacturer,
    raw:instrument:software_version::STRING AS software_version,
    raw:sample_metadata:sample_id::NUMBER AS sample_id,
    raw:sample_metadata:sample_type::STRING AS sample_type,
    raw:sample_metadata:batch_id::NUMBER AS batch_id,
    raw:measurement:linear_regression:slope_abs_per_mm::FLOAT AS slope_abs_per_mm,
    raw:measurement:linear_regression:intercept::FLOAT AS intercept,
    raw:measurement:linear_regression:r_squared::FLOAT AS r_squared,
    raw:measurement:linear_regression:num_points_used::NUMBER AS data_points_used,
    raw:measurement:concentration:protein_concentration_mg_mL::FLOAT AS protein_concentration_mg_ml,
    raw:system_status:scan_result::STRING AS scan_result,
    concatenated_messages.all_system_messages AS system_messages,
    concatenated_errors.all_system_errors AS system_errors,
    source_file,
    load_time
FROM base
LEFT JOIN concatenated_messages
ON raw:test_metadata:test_id::NUMBER = concatenated_messages.test_id
LEFT JOIN concatenated_errors
ON raw:test_metadata:test_id::NUMBER = concatenated_errors.test_id
