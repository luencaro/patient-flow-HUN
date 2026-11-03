-- Duración de las etapas (visit_detail_end_datetime - visit_detail_start_datetime) por tipo de etapa.
-- Conteos de duraciones nulas, negativas, cero y positivas; percentiles (0, 1, 25, 50, 75, 99 y 100)
-- en horas sobre las duraciones POSITIVAS (para graficarlas en escala log), y n_atipicos: duraciones
-- positivas fuera de 1,5 veces el rango intercuartílico.
WITH e AS (
    SELECT
        d.visit_detail_concept_id AS concepto_etapa,
        CAST(EXTRACT(EPOCH FROM (d.visit_detail_end_datetime - d.visit_detail_start_datetime)) / 3600.0
             AS double precision) AS horas
    FROM {schema}.visit_detail d
), p AS (
    SELECT
        concepto_etapa,
        COUNT(*)                                                    AS n,
        COUNT(*) FILTER (WHERE horas IS NULL)                       AS n_sin_fin,
        COUNT(*) FILTER (WHERE horas < 0)                           AS n_negativas,
        COUNT(*) FILTER (WHERE horas = 0)                           AS n_cero,
        COUNT(*) FILTER (WHERE horas > 0)                           AS n_positivas,
        MIN(horas) FILTER (WHERE horas > 0)                         AS p00,
        percentile_cont(0.01) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p01,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p25,
        percentile_cont(0.50) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p50,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p75,
        percentile_cont(0.99) WITHIN GROUP (ORDER BY horas) FILTER (WHERE horas > 0) AS p99,
        MAX(horas) FILTER (WHERE horas > 0)                         AS p100
    FROM e
    GROUP BY concepto_etapa
), a AS (
    SELECT e.concepto_etapa, COUNT(*) AS n_atipicos
    FROM e
    JOIN p ON p.concepto_etapa = e.concepto_etapa
    WHERE e.horas > 0
      AND (e.horas < p.p25 - 1.5 * (p.p75 - p.p25) OR e.horas > p.p75 + 1.5 * (p.p75 - p.p25))
    GROUP BY e.concepto_etapa
)
SELECT
    p.concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')     AS etapa,
    p.n, p.n_sin_fin, p.n_negativas, p.n_cero, p.n_positivas,
    p.p00, p.p01, p.p25, p.p50, p.p75, p.p99, p.p100,
    COALESCE(a.n_atipicos, 0)                      AS n_atipicos
FROM p
LEFT JOIN a ON a.concepto_etapa = p.concepto_etapa
LEFT JOIN {schema}.concept c ON c.concept_id = p.concepto_etapa
ORDER BY p.n DESC;
