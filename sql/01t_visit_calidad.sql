-- Calidad de visit_occurrence en una sola fila (tabla completa). Convención: ver 01t_person_calidad.sql.
SELECT
    COUNT(*)                                                                    AS n_filas,
    COUNT(*) - COUNT(v.visit_occurrence_id)                                     AS nulos__visit_occurrence_id,
    COUNT(*) - COUNT(v.person_id)                                               AS nulos__person_id,
    COUNT(*) - COUNT(v.visit_concept_id)                                        AS nulos__visit_concept_id,
    COUNT(*) - COUNT(v.visit_start_datetime)                                    AS nulos__visit_start_datetime,
    COUNT(*) - COUNT(v.visit_end_datetime)                                      AS nulos__visit_end_datetime,
    COUNT(*) - COUNT(v.provider_id)                                             AS nulos__provider_id,
    COUNT(DISTINCT v.visit_occurrence_id)                                       AS distintos__visit_occurrence_id,
    COUNT(DISTINCT v.person_id)                                                 AS distintos__person_id,
    COUNT(DISTINCT v.visit_concept_id)                                          AS distintos__visit_concept_id,
    COUNT(DISTINCT v.provider_id)                                               AS distintos__provider_id,
    COUNT(*) - COUNT(DISTINCT v.visit_occurrence_id)                            AS chequeo__id_visita_repetido,
    COUNT(*) FILTER (WHERE v.visit_end_datetime = v.visit_start_datetime)       AS chequeo__fin_igual_a_inicio,
    COUNT(*) FILTER (WHERE v.visit_end_datetime < v.visit_start_datetime)       AS chequeo__fin_antes_de_inicio,
    COUNT(*) FILTER (WHERE date_trunc('day', v.visit_start_datetime) = v.visit_start_datetime)
                                                                                AS chequeo__inicio_a_medianoche,
    COUNT(*) FILTER (WHERE p.person_id IS NULL)                                 AS chequeo__paciente_inexistente,
    CAST(date_trunc('month', MIN(v.visit_start_datetime)) AS date)              AS rango__primer_mes,
    CAST(date_trunc('month', MAX(v.visit_start_datetime)) AS date)              AS rango__ultimo_mes
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.person p ON p.person_id = v.person_id;
