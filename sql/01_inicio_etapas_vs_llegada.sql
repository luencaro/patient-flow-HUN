-- Minutos entre el inicio de cada etapa y la llegada (visit_start_datetime), en visitas de urgencias.
-- Valores negativos: la etapa empieza antes de la llegada. Desplazada (D2): más de 60 min antes.
WITH d AS (
    SELECT
        d.visit_detail_concept_id AS concepto_etapa,
        CAST(EXTRACT(EPOCH FROM (d.visit_detail_start_datetime - v.visit_start_datetime)) / 60.0
             AS double precision) AS minutos
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
)
SELECT
    d.concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')                         AS etapa,
    COUNT(*)                                                           AS n,
    COUNT(*) FILTER (WHERE d.minutos = 0)                              AS n_igual_llegada,
    100.0 * COUNT(*) FILTER (WHERE d.minutos = 0) / COUNT(*)           AS pct_igual_llegada,
    COUNT(*) FILTER (WHERE d.minutos < -60)                            AS n_desplazadas,
    100.0 * COUNT(*) FILTER (WHERE d.minutos < -60) / COUNT(*)         AS pct_desplazadas,
    percentile_cont(0.01) WITHIN GROUP (ORDER BY d.minutos)            AS p01_min,
    percentile_cont(0.05) WITHIN GROUP (ORDER BY d.minutos)            AS p05_min,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY d.minutos)            AS p10_min,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY d.minutos)            AS p50_min,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY d.minutos)            AS p90_min,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY d.minutos)            AS p99_min
FROM d
LEFT JOIN {schema}.concept c ON c.concept_id = d.concepto_etapa
GROUP BY d.concepto_etapa, c.concept_name
ORDER BY n DESC;
