-- Fines de etapa con fracción de segundo (microsegundos distintos de 0), por tipo de etapa.
-- Solo etapas no previas de visitas de urgencias (9203) con fin registrado.
SELECT
    d.visit_detail_concept_id                                                               AS concepto_etapa,
    COUNT(*)                                                                                AS n,
    COUNT(*) FILTER (WHERE MOD(CAST(EXTRACT(MICROSECONDS FROM d.visit_detail_end_datetime) AS bigint), 1000000) <> 0)
                                                                                            AS n_fraccion
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
WHERE v.visit_concept_id = 9203
  AND d.visit_detail_end_datetime IS NOT NULL
  AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
GROUP BY 1
ORDER BY 1;
