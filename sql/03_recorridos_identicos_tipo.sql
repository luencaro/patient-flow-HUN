-- Recorridos idénticos (notebook 03): grupos de 2 o más visitas 9203 con la misma llegada y la misma firma
-- del recorrido, por tipo de grupo, tramo de etapas y si coinciden año de nacimiento y sexo.
-- Solo agregados: grupos, visitas y personas distintas.
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
), grupos AS (
    SELECT f.llegada, f.firma,
           COUNT(*)                                    AS n_visitas,
           COUNT(DISTINCT f.person_id)                 AS n_personas,
           MAX(f.n_etapas)                             AS n_etapas,
           COUNT(DISTINCT p.year_of_birth) <= 1 AND COUNT(DISTINCT p.gender_concept_id) <= 1
                                                       AS coinciden_nacimiento_sexo
    FROM firmas f
    JOIN {schema}.person p ON p.person_id = f.person_id
    GROUP BY f.llegada, f.firma
    HAVING COUNT(*) >= 2
), clasificados AS (
    SELECT llegada, firma, n_visitas, coinciden_nacimiento_sexo,
           CASE
               WHEN n_personas = 1 THEN '1 mismo paciente'
               WHEN n_visitas = 2 AND n_personas = 2 THEN '2 par de pacientes distintos'
               ELSE '3 más de 2 visitas'
           END                                         AS tipo_grupo,
           CASE WHEN n_etapas = 1 THEN '1' WHEN n_etapas <= 3 THEN '2-3' ELSE '4+' END AS tramo_etapas
    FROM grupos
)
SELECT
    c.tipo_grupo,
    c.tramo_etapas,
    c.coinciden_nacimiento_sexo,
    COUNT(DISTINCT (c.llegada, c.firma))               AS n_grupos,
    COUNT(*)                                           AS n_visitas,
    COUNT(DISTINCT f.person_id)                        AS n_personas
FROM clasificados c
JOIN firmas f ON f.llegada = c.llegada AND f.firma = c.firma
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
