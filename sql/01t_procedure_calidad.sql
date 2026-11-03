-- Calidad de procedure_occurrence en una sola fila (tabla completa). Convención: ver 01t_person_calidad.sql.
SELECT
    COUNT(*)                                                                AS n_filas,
    COUNT(*) - COUNT(po.procedure_occurrence_id)                            AS nulos__procedure_occurrence_id,
    COUNT(*) - COUNT(po.person_id)                                          AS nulos__person_id,
    COUNT(*) - COUNT(po.visit_occurrence_id)                                AS nulos__visit_occurrence_id,
    COUNT(*) - COUNT(po.procedure_concept_id)                               AS nulos__procedure_concept_id,
    COUNT(*) - COUNT(po.procedure_date)                                     AS nulos__procedure_date,
    COUNT(DISTINCT po.person_id)                                            AS distintos__person_id,
    COUNT(DISTINCT po.visit_occurrence_id)                                  AS distintos__visit_occurrence_id,
    COUNT(DISTINCT po.procedure_concept_id)                                 AS distintos__procedure_concept_id,
    COUNT(*) FILTER (WHERE po.procedure_concept_id = 0)                     AS chequeo__concepto_0,
    COUNT(*) FILTER (WHERE po.procedure_concept_id IS NOT NULL AND c.concept_id IS NULL)
                                                                            AS chequeo__concepto_sin_traduccion,
    COUNT(*) FILTER (WHERE po.visit_occurrence_id IS NOT NULL AND v.visit_occurrence_id IS NULL)
                                                                            AS chequeo__visita_inexistente
FROM {schema}.procedure_occurrence po
LEFT JOIN {schema}.concept c ON c.concept_id = po.procedure_concept_id
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = po.visit_occurrence_id;
