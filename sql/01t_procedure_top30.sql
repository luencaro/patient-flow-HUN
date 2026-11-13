-- Los 30 procedimientos más frecuentes (sin el concepto 0), traducidos con su dominio y vocabulario.
WITH t AS (
    SELECT procedure_concept_id AS concepto, COUNT(*) AS n_registros
    FROM {schema}.procedure_occurrence
    WHERE procedure_concept_id <> 0
    GROUP BY procedure_concept_id
    ORDER BY n_registros DESC
    LIMIT 30
)
SELECT
    t.concepto,
    COALESCE(c.concept_name, '(sin concepto)')     AS procedimiento,
    c.vocabulary_id                                AS vocabulario,
    c.domain_id                                    AS dominio,
    t.n_registros
FROM t
LEFT JOIN {schema}.concept c ON c.concept_id = t.concepto
ORDER BY t.n_registros DESC;
