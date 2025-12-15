{{ config(
    materialized = 'table',
    unique_key = 'batch_id',
    on_schema_change = 'append_new_columns'
) }}

WITH samples_base AS (
    SELECT 
        ss.batch_id,
        ss.sample_id,
        ss.sample_type,
        ss.test_id,
        ss.test_ts,
        ss.protein_concentration_mg_ml,
        ss.scan_result,
        ROW_NUMBER() OVER (PARTITION BY ss.sample_id ORDER BY ss.test_ts) - 1 AS retest_count
    FROM {{ ref('sample_silver') }} ss
),

pre_sample_results AS (
    SELECT 
        sb.batch_id,
        sb.protein_concentration_mg_ml AS pre_chrom_concentration_mg_ml,
        sb.retest_count AS pre_chrom_sample_retest_count
    FROM samples_base sb
    WHERE sb.sample_type = 'pre-affinity'
    AND sb.scan_result = 'success'
),

post_sample_results AS (
    SELECT 
        sb.batch_id,
        sb.protein_concentration_mg_ml AS post_chrom_concentration_mg_ml,
        sb.retest_count AS post_chrom_sample_retest_count
    FROM samples_base sb
    WHERE sb.sample_type = 'post-affinity'
    AND sb.scan_result = 'success'
),

load_base AS (
    SELECT
        tb.batch_id,
        max(tb.phase_tot_cv) * 226 AS total_load_vol_l,
        max(tb.uv_auc) AS load_uv_auc
    FROM {{ ref('trend_base') }} tb
    WHERE tb.phase_name = 'Load'
    GROUP BY tb.batch_id
),

elution_base AS (
    SELECT
        tb.batch_id,
        min(tb.phase_tot_cv) AS elution_pooling_start_cv,
        max(tb.phase_tot_cv) AS elution_pooling_end_cv
    FROM {{ ref('trend_base') }} tb
    WHERE tb.phase_name = 'Elution'
    AND tb.uv_mau > 50
    GROUP BY tb.batch_id
)

SELECT
    bb.batch_id,
    bb.recipe_name,
    bb.chrom_id,
    bb.run_number,
    bb.batch_start_ts,
    bb.batch_end_ts,
    presmp.pre_chrom_concentration_mg_ml,
    presmp.pre_chrom_sample_retest_count,
    lb.total_load_vol_l,
    postsmp.post_chrom_concentration_mg_ml,
    postsmp.post_chrom_sample_retest_count,
    eb.elution_pooling_start_cv,
    eb.elution_pooling_end_cv,
    (eb.elution_pooling_end_cv - eb.elution_pooling_start_cv) * 226 AS total_pool_volume_l,
    (eb.elution_pooling_end_cv - eb.elution_pooling_start_cv) * 226 * postsmp.post_chrom_concentration_mg_ml / 
    (lb.total_load_vol_l * pre_chrom_concentration_mg_ml) * 100 AS step_yield_pct,
    lb.load_uv_auc,
    CASE 
        WHEN lb.load_uv_auc > 100 THEN 'Load Breakthrough Alert'
        ELSE 'No Alerts'
    END AS batch_alerts
FROM {{ ref('batch_base') }} bb
LEFT JOIN pre_sample_results presmp
ON bb.batch_id = presmp.batch_id
LEFT JOIN post_sample_results postsmp
ON bb.batch_id = postsmp.batch_id
LEFT JOIN load_base lb
ON bb.batch_id = lb.batch_id
LEFT JOIN elution_base eb
on bb.batch_id = eb.batch_id
