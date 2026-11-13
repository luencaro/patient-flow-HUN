-- Duración de las etapas no previas de las visitas de urgencias (9203), por tipo de etapa y para todas.
-- Etapa no previa: no empieza más de 1 hora antes de la llegada (misma regla que visitas_urgencias.sql).
-- Por grupo: conteos de duraciones nulas, negativas, cero y positivas; percentiles 50, 99 y 99,9 de las
-- positivas; cuartiles del logaritmo natural de las positivas y límite de Tukey sobre el logaritmo
-- (exp(Q3 + 3 × RIC)); y cuántas etapas superan el percentil 99,9 y el límite de Tukey.
WITH d AS (
    SELECT
        d.visit_detail_concept_id AS c,
        CAST(EXTRACT(EPOCH FROM (d.visit_detail_end_datetime - d.visit_detail_start_datetime)) / 3600.0
             AS double precision) AS horas
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
), dd AS (
    SELECT CAST(c AS text) AS etapa, horas FROM d
    UNION ALL
    SELECT 'todas', horas FROM d
), lim AS (
    SELECT
        etapa,
        COUNT(*)                                                                    AS n,
        COUNT(*) FILTER (WHERE horas IS NULL)                                       AS n_sin_fin,
        COUNT(*) FILTER (WHERE horas < 0)                                           AS n_negativas,
        COUNT(*) FILTER (WHERE horas = 0)                                           AS n_dur_0,
        COUNT(*) FILTER (WHERE horas > 0)                                           AS n_positivas,
        percentile_cont(0.50) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0)  AS p50_h,
        percentile_cont(0.99) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0)  AS p99_h,
        percentile_cont(0.999) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p99_9_h,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY LN(GREATEST(horas, 1e-12))) FILTER (WHERE horas > 0) AS q1_log,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY LN(GREATEST(horas, 1e-12))) FILTER (WHERE horas > 0) AS q3_log,
        MAX(horas)                                                                  AS max_h
    FROM dd
    GROUP BY etapa
), lim2 AS (
    SELECT lim.*, EXP(q3_log + 3 * (q3_log - q1_log)) AS tukey_log_h
    FROM lim
), cnt AS (
    SELECT
        dd.etapa,
        COUNT(*) FILTER (WHERE dd.horas > l.p99_9_h)        AS n_sobre_p99_9,
        COUNT(*) FILTER (WHERE dd.horas > l.tukey_log_h)    AS n_sobre_tukey_log
    FROM dd
    JOIN lim2 l ON l.etapa = dd.etapa
    GROUP BY dd.etapa
)
SELECT l.*, c.n_sobre_p99_9, c.n_sobre_tukey_log
FROM lim2 l
JOIN cnt c ON c.etapa = l.etapa
ORDER BY l.etapa;
