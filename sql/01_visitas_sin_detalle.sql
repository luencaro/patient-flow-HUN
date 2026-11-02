-- Visitas de urgencias (9203) sin ningún visit_detail, y con solo etapas desplazadas, por mes.
WITH det AS (
    SELECT
        d.visit_occurrence_id,
        BOOL_OR(d.visit_detail_start_datetime >= v.visit_start_datetime - INTERVAL '1 hour') AS tiene_valida
    FROM {schema}.visit_detail d
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
    WHERE v.visit_concept_id = 9203
    GROUP BY d.visit_occurrence_id
)
SELECT
    CAST(date_trunc('month', v.visit_start_datetime) AS date)               AS mes,
    COUNT(*)                                                                AS n,
    COUNT(*) FILTER (WHERE det.visit_occurrence_id IS NULL)                 AS n_sin_detalle,
    100.0 * COUNT(*) FILTER (WHERE det.visit_occurrence_id IS NULL) / COUNT(*) AS pct_sin_detalle,
    COUNT(*) FILTER (WHERE det.tiene_valida = FALSE)                        AS n_solo_desplazados,
    100.0 * COUNT(*) FILTER (WHERE det.tiene_valida = FALSE) / COUNT(*)     AS pct_solo_desplazados
FROM {schema}.visit_occurrence v
LEFT JOIN det ON det.visit_occurrence_id = v.visit_occurrence_id
WHERE v.visit_concept_id = 9203
GROUP BY CAST(date_trunc('month', v.visit_start_datetime) AS date)
ORDER BY mes;
