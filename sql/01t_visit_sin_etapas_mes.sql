-- Visitas sin ninguna etapa (visit_detail) por mes de inicio y tipo de visita. Todos los meses presentes.
SELECT
    CAST(date_trunc('month', v.visit_start_datetime) AS date)                AS mes,
    v.visit_concept_id                                                       AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')                               AS tipo_visita,
    COUNT(*)                                                                 AS n,
    COUNT(*) FILTER (WHERE d.visit_occurrence_id IS NULL)                    AS n_sin_etapas
FROM {schema}.visit_occurrence v
LEFT JOIN (SELECT DISTINCT visit_occurrence_id FROM {schema}.visit_detail) d
       ON d.visit_occurrence_id = v.visit_occurrence_id
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY 1, 2, 3
ORDER BY 1, 2;
