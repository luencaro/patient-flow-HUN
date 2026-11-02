-- Histograma de días de desplazamiento por etapa, en visitas de urgencias.
-- Solo etapas desplazadas (D2): inicio más de 1 hora antes de la llegada.
-- dias_desplazamiento = FLOOR((llegada - inicio de la etapa) en días).
SELECT
    d.visit_detail_concept_id                                   AS concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')                  AS etapa,
    CAST(FLOOR(EXTRACT(EPOCH FROM (v.visit_start_datetime - d.visit_detail_start_datetime)) / 86400.0)
         AS integer)                                            AS dias_desplazamiento,
    COUNT(*)                                                    AS n_detalles
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
LEFT JOIN {schema}.concept c ON c.concept_id = d.visit_detail_concept_id
WHERE v.visit_concept_id = 9203
  AND d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour'
GROUP BY d.visit_detail_concept_id, c.concept_name,
         CAST(FLOOR(EXTRACT(EPOCH FROM (v.visit_start_datetime - d.visit_detail_start_datetime)) / 86400.0)
              AS integer)
ORDER BY concepto_etapa, dias_desplazamiento;
