-- Histograma de la duración de las etapas en escala logarítmica (bins de 1/4 de década, en horas).
-- Solo duraciones positivas; las nulas, cero y negativas se cuentan en 01_duracion_etapas.sql.
WITH e AS (
    SELECT
        d.visit_detail_concept_id AS concepto_etapa,
        CAST(EXTRACT(EPOCH FROM (d.visit_detail_end_datetime - d.visit_detail_start_datetime)) / 3600.0
             AS double precision) AS horas
    FROM {schema}.visit_detail d
)
SELECT
    e.concepto_etapa,
    COALESCE(c.concept_name, '(sin concepto)')           AS etapa,
    FLOOR(LOG(e.horas) * 4) / 4.0                        AS bin_log10_h,
    COUNT(*)                                             AS n_detalles
FROM e
LEFT JOIN {schema}.concept c ON c.concept_id = e.concepto_etapa
WHERE e.horas > 0
GROUP BY e.concepto_etapa, c.concept_name, FLOOR(LOG(e.horas) * 4) / 4.0
ORDER BY e.concepto_etapa, bin_log10_h;
