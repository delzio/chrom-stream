{{ config(
    materialized = 'table',
    unique_key = 'trend_point_id',
    on_schema_change = 'append_new_columns'
) }}

WITH trend_base AS (
    SELECT
        bb.batch_id,
        bb.chrom_id,
        bb.recipe_name,
        bb.run_number,
        pb.phase_name,
        ts.totalized_batch_time_sec,
        ts.reading_ts,
        ts.flow_rate_lpm,
        ts.pressure_bar,
        ts.ph,
        ts.uv_mau,
        ts.cond_ms_cm,
        0.5 * (
            ts.flow_rate_lpm + LAG(ts.flow_rate_lpm) OVER (PARTITION BY bb.batch_id ORDER BY ts.reading_ts)
        ) * (
            DATEDIFF(seconds, LAG(ts.reading_ts) OVER (PARTITION BY bb.batch_id ORDER BY ts.reading_ts), ts.reading_ts) / 60
        ) AS vol_thru_l,
        0.5 * (
            ts.uv_mau + LAG(ts.uv_mau) OVER (PARTITION BY bb.batch_id ORDER BY ts.reading_ts)
        ) * (
            DATEDIFF(seconds, LAG(ts.reading_ts) OVER (PARTITION BY bb.batch_id ORDER BY ts.reading_ts), ts.reading_ts) / 60
        ) AS uv_auc
    FROM {{ ref('trend_silver' )}} ts
    LEFT JOIN {{ ref('batch_base') }} bb
    ON ts.chrom_id = bb.chrom_id
    AND ts.reading_ts BETWEEN bb.batch_start_ts AND bb.batch_end_ts
    LEFT JOIN {{ ref('phase_base') }} pb
    ON bb.batch_id = pb.batch_id
    AND ts.reading_ts BETWEEN pb.phase_start_ts AND pb.phase_end_ts
)

SELECT
    {{ dbt_utils.generate_surrogate_key([
        "tb.chrom_id",
        "tb.reading_ts",
    ]) }} AS trend_point_id,
    tb.*,
    SUM(tb.vol_thru_l) OVER (PARTITION BY tb.batch_id ORDER BY tb.reading_ts) / 226 AS batch_tot_cv, --226L colummn
    SUM(tb.vol_thru_l) OVER (PARTITION BY tb.batch_id, tb.phase_name ORDER BY tb.reading_ts) / 226 AS phase_tot_cv, --226L colummn
    SUM(tb.uv_auc) OVER (PARTITION BY tb.batch_id, tb.phase_name ORDER BY tb.reading_ts) AS uv_tot_auc
FROM
    trend_base tb
