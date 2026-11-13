-- ¿Los fines con fracción de segundo se concentran en pocos instantes repetidos? Solo agregados:
-- para los 20 instantes más repetidos, cuántas etapas comparten ese mismo instante (sin mostrar el
-- instante), y en todas las filas el total de instantes distintos y de etapas con fracción de segundo.
WITH f AS (
    SELECT d.visit_detail_end_datetime AS fin
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND d.visit_detail_end_datetime IS NOT NULL
      AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
      AND MOD(CAST(EXTRACT(MICROSECONDS FROM d.visit_detail_end_datetime) AS bigint), 1000000) <> 0
), i AS (
    SELECT fin, COUNT(*) AS n FROM f GROUP BY fin
), r AS (
    SELECT n, ROW_NUMBER() OVER (ORDER BY n DESC) AS rango FROM i
), t AS (
    SELECT COUNT(*) AS instantes_distintos, SUM(n) AS n_total FROM i
)
SELECT r.rango, r.n AS n_etapas, t.instantes_distintos, t.n_total
FROM r CROSS JOIN t
WHERE r.rango <= 20
ORDER BY r.rango;
