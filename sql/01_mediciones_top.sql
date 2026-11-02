-- Las 50 mediciones más frecuentes, con nombre, vocabulario y dominio.
SELECT
    m.measurement_concept_id                       AS concepto_medicion,
    COALESCE(c.concept_name, '(sin concepto)')     AS medicion,
    c.vocabulary_id                                AS vocabulario,
    c.domain_id                                    AS dominio,
    COUNT(*)                                       AS n_registros,
    COUNT(m.value_as_number)                       AS n_con_valor,
    COUNT(DISTINCT m.visit_occurrence_id)          AS n_visitas
FROM {schema}.measurement m
LEFT JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
GROUP BY m.measurement_concept_id, c.concept_name, c.vocabulary_id, c.domain_id
ORDER BY n_registros DESC
LIMIT 50;
