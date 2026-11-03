-- Conceptos cuyo nombre es 'Emergency department Consult note' (D11) y cuántos procedimientos los usan.
-- Si no devuelve filas, nota_consulta_urg queda en FALSE para todos los episodios: revisar el nombre.
SELECT
    c.concept_id                AS concepto,
    c.concept_name              AS nombre,
    c.domain_id                 AS dominio,
    c.vocabulary_id             AS vocabulario,
    COUNT(po.procedure_concept_id) AS n_registros
FROM {schema}.concept c
LEFT JOIN {schema}.procedure_occurrence po ON po.procedure_concept_id = c.concept_id
WHERE c.concept_name = 'Emergency department Consult note'
GROUP BY 1, 2, 3, 4;
