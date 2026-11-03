-- value_as_number de las 10 mediciones (concepto distinto de 0) con más registros con valor numérico.
-- Percentiles 0, 1, 25, 50, 75, 99 y 100, y n_atipicos: valores fuera de 1,5 veces el rango intercuartílico.
WITH top AS (
    SELECT measurement_concept_id AS concepto, COUNT(*) AS n
    FROM {schema}.measurement
    WHERE measurement_concept_id <> 0
      AND value_as_number IS NOT NULL
    GROUP BY measurement_concept_id
    ORDER BY n DESC
    LIMIT 10
), m AS (
    SELECT m.measurement_concept_id AS concepto, m.value_as_number AS valor
    FROM {schema}.measurement m
    JOIN top ON top.concepto = m.measurement_concept_id
    WHERE m.value_as_number IS NOT NULL
), p AS (
    SELECT
        concepto,
        COUNT(*)                                                AS n,
        MIN(valor)                                              AS p00,
        percentile_cont(0.01) WITHIN GROUP (ORDER BY valor)     AS p01,
        percentile_cont(0.25) WITHIN GROUP (ORDER BY valor)     AS p25,
        percentile_cont(0.50) WITHIN GROUP (ORDER BY valor)     AS p50,
        percentile_cont(0.75) WITHIN GROUP (ORDER BY valor)     AS p75,
        percentile_cont(0.99) WITHIN GROUP (ORDER BY valor)     AS p99,
        MAX(valor)                                              AS p100
    FROM m
    GROUP BY concepto
), a AS (
    SELECT m.concepto, COUNT(*) AS n_atipicos
    FROM m
    JOIN p ON p.concepto = m.concepto
    WHERE m.valor < p.p25 - 1.5 * (p.p75 - p.p25) OR m.valor > p.p75 + 1.5 * (p.p75 - p.p25)
    GROUP BY m.concepto
)
SELECT
    p.concepto,
    COALESCE(c.concept_name, '(sin concepto)')     AS medicion,
    c.vocabulary_id                                AS vocabulario,
    p.n, p.p00, p.p01, p.p25, p.p50, p.p75, p.p99, p.p100,
    COALESCE(a.n_atipicos, 0)                      AS n_atipicos
FROM p
LEFT JOIN a ON a.concepto = p.concepto
LEFT JOIN {schema}.concept c ON c.concept_id = p.concepto
ORDER BY p.n DESC;
