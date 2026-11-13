-- Recorridos idénticos (notebook 03): pares de visitas 9203 de 2 pacientes distintos con la misma llegada
-- y la misma firma del recorrido, por mes de llegada. Solo agregados.
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
)
SELECT
    DATE_TRUNC('month', llegada)::date                 AS mes,
    COUNT(*)                                           AS n_pares
FROM pares
GROUP BY 1
ORDER BY 1;
