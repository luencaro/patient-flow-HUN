-- Histograma de días entre el fin de una etapa 9201 previa (que termina antes de la llegada) y la llegada
-- a urgencias. Evento previo: inicio más de 1 hora antes de la llegada.
SELECT
    CAST(FLOOR(EXTRACT(EPOCH FROM (v.visit_start_datetime - d.visit_detail_end_datetime)) / 86400.0)
         AS integer)                                            AS dias_fin_a_llegada,
    COUNT(*)                                                    AS n_etapas
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
WHERE v.visit_concept_id = 9203
  AND d.visit_detail_concept_id = 9201
  AND d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour'
  AND d.visit_detail_end_datetime < v.visit_start_datetime
GROUP BY 1
ORDER BY 1;
