-- Calidad de condition_occurrence en una sola fila (tabla completa). Convención: ver 01t_person_calidad.sql.
SELECT
    COUNT(*)                                                                AS n_filas,
    COUNT(*) - COUNT(co.condition_occurrence_id)                            AS nulos__condition_occurrence_id,
    COUNT(*) - COUNT(co.person_id)                                          AS nulos__person_id,
    COUNT(*) - COUNT(co.visit_occurrence_id)                                AS nulos__visit_occurrence_id,
    COUNT(*) - COUNT(co.condition_concept_id)                               AS nulos__condition_concept_id,
    COUNT(*) - COUNT(co.condition_start_datetime)                           AS nulos__condition_start_datetime,
    COUNT(*) - COUNT(co.condition_type_concept_id)                          AS nulos__condition_type_concept_id,
    COUNT(DISTINCT co.person_id)                                            AS distintos__person_id,
    COUNT(DISTINCT co.visit_occurrence_id)                                  AS distintos__visit_occurrence_id,
    COUNT(DISTINCT co.condition_concept_id)                                 AS distintos__condition_concept_id,
    COUNT(DISTINCT co.condition_type_concept_id)                            AS distintos__condition_type_concept_id,
    COUNT(*) FILTER (WHERE co.condition_concept_id = 0)                     AS chequeo__concepto_0,
    COUNT(*) FILTER (WHERE co.condition_concept_id IS NOT NULL AND c.concept_id IS NULL)
                                                                            AS chequeo__concepto_sin_traduccion,
    COUNT(*) FILTER (WHERE co.visit_occurrence_id IS NOT NULL AND v.visit_occurrence_id IS NULL)
                                                                            AS chequeo__visita_inexistente,
    COUNT(*) FILTER (WHERE co.condition_start_datetime > u.ultima_visita)   AS chequeo__fecha_posterior_a_la_ultima_visita,
    COUNT(*) FILTER (WHERE co.condition_start_datetime < u.primera_visita)  AS chequeo__fecha_anterior_a_la_primera_visita,
    CAST(date_trunc('month', MIN(co.condition_start_datetime)) AS date)     AS rango__primer_mes,
    CAST(date_trunc('month', MAX(co.condition_start_datetime)) AS date)     AS rango__ultimo_mes
FROM {schema}.condition_occurrence co
LEFT JOIN {schema}.concept c ON c.concept_id = co.condition_concept_id
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = co.visit_occurrence_id
CROSS JOIN (SELECT MIN(visit_start_datetime) AS primera_visita, MAX(visit_start_datetime) AS ultima_visita
            FROM {schema}.visit_occurrence) u;
