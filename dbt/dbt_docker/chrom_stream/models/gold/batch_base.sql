{{ config(
    materialized = 'table',
    unique_key = 'batch_id',
    on_schema_change = 'append_new_columns'
) }}

WITH batch_base AS (
    SELECT
        batch_id,
        recipe_name,
        chrom_id,
        event_name,
        event_ts,
        chrom_id || '_run_' || DENSE_RANK() OVER (PARTITION BY chrom_id ORDER BY batch_id) AS run_number
    FROM {{ ref('batch_silver') }} 
),

batch_starts AS (
    SELECT
        bb.batch_id,
        bb.recipe_name,
        bb.chrom_id,
        bb.event_ts AS batch_start_ts,
        bb.run_number
    FROM batch_base bb
    WHERE event_name = 'batch_start'
),

batch_ends AS (
    SELECT
        bb.batch_id,
        bb.event_ts AS batch_end_ts
    FROM batch_base bb
    WHERE event_name = 'batch_end'
)

SELECT
    bs.batch_id,
    bs.recipe_name,
    bs.chrom_id,
    bs.run_number,
    bs.batch_start_ts,
    be.batch_end_ts
FROM batch_starts bs 
LEFT JOIN batch_ends be
ON bs.batch_id = be.batch_id