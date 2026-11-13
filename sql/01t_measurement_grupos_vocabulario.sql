-- Duplicación SNOMED/LOINC: se agrupan las mediciones por (visita, fecha y hora de la medición) y se
-- cuenta cuántos grupos tienen registros SNOMED y LOINC a la vez. Solo se devuelven agregados.
WITH m AS (
    SELECT m.visit_occurrence_id, m.measurement_datetime, c.vocabulary_id, m.measurement_concept_id
    FROM {schema}.measurement m
    LEFT JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
    WHERE m.visit_occurrence_id IS NOT NULL
      AND m.measurement_datetime IS NOT NULL
), g AS (
    SELECT
        visit_occurrence_id,
        measurement_datetime,
        COUNT(*)                                                AS k,
        COUNT(*) FILTER (WHERE vocabulary_id = 'SNOMED')        AS k_snomed,
        COUNT(*) FILTER (WHERE vocabulary_id = 'LOINC')         AS k_loinc
    FROM m
    GROUP BY visit_occurrence_id, measurement_datetime
)
SELECT
    CASE
        WHEN k_snomed > 0 AND k_loinc > 0 THEN '1 SNOMED y LOINC'
        WHEN k_snomed > 0                 THEN '2 solo SNOMED'
        WHEN k_loinc > 0                  THEN '3 solo LOINC'
        ELSE                                   '4 ni SNOMED ni LOINC'
    END                                                         AS categoria,
    COUNT(*)                                                    AS n_grupos,
    SUM(k)                                                      AS n_registros,
    COUNT(*) FILTER (WHERE k_snomed = k_loinc)                  AS n_grupos_mismo_numero
FROM g
GROUP BY 1
ORDER BY 1;
