-- describe() de condition_occurrence sobre la tabla completa: numéricas y fechas (sin columnas de ID).
-- Una sola fila; alias <estadístico>__<columna> (count, mean, std, min, p25, p50, p75, max).
-- Numéricas: percentiles con percentile_cont. Fechas: count, min, percentiles con percentile_disc y max.
-- AVISO: tabla de decenas de millones de filas; los percentiles y conteos sobre la tabla completa
-- pueden tardar varios minutos.
SELECT
    COUNT(condition_start_datetime) AS count__condition_start_datetime
    , MIN(condition_start_datetime) AS min__condition_start_datetime
    , percentile_disc(0.25) WITHIN GROUP (ORDER BY condition_start_datetime) AS p25__condition_start_datetime
    , percentile_disc(0.50) WITHIN GROUP (ORDER BY condition_start_datetime) AS p50__condition_start_datetime
    , percentile_disc(0.75) WITHIN GROUP (ORDER BY condition_start_datetime) AS p75__condition_start_datetime
    , MAX(condition_start_datetime) AS max__condition_start_datetime
FROM {schema}.condition_occurrence;
