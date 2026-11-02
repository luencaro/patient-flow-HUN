-- Etapas que aparecen dentro de cada tipo de visita: número de detalles y de visitas distintas.
SELECT
    v.visit_concept_id                             AS concepto_visita,
    COALESCE(cv.concept_name, '(sin concepto)')    AS tipo_visita,
    d.visit_detail_concept_id                      AS concepto_etapa,
    COALESCE(cd.concept_name, '(sin concepto)')    AS etapa,
    COUNT(*)                                       AS n_detalles,
    COUNT(DISTINCT d.visit_occurrence_id)          AS n_visitas
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
LEFT JOIN {schema}.concept cv ON cv.concept_id = v.visit_concept_id
LEFT JOIN {schema}.concept cd ON cd.concept_id = d.visit_detail_concept_id
GROUP BY v.visit_concept_id, cv.concept_name, d.visit_detail_concept_id, cd.concept_name
ORDER BY v.visit_concept_id, n_detalles DESC;
