-- Intervalo entre visitas 9203 consecutivas del mismo paciente (orden: llegada, visit_occurrence_id).
-- gap = llegada de la siguiente - fin de la anterior. Fin = máximo fin de las etapas que no son eventos previos
-- (o la llegada si no hay fin o es anterior a ella).
-- duracion_previa: 'corta' si la visita anterior dura < 5 min, 'larga' si dura >= 5 min,
-- 'sin_fin' si no tiene etapas no previas con fin (incluye las visitas sin etapas).
WITH det AS (
    SELECT d.visit_occurrence_id, MAX(d.visit_detail_end_datetime) AS fin
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND d.visit_detail_start_datetime >= v.visit_start_datetime - INTERVAL '1 hour'
    GROUP BY d.visit_occurrence_id
), vis AS (
    SELECT
        v.person_id,
        v.visit_occurrence_id,
        v.visit_start_datetime                                              AS llegada,
        GREATEST(COALESCE(det.fin, v.visit_start_datetime), v.visit_start_datetime) AS fin_ref,
        det.fin - v.visit_start_datetime                                    AS duracion
    FROM {schema}.visit_occurrence v
    LEFT JOIN det ON det.visit_occurrence_id = v.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
), pares AS (
    SELECT
        llegada,
        fin_ref,
        duracion,
        LEAD(llegada) OVER (PARTITION BY person_id ORDER BY llegada, visit_occurrence_id) AS llegada_sig
    FROM vis
), g AS (
    SELECT
        CASE
            WHEN duracion IS NULL THEN 'sin_fin'
            WHEN duracion < INTERVAL '5 minutes' THEN 'corta'
            ELSE 'larga'
        END                                                                     AS duracion_previa,
        llegada_sig = llegada                                                   AS misma_llegada,
        CAST(EXTRACT(EPOCH FROM (llegada_sig - fin_ref)) / 60.0 AS double precision) AS gap_min
    FROM pares
    WHERE llegada_sig IS NOT NULL
)
SELECT
    CASE
        WHEN misma_llegada        THEN '00 misma llegada'
        WHEN gap_min < 0          THEN '01 traslapada'
        WHEN gap_min < 10         THEN '02 0-10 min'
        WHEN gap_min < 20         THEN '03 10-20 min'
        WHEN gap_min < 30         THEN '04 20-30 min'
        WHEN gap_min < 45         THEN '05 30-45 min'
        WHEN gap_min < 60         THEN '06 45-60 min'
        WHEN gap_min < 90         THEN '07 60-90 min'
        WHEN gap_min < 120        THEN '08 90-120 min'
        WHEN gap_min < 240        THEN '09 2-4 h'
        WHEN gap_min < 720        THEN '10 4-12 h'
        WHEN gap_min < 1440       THEN '11 12-24 h'
        WHEN gap_min < 4320       THEN '12 1-3 d'
        WHEN gap_min < 10080      THEN '13 3-7 d'
        WHEN gap_min < 43200      THEN '14 7-30 d'
        ELSE                           '15 30 d o más'
    END                     AS categoria,
    duracion_previa,
    COUNT(*)                AS n_pares
FROM g
GROUP BY 1, 2
ORDER BY 1, 2;
