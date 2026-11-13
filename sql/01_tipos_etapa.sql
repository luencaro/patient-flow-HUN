-- Tipos de etapa (visit_detail) traducidos con concept.
SELECT
    d.visit_detail_concept_id                      AS concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')     AS etapa,
    c.vocabulary_id                                AS vocabulario,
    COUNT(*)                                       AS n_detalles,
    COUNT(DISTINCT d.visit_occurrence_id)          AS n_visitas
FROM {schema}.visit_detail d
LEFT JOIN {schema}.concept c ON c.concept_id = d.visit_detail_concept_id
GROUP BY d.visit_detail_concept_id, c.concept_name, c.vocabulary_id
ORDER BY n_detalles DESC;
