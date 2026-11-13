-- Ingresos por urgencias (etapa 9203 no previa de visitas 9203) por trimestre de inicio del ingreso:
-- total, de más de 22 minutos y de más de 24 horas. Todos los trimestres presentes en los datos.
SELECT
    CAST(date_trunc('quarter', d.visit_detail_start_datetime) AS date)                          AS trimestre,
    COUNT(*)                                                                                    AS n,
    COUNT(*) FILTER (WHERE d.visit_detail_end_datetime - d.visit_detail_start_datetime > INTERVAL '22 minutes')
                                                                                                AS n_mas_22_min,
    COUNT(*) FILTER (WHERE d.visit_detail_end_datetime - d.visit_detail_start_datetime > INTERVAL '24 hours')
                                                                                                AS n_mas_24_h
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
WHERE v.visit_concept_id = 9203
  AND d.visit_detail_concept_id = 9203
  AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
GROUP BY 1
ORDER BY 1;
