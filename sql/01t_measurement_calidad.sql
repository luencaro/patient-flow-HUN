-- Calidad de measurement en una sola fila (tabla completa). Convención: ver 01t_person_calidad.sql.
SELECT
    COUNT(*)                                                                AS n_filas,
    COUNT(*) - COUNT(m.measurement_id)                                      AS nulos__measurement_id,
    COUNT(*) - COUNT(m.person_id)                                           AS nulos__person_id,
    COUNT(*) - COUNT(m.visit_occurrence_id)                                 AS nulos__visit_occurrence_id,
    COUNT(*) - COUNT(m.measurement_concept_id)                              AS nulos__measurement_concept_id,
    COUNT(*) - COUNT(m.measurement_datetime)                                AS nulos__measurement_datetime,
    COUNT(*) - COUNT(m.value_as_number)                                     AS nulos__value_as_number,
    COUNT(*) - COUNT(m.measurement_source_value_extended)                   AS nulos__measurement_source_value_extended,
    COUNT(DISTINCT m.person_id)                                             AS distintos__person_id,
    COUNT(DISTINCT m.visit_occurrence_id)                                   AS distintos__visit_occurrence_id,
    COUNT(DISTINCT m.measurement_concept_id)                                AS distintos__measurement_concept_id,
    COUNT(*) FILTER (WHERE m.measurement_concept_id = 0)                    AS chequeo__concepto_0,
    COUNT(*) FILTER (WHERE m.measurement_concept_id = 0 AND m.measurement_source_value_extended IS NOT NULL)
                                                                            AS chequeo__concepto_0_con_texto,
    COUNT(*) FILTER (WHERE m.measurement_concept_id IS NOT NULL AND c.concept_id IS NULL)
                                                                            AS chequeo__concepto_sin_traduccion,
    COUNT(*) FILTER (WHERE m.value_as_number IS NOT NULL)                   AS chequeo__con_valor_numerico,
    COUNT(*) FILTER (WHERE m.visit_occurrence_id IS NOT NULL AND v.visit_occurrence_id IS NULL)
                                                                            AS chequeo__visita_inexistente,
    CAST(date_trunc('month', MIN(m.measurement_datetime)) AS date)          AS rango__primer_mes,
    CAST(date_trunc('month', MAX(m.measurement_datetime)) AS date)          AS rango__ultimo_mes
FROM {schema}.measurement m
LEFT JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = m.visit_occurrence_id;
