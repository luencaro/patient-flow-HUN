-- Recorridos idénticos (notebook 03): pares de visitas 9203 de 2 pacientes distintos con la misma llegada y
-- la misma firma del recorrido, por diferencia de año de nacimiento, menores de edad (edad en la llegada
-- < 18) y si tienen el mismo sexo. Solo agregados.
WITH urg AS (
    SELECT visit_occurrence_id, person_id, visit_start_datetime AS llegada
    FROM {schema}.visit_occurrence
    WHERE visit_concept_id = 9203
), firmas AS (
    -- Firma del recorrido: todas las etapas de la visita con su tipo, inicio y fin exactos.
    SELECT u.visit_occurrence_id, u.person_id, u.llegada,
           COUNT(*) AS n_etapas,
           MD5(STRING_AGG(d.visit_detail_concept_id::text || '|' || d.visit_detail_start_datetime::text || '|'
                          || COALESCE(d.visit_detail_end_datetime::text, ''), ';'
                          ORDER BY d.visit_detail_start_datetime, d.visit_detail_end_datetime, d.visit_detail_concept_id))
               AS firma
    FROM urg u
    JOIN {schema}.visit_detail d ON d.visit_occurrence_id = u.visit_occurrence_id
    GROUP BY u.visit_occurrence_id, u.person_id, u.llegada
), pares AS (
    SELECT llegada, firma
    FROM firmas
    GROUP BY llegada, firma
    HAVING COUNT(*) = 2 AND COUNT(DISTINCT person_id) = 2
), por_par AS (
    SELECT
        MAX(p.year_of_birth) - MIN(p.year_of_birth)    AS dif_nacimiento,
        COUNT(p.year_of_birth)                         AS n_con_nacimiento,
        COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM f.llegada) - p.year_of_birth < 18) AS n_menores,
        COUNT(DISTINCT p.gender_concept_id) = 1 AND COUNT(p.gender_concept_id) = 2  AS mismo_sexo
    FROM firmas f
    JOIN pares pr ON pr.llegada = f.llegada AND pr.firma = f.firma
    JOIN {schema}.person p ON p.person_id = f.person_id
    GROUP BY f.llegada, f.firma
)
SELECT
    CASE
        WHEN n_con_nacimiento < 2 THEN '5 sin dato'
        WHEN dif_nacimiento = 0 THEN '1 0'
        WHEN dif_nacimiento <= 14 THEN '2 1-14'
        WHEN dif_nacimiento <= 44 THEN '3 15-44'
        ELSE '4 45+'
    END                                                AS diferencia_anio_nacimiento,
    CASE WHEN n_menores = 0 THEN '1 ninguno' WHEN n_menores = 1 THEN '2 uno' ELSE '3 ambos' END
                                                       AS menores_de_edad,
    mismo_sexo,
    COUNT(*)                                           AS n_pares
FROM por_par
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
