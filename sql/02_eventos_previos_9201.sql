-- Etapas 9201 (hospitalización en piso) que son eventos previos (inicio > 1 h antes de la llegada) en
-- visitas de urgencias. Reproduce el análisis hecho en DBeaver (sección 2.3 del documento de decisiones).
-- categoria: 'termina_antes' si la etapa termina antes de la llegada; 'sigue_abierta' si termina en o
--   después de la llegada, o no tiene fin.
-- dias_fin_a_llegada: días entre el fin de la etapa y la llegada (solo tiene sentido en 'termina_antes').
-- n_fin_30d: etapas cuyo fin está en los 30 días antes de la llegada (definición de hosp_previa_30d).
-- n_visita_cerca: el mismo paciente tiene OTRA visita (de cualquier tipo) que empieza a +/- 24 h del inicio
--   de la etapa. Se calcula con un JOIN contra un conjunto pre-agregado, no con un EXISTS correlacionado.
WITH previos AS (
    SELECT
        d.visit_detail_id,
        v.visit_occurrence_id,
        v.person_id,
        d.visit_detail_start_datetime AS ini,
        d.visit_detail_end_datetime   AS fin,
        v.visit_start_datetime        AS llegada
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND d.visit_detail_concept_id = 9201
      AND d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour'
), visitas_pacientes AS (
    SELECT v.person_id, v.visit_occurrence_id, v.visit_start_datetime
    FROM {schema}.visit_occurrence v
    JOIN (SELECT DISTINCT person_id FROM previos) pp ON pp.person_id = v.person_id
), cerca AS (
    SELECT DISTINCT p.visit_detail_id
    FROM previos p
    JOIN visitas_pacientes o
      ON o.person_id = p.person_id
     AND o.visit_occurrence_id <> p.visit_occurrence_id
     AND o.visit_start_datetime BETWEEN p.ini - INTERVAL '24 hours' AND p.ini + INTERVAL '24 hours'
), m AS (
    SELECT
        CASE WHEN p.fin < p.llegada THEN 'termina_antes' ELSE 'sigue_abierta' END                 AS categoria,
        CAST(EXTRACT(EPOCH FROM (p.llegada - p.fin)) / 86400.0 AS double precision)               AS dias_fin_a_llegada,
        CAST(EXTRACT(EPOCH FROM (p.fin - p.ini)) / 3600.0 AS double precision)                    AS duracion_h,
        p.fin <= p.llegada AND p.fin >= p.llegada - INTERVAL '30 days'                            AS fin_30d,
        ce.visit_detail_id IS NOT NULL                                                            AS visita_cerca
    FROM previos p
    LEFT JOIN cerca ce ON ce.visit_detail_id = p.visit_detail_id
)
SELECT
    categoria,
    COUNT(*)                                                                    AS n,
    100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()                                    AS pct_del_total,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY dias_fin_a_llegada)            AS p10_dias_fin_a_llegada,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY dias_fin_a_llegada)            AS p50_dias_fin_a_llegada,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY dias_fin_a_llegada)            AS p90_dias_fin_a_llegada,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY duracion_h)                    AS p10_duracion_h,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY duracion_h)                    AS p50_duracion_h,
    percentile_cont(0.90) WITHIN GROUP (ORDER BY duracion_h)                    AS p90_duracion_h,
    COUNT(*) FILTER (WHERE fin_30d)                                             AS n_fin_30d,
    100.0 * COUNT(*) FILTER (WHERE fin_30d) / COUNT(*)                          AS pct_fin_30d,
    COUNT(*) FILTER (WHERE visita_cerca)                                        AS n_visita_cerca,
    100.0 * COUNT(*) FILTER (WHERE visita_cerca) / COUNT(*)                     AS pct_visita_cerca
FROM m
GROUP BY categoria
ORDER BY categoria DESC;
