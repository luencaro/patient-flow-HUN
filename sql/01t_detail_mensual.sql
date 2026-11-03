-- Etapas por mes de inicio y tipo de etapa (traducido).
SELECT
    CAST(date_trunc('month', d.visit_detail_start_datetime) AS date)    AS mes,
    d.visit_detail_concept_id                                           AS concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')                          AS etapa,
    COUNT(*)                                                            AS n_etapas
FROM {schema}.visit_detail d
LEFT JOIN {schema}.concept c ON c.concept_id = d.visit_detail_concept_id
GROUP BY 1, 2, 3
ORDER BY 1, 2;
