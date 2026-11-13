-- describe() de measurement sobre la tabla completa: numéricas y fechas (sin columnas de ID).
-- Una sola fila; alias <estadístico>__<columna> (count, mean, std, min, p25, p50, p75, max).
-- Numéricas: percentiles con percentile_cont. Fechas: count, min, percentiles con percentile_disc y max.
-- AVISO: tabla de decenas de millones de filas; los percentiles y conteos sobre la tabla completa
-- pueden tardar varios minutos.
SELECT
    COUNT(value_as_number) AS count__value_as_number
    , CAST(AVG(value_as_number) AS double precision) AS mean__value_as_number
    , CAST(STDDEV_SAMP(value_as_number) AS double precision) AS std__value_as_number
    , MIN(value_as_number) AS min__value_as_number
    , percentile_cont(0.25) WITHIN GROUP (ORDER BY value_as_number) AS p25__value_as_number
    , percentile_cont(0.50) WITHIN GROUP (ORDER BY value_as_number) AS p50__value_as_number
    , percentile_cont(0.75) WITHIN GROUP (ORDER BY value_as_number) AS p75__value_as_number
    , MAX(value_as_number) AS max__value_as_number
    , COUNT(measurement_datetime) AS count__measurement_datetime
    , MIN(measurement_datetime) AS min__measurement_datetime
    , percentile_disc(0.25) WITHIN GROUP (ORDER BY measurement_datetime) AS p25__measurement_datetime
    , percentile_disc(0.50) WITHIN GROUP (ORDER BY measurement_datetime) AS p50__measurement_datetime
    , percentile_disc(0.75) WITHIN GROUP (ORDER BY measurement_datetime) AS p75__measurement_datetime
    , MAX(measurement_datetime) AS max__measurement_datetime
FROM {schema}.measurement;
