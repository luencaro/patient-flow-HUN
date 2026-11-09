-- Días entre el inicio de cada evento previo y la llegada, por tipo de etapa, en visitas de urgencias.
-- Evento previo: etapa que empieza más de 1 hora antes de la llegada. El hospital confirmó que las
-- fechas no están corridas: son eventos previos asociados a la visita.
-- dias_antes_llegada = FLOOR((llegada - inicio de la etapa) en días).
SELECT
    d.visit_detail_concept_id                                   AS concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')                  AS etapa,
    CAST(FLOOR(EXTRACT(EPOCH FROM (v.visit_start_datetime - d.visit_detail_start_datetime)) / 86400.0)
         AS integer)                                            AS dias_antes_llegada,
    COUNT(*)                                                    AS n_etapas
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
LEFT JOIN {schema}.concept c ON c.concept_id = d.visit_detail_concept_id
WHERE v.visit_concept_id = 9203
  AND d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour'
GROUP BY 1, 2, 3
ORDER BY 1, 3;
