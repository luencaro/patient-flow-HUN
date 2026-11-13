-- describe() de procedure_occurrence sobre la tabla completa: numéricas y fechas (sin columnas de ID).
-- Una sola fila; alias <estadístico>__<columna> (count, mean, std, min, p25, p50, p75, max).
-- Numéricas: percentiles con percentile_cont. Fechas: count, min, percentiles con percentile_disc y max.
-- AVISO: tabla de decenas de millones de filas; los percentiles y conteos sobre la tabla completa
-- pueden tardar varios minutos.
SELECT
    COUNT(procedure_date) AS count__procedure_date
    , MIN(procedure_date) AS min__procedure_date
    , percentile_disc(0.25) WITHIN GROUP (ORDER BY procedure_date) AS p25__procedure_date
    , percentile_disc(0.50) WITHIN GROUP (ORDER BY procedure_date) AS p50__procedure_date
    , percentile_disc(0.75) WITHIN GROUP (ORDER BY procedure_date) AS p75__procedure_date
    , MAX(procedure_date) AS max__procedure_date
FROM {schema}.procedure_occurrence;
