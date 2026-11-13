-- describe() de person sobre la tabla completa: numéricas y fechas (sin columnas de ID).
-- Una sola fila; alias <estadístico>__<columna> (count, mean, std, min, p25, p50, p75, max).
-- Numéricas: percentiles con percentile_cont. Fechas: count, min, percentiles con percentile_disc y max.
SELECT
    COUNT(year_of_birth) AS count__year_of_birth
    , CAST(AVG(year_of_birth) AS double precision) AS mean__year_of_birth
    , CAST(STDDEV_SAMP(year_of_birth) AS double precision) AS std__year_of_birth
    , MIN(year_of_birth) AS min__year_of_birth
    , percentile_cont(0.25) WITHIN GROUP (ORDER BY year_of_birth) AS p25__year_of_birth
    , percentile_cont(0.50) WITHIN GROUP (ORDER BY year_of_birth) AS p50__year_of_birth
    , percentile_cont(0.75) WITHIN GROUP (ORDER BY year_of_birth) AS p75__year_of_birth
    , MAX(year_of_birth) AS max__year_of_birth
FROM {schema}.person;
