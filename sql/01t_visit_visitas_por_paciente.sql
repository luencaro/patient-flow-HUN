-- Distribución de visitas por paciente: todas las visitas y solo urgencias (9203).
WITH pp AS (
    SELECT
        person_id,
        COUNT(*)                                          AS k_todas,
        COUNT(*) FILTER (WHERE visit_concept_id = 9203)   AS k_urgencias
    FROM {schema}.visit_occurrence
    GROUP BY person_id
), largo AS (
    SELECT 'todas' AS alcance, k_todas AS k FROM pp
    UNION ALL
    SELECT 'urgencias', k_urgencias FROM pp WHERE k_urgencias > 0
)
SELECT
    alcance,
    CASE
        WHEN k = 1 THEN '1'
        WHEN k = 2 THEN '2'
        WHEN k = 3 THEN '3'
        WHEN k <= 5 THEN '4-5'
        WHEN k <= 9 THEN '6-9'
        ELSE '10+'
    END                 AS visitas_por_paciente,
    COUNT(*)            AS n_pacientes,
    SUM(k)              AS n_visitas
FROM largo
GROUP BY 1, 2
ORDER BY 1, MIN(k);
