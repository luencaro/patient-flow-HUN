-- Completitud mensual de las visitas de urgencias (9203), por mes de llegada (población de análisis y visitas sin etapas).
-- n_sin_etapas: visitas sin ningún visit_detail.
-- n_solo_eventos_previos: visitas cuyas etapas son todas eventos previos.
-- n_hospitalizadas: con al menos un 9201 que no es evento previo (definición de hospitalizado).
-- n_atencion: no hospitalizadas con fin de urgencias >= llegada + 5 min (aproximación por visita al grupo 2).
WITH d AS (
    SELECT
        d.visit_occurrence_id,
        d.visit_detail_concept_id   AS c,
        d.visit_detail_end_datetime AS fin,
        COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE) AS previo
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
), det AS (
    SELECT
        visit_occurrence_id,
        BOOL_OR(NOT previo)                                 AS tiene_etapa,
        BOOL_OR(NOT previo AND c = 9201)                    AS hosp,
        MAX(fin) FILTER (WHERE NOT previo AND c <> 9201)    AS fin_urg
    FROM d
    GROUP BY visit_occurrence_id
)
SELECT
    CAST(date_trunc('month', v.visit_start_datetime) AS date)                       AS mes,
    COUNT(*)                                                                        AS n,
    COUNT(*) FILTER (WHERE det.visit_occurrence_id IS NULL)                         AS n_sin_etapas,
    100.0 * COUNT(*) FILTER (WHERE det.visit_occurrence_id IS NULL) / COUNT(*)      AS pct_sin_etapas,
    COUNT(*) FILTER (WHERE det.tiene_etapa = FALSE)                                 AS n_solo_eventos_previos,
    100.0 * COUNT(*) FILTER (WHERE det.tiene_etapa = FALSE) / COUNT(*)              AS pct_solo_eventos_previos,
    COUNT(*) FILTER (WHERE det.hosp)                                                AS n_hospitalizadas,
    100.0 * COUNT(*) FILTER (WHERE det.hosp) / COUNT(*)                             AS pct_hospitalizadas,
    COUNT(*) FILTER (WHERE det.hosp = FALSE
                       AND det.fin_urg >= v.visit_start_datetime + INTERVAL '5 minutes') AS n_atencion,
    100.0 * COUNT(*) FILTER (WHERE det.hosp = FALSE
                       AND det.fin_urg >= v.visit_start_datetime + INTERVAL '5 minutes') / COUNT(*)
                                                                                    AS pct_atencion
FROM {schema}.visit_occurrence v
LEFT JOIN det ON det.visit_occurrence_id = v.visit_occurrence_id
WHERE v.visit_concept_id = 9203
GROUP BY 1
ORDER BY 1;
