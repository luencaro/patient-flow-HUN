-- Procedimientos por dominio del concepto y tipo de visita.
SELECT
    COALESCE(cv.concept_name, '(sin visita)')      AS tipo_visita,
    COALESCE(cp.domain_id, '(sin concepto)')       AS dominio,
    COUNT(*)                                       AS n_registros
FROM {schema}.procedure_occurrence po
LEFT JOIN {schema}.concept cp ON cp.concept_id = po.procedure_concept_id
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = po.visit_occurrence_id
LEFT JOIN {schema}.concept cv ON cv.concept_id = v.visit_concept_id
GROUP BY 1, 2
ORDER BY 1, n_registros DESC;
