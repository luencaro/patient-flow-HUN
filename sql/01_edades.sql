-- Edad al llegar (año de llegada - year_of_birth) en visitas de urgencias.
-- categoria marca los valores imposibles (D8); banda_5 agrupa las edades válidas en tramos de 5 años.
WITH e AS (
    SELECT CAST(EXTRACT(YEAR FROM v.visit_start_datetime) AS integer) - p.year_of_birth AS edad
    FROM {schema}.visit_occurrence v
    LEFT JOIN {schema}.person p ON p.person_id = v.person_id
    WHERE v.visit_concept_id = 9203
)
SELECT
    CASE
        WHEN edad IS NULL THEN 'sin_dato'
        WHEN edad < 0     THEN 'negativa'
        WHEN edad > 110   THEN 'mayor_110'
        WHEN edad < 18    THEN 'pediatria'
        WHEN edad < 65    THEN 'adulto'
        ELSE                   'adulto_mayor'
    END                                                         AS categoria,
    CASE WHEN edad BETWEEN 0 AND 110 THEN (edad / 5) * 5 END    AS banda_5,
    COUNT(*)                                                    AS n_visitas
FROM e
GROUP BY 1, 2
ORDER BY 2, 1;
