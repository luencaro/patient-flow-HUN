-- Recorridos idénticos entre pacientes distintos (notebook 03, regla recorridos_identicos_otro_paciente).
-- Fila por visita: su resultado solo se guarda en data/raw/ con consultar() y nunca se muestra.
-- Visitas 9203 agrupadas por (llegada, firma del recorrido); se conservan solo los grupos con exactamente
-- 2 visitas de 2 personas distintas. tiene_diagnostico: la visita tiene algún condition_occurrence
-- (conjunto preagregado de visitas, sin subconsulta correlacionada).
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
    SELECT llegada, firma
    FROM firmas
    GROUP BY llegada, firma
    HAVING COUNT(*) = 2 AND COUNT(DISTINCT person_id) = 2
), en_pares AS (
    SELECT f.visit_occurrence_id, f.llegada, f.firma, f.n_etapas
    FROM firmas f
    JOIN grupos g ON g.llegada = f.llegada AND g.firma = f.firma
), con_diagnostico AS (
    SELECT DISTINCT co.visit_occurrence_id
    FROM {schema}.condition_occurrence co
    WHERE co.visit_occurrence_id IN (SELECT visit_occurrence_id FROM en_pares)
)
SELECT
    p.visit_occurrence_id,
    MD5(p.llegada::text || p.firma)           AS grupo,
    (c.visit_occurrence_id IS NOT NULL)       AS tiene_diagnostico,
    p.n_etapas
FROM en_pares p
LEFT JOIN con_diagnostico c ON c.visit_occurrence_id = p.visit_occurrence_id;
