{{ config(
    materialized = 'table',
    unique_key = 'phase_id',
    on_schema_change = 'append_new_columns'
) }}

WITH phase_starts AS (
    SELECT
        ps.batch_id,
        ps.phase_name,
        ps.event_ts AS phase_start_ts
    FROM {{ ref('phase_silver') }} ps
    WHERE event_name = 'phase_start'
),

phase_ends AS (
    SELECT
        ps.batch_id,
        ps.phase_name,
        ps.event_ts AS phase_end_ts
    FROM {{ ref('phase_silver') }} ps
    WHERE event_name = 'phase_end'
)

SELECT
    {{ dbt_utils.generate_surrogate_key([
        "ps.batch_id",
        "ps.phase_name"
    ]) }} AS phase_id,
    ps.batch_id,
    ps.phase_name,
    ps.phase_start_ts,
    pe.phase_end_ts
FROM phase_starts ps 
LEFT JOIN phase_ends pe
ON ps.batch_id = pe.batch_id
AND ps.phase_name = pe.phase_name