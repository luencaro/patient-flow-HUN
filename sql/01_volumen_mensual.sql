-- Visitas por mes de llegada y tipo de visita.
SELECT
    CAST(date_trunc('month', v.visit_start_datetime) AS date)   AS mes,
    v.visit_concept_id                                          AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')                  AS tipo_visita,
    COUNT(*)                                                    AS n_visitas
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY CAST(date_trunc('month', v.visit_start_datetime) AS date), v.visit_concept_id, c.concept_name
ORDER BY mes, concepto_visita;
