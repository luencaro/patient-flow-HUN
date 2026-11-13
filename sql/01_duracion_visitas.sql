-- Duración de la visita completa (visit_end_datetime - visit_start_datetime) por tipo de visita.
-- Sirve para demostrar que la duración registrada es 0 en todas las visitas.
WITH e AS (
    SELECT
        v.visit_concept_id AS concepto_visita,
        CAST(EXTRACT(EPOCH FROM (v.visit_end_datetime - v.visit_start_datetime)) / 3600.0
             AS double precision) AS horas
    FROM {schema}.visit_occurrence v
)
SELECT
    e.concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')                          AS tipo_visita,
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
LEFT JOIN {schema}.concept c ON c.concept_id = e.concepto_visita
GROUP BY e.concepto_visita, c.concept_name
ORDER BY n DESC;
