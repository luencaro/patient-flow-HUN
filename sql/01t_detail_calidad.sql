-- Calidad de visit_detail en una sola fila (tabla completa). Convención: ver 01t_person_calidad.sql.
SELECT
    COUNT(*)                                                                    AS n_filas,
    COUNT(*) - COUNT(d.visit_detail_id)                                         AS nulos__visit_detail_id,
    COUNT(*) - COUNT(d.visit_occurrence_id)                                     AS nulos__visit_occurrence_id,
    COUNT(*) - COUNT(d.visit_detail_concept_id)                                 AS nulos__visit_detail_concept_id,
    COUNT(*) - COUNT(d.visit_detail_start_datetime)                             AS nulos__visit_detail_start_datetime,
    COUNT(*) - COUNT(d.visit_detail_end_datetime)                               AS nulos__visit_detail_end_datetime,
    COUNT(*) - COUNT(d.provider_id)                                             AS nulos__provider_id,
    COUNT(DISTINCT d.visit_detail_id)                                           AS distintos__visit_detail_id,
    COUNT(DISTINCT d.visit_occurrence_id)                                       AS distintos__visit_occurrence_id,
    COUNT(DISTINCT d.visit_detail_concept_id)                                   AS distintos__visit_detail_concept_id,
    COUNT(DISTINCT d.provider_id)                                               AS distintos__provider_id,
    COUNT(*) - COUNT(DISTINCT d.visit_detail_id)                                AS chequeo__id_etapa_repetido,
    COUNT(*) FILTER (WHERE d.visit_detail_end_datetime < d.visit_detail_start_datetime)
                                                                                AS chequeo__fin_antes_de_inicio,
    COUNT(*) FILTER (WHERE d.visit_detail_end_datetime = d.visit_detail_start_datetime)
                                                                                AS chequeo__duracion_cero,
    COUNT(*) FILTER (WHERE v.visit_occurrence_id IS NULL)                       AS chequeo__visita_inexistente,
    COUNT(*) FILTER (WHERE d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour')
                                                                                AS chequeo__etapa_inicia_mas_de_1h_antes_de_su_visita,
    CAST(date_trunc('month', MIN(d.visit_detail_start_datetime)) AS date)       AS rango__primer_mes,
    CAST(date_trunc('month', MAX(d.visit_detail_start_datetime)) AS date)       AS rango__ultimo_mes
FROM {schema}.visit_detail d
LEFT JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id;
