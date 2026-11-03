-- Visitas por tipo, día de la semana (0 = lunes ... 6 = domingo) y hora de inicio.
SELECT
    v.visit_concept_id                                                  AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')                          AS tipo_visita,
    CAST(EXTRACT(ISODOW FROM v.visit_start_datetime) AS integer) - 1    AS dia_semana,
    CAST(EXTRACT(HOUR FROM v.visit_start_datetime) AS integer)          AS hora,
    COUNT(*)                                                            AS n_visitas
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.concept c ON c.concept_id = v.visit_concept_id
GROUP BY 1, 2, 3, 4
ORDER BY 1, 3, 4;
