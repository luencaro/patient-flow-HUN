-- Periodo cubierto y volumen total de visitas (solo agregados, fechas a nivel de día).
SELECT
    CAST(MIN(visit_start_datetime) AS date)          AS primera_fecha,
    CAST(MAX(visit_start_datetime) AS date)          AS ultima_fecha,
    COUNT(*)                                         AS n_visitas,
    COUNT(*) FILTER (WHERE visit_concept_id = 9203)  AS n_visitas_urgencias,
    COUNT(DISTINCT person_id)                        AS n_pacientes
FROM {schema}.visit_occurrence;
