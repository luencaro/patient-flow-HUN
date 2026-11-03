-- Etapas que empiezan más de 1 hora antes del inicio de su visita, por tipo de etapa y tipo de visita.
SELECT
    d.visit_detail_concept_id                                       AS concepto_etapa,
    COALESCE(ce.concept_name, '(sin concepto)')                     AS etapa,
    v.visit_concept_id                                              AS concepto_visita,
    COALESCE(cv.concept_name, '(sin concepto)')                     AS tipo_visita,
    COUNT(*)                                                        AS n,
    COUNT(*) FILTER (WHERE d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour')
                                                                    AS n_inicia_antes
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
LEFT JOIN {schema}.concept ce ON ce.concept_id = d.visit_detail_concept_id
LEFT JOIN {schema}.concept cv ON cv.concept_id = v.visit_concept_id
GROUP BY 1, 2, 3, 4
ORDER BY 1, 3;
