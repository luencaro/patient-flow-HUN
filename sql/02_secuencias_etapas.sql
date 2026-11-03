-- Las 20 secuencias de etapas más comunes en visitas de urgencias (sin eventos previos, D2).
-- Códigos: URG = 9203 (ingreso por urgencias), MOV = 3045729 (movimiento o etapa),
-- PISO = 9201 (hospitalización en piso), AMB = 581479 (ingreso ambulatorio).
-- Las repeticiones consecutivas de la misma etapa se colapsan (URG, MOV, MOV, PISO -> URG > MOV > PISO).
-- Las visitas sin etapas no previas no aparecen (ver 02_completitud_mensual.sql).
WITH d AS (
    SELECT d.visit_occurrence_id, d.visit_detail_id, d.visit_detail_concept_id AS c,
           d.visit_detail_start_datetime AS ini
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND d.visit_detail_start_datetime >= v.visit_start_datetime - INTERVAL '1 hour'
), o AS (
    SELECT d.*,
           LAG(c) OVER (PARTITION BY visit_occurrence_id ORDER BY ini, visit_detail_id) AS c_prev
    FROM d
), s AS (
    SELECT
        visit_occurrence_id,
        STRING_AGG(
            CASE c
                WHEN 9203 THEN 'URG'
                WHEN 3045729 THEN 'MOV'
                WHEN 9201 THEN 'PISO'
                WHEN 581479 THEN 'AMB'
                ELSE CAST(c AS text)
            END,
            ' > ' ORDER BY ini, visit_detail_id
        ) AS secuencia
    FROM o
    WHERE c_prev IS NULL OR c_prev <> c
    GROUP BY visit_occurrence_id
)
SELECT
    secuencia,
    COUNT(*)                                        AS n_visitas,
    100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()        AS pct_visitas
FROM s
GROUP BY secuencia
ORDER BY n_visitas DESC
LIMIT 20;
