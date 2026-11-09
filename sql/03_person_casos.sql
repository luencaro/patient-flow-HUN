-- Casos de person para el notebook 03: año de nacimiento imposible y sexo sin dato.
-- Por categoría: personas, personas con alguna visita de urgencias (9203) y visitas de urgencias.
-- Solo agregados.
WITH vu AS (
    SELECT person_id, COUNT(*) AS n_visitas
    FROM {schema}.visit_occurrence
    WHERE visit_concept_id = 9203
    GROUP BY person_id
), p AS (
    SELECT p.year_of_birth, p.gender_concept_id, COALESCE(vu.n_visitas, 0) AS n_visitas_urg
    FROM {schema}.person p
    LEFT JOIN vu ON vu.person_id = p.person_id
)
SELECT
    'anio_nacimiento'                                       AS caso,
    CASE
        WHEN year_of_birth IS NULL THEN '5 sin dato'
        WHEN year_of_birth = 1 THEN '1 año 1'
        WHEN year_of_birth < 1900 THEN '2 entre 2 y 1899'
        WHEN year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE) THEN '4 futuro'
        ELSE '3 desde 1900'
    END                                                     AS categoria,
    COUNT(*)                                                AS n_personas,
    COUNT(*) FILTER (WHERE n_visitas_urg > 0)               AS n_personas_con_urgencias,
    SUM(n_visitas_urg)                                      AS n_visitas_urgencias
FROM p
GROUP BY 1, 2
UNION ALL
SELECT
    'sexo',
    CASE
        WHEN gender_concept_id IS NULL THEN '3 nulo'
        WHEN gender_concept_id = 0 THEN '2 concepto 0'
        ELSE '1 con concepto'
    END,
    COUNT(*),
    COUNT(*) FILTER (WHERE n_visitas_urg > 0),
    SUM(n_visitas_urg)
FROM p
GROUP BY 1, 2
ORDER BY 1, 2;
