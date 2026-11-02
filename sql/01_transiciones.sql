-- Transiciones entre etapas consecutivas dentro de una visita de urgencias (sin etapas desplazadas).
-- gap = inicio de la etapa siguiente - fin de la etapa actual, en minutos (negativo = traslape).
WITH d AS (
    SELECT
        d.visit_occurrence_id,
        d.visit_detail_id,
        d.visit_detail_concept_id     AS concepto,
        d.visit_detail_start_datetime AS ini,
        d.visit_detail_end_datetime   AS fin
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND d.visit_detail_start_datetime >= v.visit_start_datetime - INTERVAL '1 hour'
), pares AS (
    SELECT
        concepto                AS concepto_origen,
        fin                     AS fin_origen,
        LEAD(concepto) OVER w   AS concepto_destino,
        LEAD(ini) OVER w        AS ini_destino
    FROM d
    WINDOW w AS (PARTITION BY visit_occurrence_id ORDER BY ini, visit_detail_id)
), t AS (
    SELECT
        concepto_origen,
        concepto_destino,
        CAST(EXTRACT(EPOCH FROM (ini_destino - fin_origen)) / 60.0 AS double precision) AS gap_min
    FROM pares
    WHERE concepto_destino IS NOT NULL
)
SELECT
    t.concepto_origen,
    COALESCE(co.concept_name, '(sin concepto)')                        AS etapa_origen,
    t.concepto_destino,
    COALESCE(cd.concept_name, '(sin concepto)')                        AS etapa_destino,
    COUNT(*)                                                           AS n,
    COUNT(*) FILTER (WHERE t.gap_min IS NULL)                          AS n_gap_nulo,
    100.0 * COUNT(*) FILTER (WHERE t.gap_min IS NULL) / COUNT(*)       AS pct_gap_nulo,
    COUNT(*) FILTER (WHERE t.gap_min < 0)                              AS n_traslape,
    100.0 * COUNT(*) FILTER (WHERE t.gap_min < 0) / COUNT(*)           AS pct_traslape,
    COUNT(*) FILTER (WHERE t.gap_min = 0)                              AS n_contiguas,
    100.0 * COUNT(*) FILTER (WHERE t.gap_min = 0) / COUNT(*)           AS pct_contiguas,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY t.gap_min)            AS p10_gap_min,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY t.gap_min)            AS p50_gap_min,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY t.gap_min)            AS p90_gap_min
FROM t
LEFT JOIN {schema}.concept co ON co.concept_id = t.concepto_origen
LEFT JOIN {schema}.concept cd ON cd.concept_id = t.concepto_destino
GROUP BY t.concepto_origen, co.concept_name, t.concepto_destino, cd.concept_name
ORDER BY n DESC;
