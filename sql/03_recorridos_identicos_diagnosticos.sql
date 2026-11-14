-- Recorridos idénticos (notebook 03): pares de visitas 9203 (exactamente 2 visitas con la misma llegada y
-- la misma firma del recorrido) por tipo de par y comparación de sus diagnósticos. Los diagnósticos de una
-- visita se resumen como el conjunto de condition_concept_id distintos. Solo agregados.
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
    SELECT llegada, firma,
           CASE WHEN COUNT(DISTINCT person_id) = 1 THEN '1 mismo paciente' ELSE '2 pacientes distintos' END
               AS tipo_par
    FROM firmas
    GROUP BY llegada, firma
    HAVING COUNT(*) = 2
), visitas_pares AS (
    SELECT f.visit_occurrence_id, f.llegada, f.firma, p.tipo_par
    FROM firmas f
    JOIN pares p ON p.llegada = f.llegada AND p.firma = f.firma
), diagnosticos AS (
    SELECT co.visit_occurrence_id,
           MD5(STRING_AGG(DISTINCT co.condition_concept_id::text, ',' ORDER BY co.condition_concept_id::text))
               AS firma_diagnosticos
    FROM {schema}.condition_occurrence co
    WHERE co.visit_occurrence_id IN (SELECT visit_occurrence_id FROM visitas_pares)
    GROUP BY co.visit_occurrence_id
), por_par AS (
    SELECT v.tipo_par,
           COUNT(d.firma_diagnosticos)                 AS n_con_diagnostico,
           COUNT(DISTINCT d.firma_diagnosticos)        AS n_conjuntos
    FROM visitas_pares v
    LEFT JOIN diagnosticos d ON d.visit_occurrence_id = v.visit_occurrence_id
    GROUP BY v.tipo_par, v.llegada, v.firma
)
SELECT
    tipo_par,
    CASE
        WHEN n_con_diagnostico = 0 THEN '1 ninguna tiene'
        WHEN n_con_diagnostico = 1 THEN '2 solo una tiene'
        WHEN n_conjuntos = 1 THEN '3 mismos diagnósticos'
        ELSE '4 diagnósticos distintos'
    END                                                AS diagnosticos,
    COUNT(*)                                           AS n_pares
FROM por_par
GROUP BY 1, 2
ORDER BY 1, 2;
