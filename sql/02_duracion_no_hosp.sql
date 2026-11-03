-- Duración de las visitas de urgencias no hospitalizadas (fin_urg - llegada), en tramos, para ver el corte
-- de 5 minutos de los contactos breves (D6). Incluye las visitas sin etapas no previas (D10) y, aparte,
-- las hospitalizadas (D3).
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
), x AS (
    SELECT
        det.tiene_etapa,
        det.hosp,
        CAST(EXTRACT(EPOCH FROM (det.fin_urg - v.visit_start_datetime)) / 60.0 AS double precision) AS minutos
    FROM {schema}.visit_occurrence v
    LEFT JOIN det ON det.visit_occurrence_id = v.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
)
SELECT
    CASE
        WHEN tiene_etapa IS NULL OR NOT tiene_etapa THEN '00 sin etapas'
        WHEN hosp                                   THEN '99 hospitalizada'
        WHEN minutos IS NULL                        THEN '01 sin fin'
        WHEN minutos < 0                            THEN '02 fin antes de la llegada'
        WHEN minutos = 0                            THEN '03 0 min'
        WHEN minutos < 1                            THEN '04 0-1 min'
        WHEN minutos < 2                            THEN '05 1-2 min'
        WHEN minutos < 5                            THEN '06 2-5 min'
        WHEN minutos < 15                           THEN '07 5-15 min'
        WHEN minutos < 30                           THEN '08 15-30 min'
        WHEN minutos < 60                           THEN '09 30-60 min'
        WHEN minutos < 240                          THEN '10 1-4 h'
        WHEN minutos < 720                          THEN '11 4-12 h'
        WHEN minutos < 1440                         THEN '12 12-24 h'
        ELSE                                             '13 24 h o más'
    END                     AS tramo,
    COUNT(*)                AS n_visitas
FROM x
GROUP BY 1
ORDER BY 1;
