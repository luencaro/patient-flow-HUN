-- Mediciones por mes (measurement_datetime) y vocabulario del concepto, con cuántas tienen valor numérico.
SELECT
    CAST(date_trunc('month', m.measurement_datetime) AS date)       AS mes,
    CASE
        WHEN m.measurement_concept_id = 0 THEN 'concepto 0'
        ELSE COALESCE(c.vocabulary_id, '(sin concepto)')
    END                                                             AS vocabulario,
    COUNT(*)                                                        AS n_registros,
    COUNT(m.value_as_number)                                        AS n_con_valor
FROM {schema}.measurement m
LEFT JOIN {schema}.concept c ON c.concept_id = m.measurement_concept_id
GROUP BY 1, 2
ORDER BY 1, 2;
