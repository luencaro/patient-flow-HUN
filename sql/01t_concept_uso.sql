-- Conceptos usados en la base, por tabla, dominio y vocabulario (tablas completas).
-- conceptos_distintos cuenta conceptos (no personas), por eso no lleva el prefijo n_.
WITH u AS (
    SELECT 'person (sexo)' AS tabla, gender_concept_id AS concepto, COUNT(*) AS n
    FROM {schema}.person GROUP BY gender_concept_id
    UNION ALL
    SELECT 'person (raza)', race_concept_id, COUNT(*)
    FROM {schema}.person GROUP BY race_concept_id
    UNION ALL
    SELECT 'person (etnia)', ethnicity_concept_id, COUNT(*)
    FROM {schema}.person GROUP BY ethnicity_concept_id
    UNION ALL
    SELECT 'visit_occurrence', visit_concept_id, COUNT(*)
    FROM {schema}.visit_occurrence GROUP BY visit_concept_id
    UNION ALL
    SELECT 'visit_detail', visit_detail_concept_id, COUNT(*)
    FROM {schema}.visit_detail GROUP BY visit_detail_concept_id
    UNION ALL
    SELECT 'condition_occurrence', condition_concept_id, COUNT(*)
    FROM {schema}.condition_occurrence GROUP BY condition_concept_id
    UNION ALL
    SELECT 'procedure_occurrence', procedure_concept_id, COUNT(*)
    FROM {schema}.procedure_occurrence GROUP BY procedure_concept_id
    UNION ALL
    SELECT 'measurement', measurement_concept_id, COUNT(*)
    FROM {schema}.measurement GROUP BY measurement_concept_id
)
SELECT
    u.tabla,
    COALESCE(c.domain_id, '(sin concepto)')        AS dominio,
    COALESCE(c.vocabulary_id, '(sin concepto)')    AS vocabulario,
    COUNT(*)                                       AS conceptos_distintos,
    SUM(u.n)                                       AS n_registros
FROM u
LEFT JOIN {schema}.concept c ON c.concept_id = u.concepto
GROUP BY 1, 2, 3
ORDER BY 1, n_registros DESC;
