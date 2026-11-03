-- Sexo, raza y etnia de las personas, traducidos con concept.
WITH v AS (
    SELECT 'sexo' AS variable, gender_concept_id AS concepto FROM {schema}.person
    UNION ALL
    SELECT 'raza', race_concept_id FROM {schema}.person
    UNION ALL
    SELECT 'etnia', ethnicity_concept_id FROM {schema}.person
)
SELECT
    v.variable,
    v.concepto,
    COALESCE(c.concept_name, '(sin concepto)')     AS nombre,
    COUNT(*)                                       AS n_personas
FROM v
LEFT JOIN {schema}.concept c ON c.concept_id = v.concepto
GROUP BY v.variable, v.concepto, c.concept_name
ORDER BY v.variable, n_personas DESC;
