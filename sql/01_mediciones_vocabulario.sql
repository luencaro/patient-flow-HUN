-- Registros de measurement por vocabulario (para documentar la duplicación SNOMED/LOINC).
SELECT
    COALESCE(c.vocabulary_id, '(sin concepto)')    AS vocabulario,
    COUNT(*)                                       AS n_registros,
    COUNT(DISTINCT m.measurement_concept_id)       AS n_conceptos
FROM {schema}.measurement m
LEFT JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
GROUP BY COALESCE(c.vocabulary_id, '(sin concepto)')
ORDER BY n_registros DESC;
