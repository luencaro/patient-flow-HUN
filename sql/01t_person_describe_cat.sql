-- describe() de person sobre la tabla completa: categóricas (*_concept_id).
-- Una fila por columna: count (no nulos), unique (valores distintos no nulos), top (valor más
-- frecuente, traducido con concept) y freq (veces que aparece el top).
WITH f AS (
    SELECT 'gender_concept_id' AS columna, gender_concept_id AS valor, COUNT(*) AS n FROM {schema}.person GROUP BY gender_concept_id
    UNION ALL
    SELECT 'race_concept_id' AS columna, race_concept_id AS valor, COUNT(*) AS n FROM {schema}.person GROUP BY race_concept_id
    UNION ALL
    SELECT 'ethnicity_concept_id' AS columna, ethnicity_concept_id AS valor, COUNT(*) AS n FROM {schema}.person GROUP BY ethnicity_concept_id
), g AS (
    SELECT columna, valor, n,
           ROW_NUMBER() OVER (PARTITION BY columna ORDER BY n DESC, valor) AS puesto
    FROM f
    WHERE valor IS NOT NULL
), r AS (
    SELECT
        columna,
        SUM(n)                                 AS count,
        COUNT(*)                               AS "unique",
        MAX(valor) FILTER (WHERE puesto = 1)   AS top_concepto,
        MAX(n) FILTER (WHERE puesto = 1)       AS freq
    FROM g
    GROUP BY columna
)
SELECT
    r.columna,
    r.count,
    r."unique",
    COALESCE(c.concept_name, '(sin concepto)') || ' (' || CAST(r.top_concepto AS text) || ')' AS top,
    r.freq
FROM r
LEFT JOIN {schema}.concept c ON c.concept_id = r.top_concepto
ORDER BY r.columna;
