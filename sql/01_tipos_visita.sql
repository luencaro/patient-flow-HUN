-- Tipos de visita traducidos con concept.
SELECT
    v.visit_concept_id                             AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')     AS tipo_visita,
    c.vocabulary_id                                AS vocabulario,
    COUNT(*)                                       AS n_visitas,
    COUNT(DISTINCT v.person_id)                    AS n_pacientes
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY v.visit_concept_id, c.concept_name, c.vocabulary_id
ORDER BY n_visitas DESC;
