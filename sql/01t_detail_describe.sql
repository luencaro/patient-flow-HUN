-- describe() de visit_detail sobre la tabla completa: numéricas y fechas (sin columnas de ID).
-- Una sola fila; alias <estadístico>__<columna> (count, mean, std, min, p25, p50, p75, max).
-- Numéricas: percentiles con percentile_cont. Fechas: count, min, percentiles con percentile_disc y max.
SELECT
    COUNT(visit_detail_start_datetime) AS count__visit_detail_start_datetime
    , MIN(visit_detail_start_datetime) AS min__visit_detail_start_datetime
    , percentile_disc(0.25) WITHIN GROUP (ORDER BY visit_detail_start_datetime) AS p25__visit_detail_start_datetime
    , percentile_disc(0.50) WITHIN GROUP (ORDER BY visit_detail_start_datetime) AS p50__visit_detail_start_datetime
    , percentile_disc(0.75) WITHIN GROUP (ORDER BY visit_detail_start_datetime) AS p75__visit_detail_start_datetime
    , MAX(visit_detail_start_datetime) AS max__visit_detail_start_datetime
    , COUNT(visit_detail_end_datetime) AS count__visit_detail_end_datetime
    , MIN(visit_detail_end_datetime) AS min__visit_detail_end_datetime
    , percentile_disc(0.25) WITHIN GROUP (ORDER BY visit_detail_end_datetime) AS p25__visit_detail_end_datetime
    , percentile_disc(0.50) WITHIN GROUP (ORDER BY visit_detail_end_datetime) AS p50__visit_detail_end_datetime
    , percentile_disc(0.75) WITHIN GROUP (ORDER BY visit_detail_end_datetime) AS p75__visit_detail_end_datetime
    , MAX(visit_detail_end_datetime) AS max__visit_detail_end_datetime
FROM {schema}.visit_detail;
