-- Pares SNOMED/LOINC más frecuentes en grupos (visita, fecha y hora) con exactamente un registro
-- SNOMED y uno LOINC: muestra que el mismo examen aparece con los dos vocabularios.
-- pct_mismo_valor: porcentaje de pares en los que ambos registros tienen el mismo value_as_number.
WITH m AS (
    SELECT m.visit_occurrence_id, m.measurement_datetime, m.measurement_concept_id, m.value_as_number,
           c.vocabulary_id
    FROM {schema}.measurement m
    JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
    WHERE m.visit_occurrence_id IS NOT NULL
      AND m.measurement_datetime IS NOT NULL
      AND c.vocabulary_id IN ('SNOMED', 'LOINC')
), g AS (
    SELECT
        visit_occurrence_id,
        measurement_datetime,
        MIN(measurement_concept_id) FILTER (WHERE vocabulary_id = 'SNOMED')    AS c_snomed,
        MIN(measurement_concept_id) FILTER (WHERE vocabulary_id = 'LOINC')     AS c_loinc,
        MIN(value_as_number) FILTER (WHERE vocabulary_id = 'SNOMED')           AS v_snomed,
        MIN(value_as_number) FILTER (WHERE vocabulary_id = 'LOINC')            AS v_loinc
    FROM m
    GROUP BY visit_occurrence_id, measurement_datetime
    HAVING COUNT(*) FILTER (WHERE vocabulary_id = 'SNOMED') = 1
       AND COUNT(*) FILTER (WHERE vocabulary_id = 'LOINC') = 1
), p AS (
    SELECT c_snomed, c_loinc, COUNT(*) AS n_pares,
           COUNT(*) FILTER (WHERE v_snomed = v_loinc) AS n_mismo_valor
    FROM g
    GROUP BY c_snomed, c_loinc
)
SELECT
    COALESCE(cs.concept_name, '(sin concepto)')    AS medicion_snomed,
    COALESCE(cl.concept_name, '(sin concepto)')    AS medicion_loinc,
    p.n_pares,
    p.n_mismo_valor,
    100.0 * p.n_mismo_valor / p.n_pares            AS pct_mismo_valor
FROM p
LEFT JOIN {schema}.concept cs ON cs.concept_id = p.c_snomed
LEFT JOIN {schema}.concept cl ON cl.concept_id = p.c_loinc
ORDER BY p.n_pares DESC
LIMIT 20;
