-- Edad exacta al llegar (año de llegada - year_of_birth) en TODAS las visitas de urgencias (9203), por sexo.
-- Sin ningún límite: incluye edades negativas, mayores a 110 o sin dato (edad NULL), que se muestran como hallazgo.
SELECT
    CAST(EXTRACT(YEAR FROM v.visit_start_datetime) AS integer) - p.year_of_birth  AS edad,
    COALESCE(c.concept_name, 'Sin dato')                                         AS sexo,
    COUNT(*)                                                                     AS n_visitas
FROM {schema}.visit_occurrence v
LEFT JOIN {schema}.person p ON p.person_id = v.person_id
LEFT JOIN {schema}.concept c ON c.concept_id = p.gender_concept_id
WHERE v.visit_concept_id = 9203
GROUP BY 1, 2
ORDER BY 1, 2;
