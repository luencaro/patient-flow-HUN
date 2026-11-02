-- Duración de cada etapa (visit_detail): sin fin, negativas, cero y percentiles en horas.
-- Incluye todas las etapas (también las desplazadas); es un inventario de calidad.
WITH e AS (
    SELECT
        d.visit_detail_concept_id AS concepto_etapa,
        CAST(EXTRACT(EPOCH FROM (d.visit_detail_end_datetime - d.visit_detail_start_datetime)) / 3600.0
             AS double precision) AS horas
    FROM {schema}.visit_detail d
)
SELECT
    e.concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')                          AS etapa,
    COUNT(*)                                                            AS n,
    COUNT(*) FILTER (WHERE e.horas IS NULL)                             AS n_sin_fin,
    100.0 * COUNT(*) FILTER (WHERE e.horas IS NULL) / COUNT(*)          AS pct_sin_fin,
    COUNT(*) FILTER (WHERE e.horas < 0)                                 AS n_negativas,
    100.0 * COUNT(*) FILTER (WHERE e.horas < 0) / COUNT(*)              AS pct_negativas,
    COUNT(*) FILTER (WHERE e.horas = 0)                                 AS n_cero,
    100.0 * COUNT(*) FILTER (WHERE e.horas = 0) / COUNT(*)              AS pct_cero,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY e.horas)               AS p10_h,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY e.horas)               AS p50_h,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY e.horas)               AS p90_h,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY e.horas)               AS p99_h
FROM e
LEFT JOIN {schema}.concept c ON c.concept_id = e.concepto_etapa
GROUP BY e.concepto_etapa, c.concept_name
ORDER BY n DESC;
