-- Visitas cuyo inicio cae exactamente a medianoche, por tipo de visita.
SELECT
    v.visit_concept_id                             AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')     AS tipo_visita,
    COUNT(*)                                       AS n_visitas,
    COUNT(*) FILTER (WHERE date_trunc('day', v.visit_start_datetime) = v.visit_start_datetime)
                                                   AS n_medianoche,
    100.0 * COUNT(*) FILTER (WHERE date_trunc('day', v.visit_start_datetime) = v.visit_start_datetime)
          / COUNT(*)                               AS pct_medianoche
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY v.visit_concept_id, c.concept_name
ORDER BY n_visitas DESC;
