-- Perfil de los ingresos por urgencias (etapa 9203) según su duración. Solo etapas no previas de visitas
-- de urgencias (9203); una fila por tramo de duración del ingreso: hasta 22 min, 22 min a 24 h, 1 a 11 días,
-- más de 11 días y sin fin.
-- Por tramo: ingresos y, en conteo (n_) y porcentaje (pct_), los que
--   con_movimientos: la visita tiene etapas 3045729.
--   con_piso: la visita tiene etapas 9201.
--   fin_igual_ultimo_mov: el fin del ingreso es igual al fin del último movimiento 3045729.
--   fija_salida: el ingreso fija la salida de urgencias (su fin es mayor o igual al fin del último
--     movimiento, o la visita no tiene movimientos).
--   fin_igual_inicio_piso / fin_igual_fin_piso: el fin del ingreso es igual al inicio o al fin del piso.
--   fin_fraccion: el fin del ingreso tiene fracción de segundo.
WITH d AS (
    SELECT
        d.visit_occurrence_id,
        d.visit_detail_concept_id     AS c,
        d.visit_detail_start_datetime AS ini,
        d.visit_detail_end_datetime   AS fin
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
      AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
), visita AS (
    SELECT
        visit_occurrence_id,
        COALESCE(BOOL_OR(c = 3045729), FALSE)       AS con_mov,
        MAX(fin) FILTER (WHERE c = 3045729)         AS fin_mov,
        COALESCE(BOOL_OR(c = 9201), FALSE)          AS con_piso,
        MIN(ini) FILTER (WHERE c = 9201)            AS inicio_piso,
        MAX(fin) FILTER (WHERE c = 9201)            AS fin_piso
    FROM d
    GROUP BY visit_occurrence_id
), x AS (
    SELECT
        CASE
            WHEN d.fin IS NULL THEN '5 sin fin'
            WHEN d.fin - d.ini <= INTERVAL '22 minutes' THEN '1 hasta 22 min'
            WHEN d.fin - d.ini <= INTERVAL '24 hours' THEN '2 22 min a 24 h'
            WHEN d.fin - d.ini <= INTERVAL '11 days' THEN '3 1 a 11 días'
            ELSE '4 más de 11 días'
        END                                                         AS tramo,
        v.con_mov,
        v.con_piso,
        COALESCE(d.fin = v.fin_mov, FALSE)                          AS fin_igual_ultimo_mov,
        COALESCE(NOT v.con_mov OR d.fin >= v.fin_mov, FALSE)        AS fija_salida,
        COALESCE(d.fin = v.inicio_piso, FALSE)                      AS fin_igual_inicio_piso,
        COALESCE(d.fin = v.fin_piso, FALSE)                         AS fin_igual_fin_piso,
        COALESCE(MOD(CAST(EXTRACT(MICROSECONDS FROM d.fin) AS bigint), 1000000) <> 0, FALSE) AS fin_fraccion
    FROM d
    JOIN visita v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE d.c = 9203
)
SELECT
    tramo,
    COUNT(*)                                                                AS n,
    COUNT(*) FILTER (WHERE con_mov)                                         AS n_con_movimientos,
    100.0 * COUNT(*) FILTER (WHERE con_mov) / COUNT(*)                      AS pct_con_movimientos,
    COUNT(*) FILTER (WHERE con_piso)                                        AS n_con_piso,
    100.0 * COUNT(*) FILTER (WHERE con_piso) / COUNT(*)                     AS pct_con_piso,
    COUNT(*) FILTER (WHERE fin_igual_ultimo_mov)                            AS n_fin_igual_ultimo_mov,
    100.0 * COUNT(*) FILTER (WHERE fin_igual_ultimo_mov) / COUNT(*)         AS pct_fin_igual_ultimo_mov,
    COUNT(*) FILTER (WHERE fija_salida)                                     AS n_fija_salida,
    100.0 * COUNT(*) FILTER (WHERE fija_salida) / COUNT(*)                  AS pct_fija_salida,
    COUNT(*) FILTER (WHERE fin_igual_inicio_piso)                           AS n_fin_igual_inicio_piso,
    100.0 * COUNT(*) FILTER (WHERE fin_igual_inicio_piso) / COUNT(*)        AS pct_fin_igual_inicio_piso,
    COUNT(*) FILTER (WHERE fin_igual_fin_piso)                              AS n_fin_igual_fin_piso,
    100.0 * COUNT(*) FILTER (WHERE fin_igual_fin_piso) / COUNT(*)           AS pct_fin_igual_fin_piso,
    COUNT(*) FILTER (WHERE fin_fraccion)                                    AS n_fin_fraccion,
    100.0 * COUNT(*) FILTER (WHERE fin_fraccion) / COUNT(*)                 AS pct_fin_fraccion
FROM x
GROUP BY tramo
ORDER BY tramo;
