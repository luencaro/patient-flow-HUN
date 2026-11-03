-- Diagnósticos por mes (condition_start_datetime) y tipo de visita, con cuántos tienen concepto 0.
SELECT
    CAST(date_trunc('month', co.condition_start_datetime) AS date)  AS mes,
    COALESCE(c.concept_name, '(sin visita)')                        AS tipo_visita,
    COUNT(*)                                                        AS n_registros,
    COUNT(*) FILTER (WHERE co.condition_concept_id = 0)             AS n_concepto_0
FROM {schema}.condition_occurrence co
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = co.visit_occurrence_id
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY 1, 2
ORDER BY 1, 2;
