-- Top 15 procedimientos (sin el concepto 0) en visitas de urgencias (9203) y ambulatorias (581479).
WITH base AS (
    SELECT v.visit_concept_id AS concepto_visita, po.procedure_concept_id AS concepto, COUNT(*) AS n_registros
    FROM {schema}.procedure_occurrence po
    JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = po.visit_occurrence_id
    WHERE v.visit_concept_id IN (9203, 581479)
      AND po.procedure_concept_id <> 0
    GROUP BY 1, 2
), r AS (
    SELECT
        base.*,
        ROW_NUMBER() OVER (PARTITION BY concepto_visita ORDER BY n_registros DESC, concepto)   AS rango,
        100.0 * n_registros / SUM(n_registros) OVER (PARTITION BY concepto_visita)            AS pct_registros
    FROM base
)
SELECT
    CASE r.concepto_visita WHEN 9203 THEN 'urgencias' ELSE 'ambulatoria' END   AS tipo_visita,
    r.rango,
    r.concepto,
    COALESCE(c.concept_name, '(sin concepto)')                                 AS procedimiento,
    c.domain_id                                                                AS dominio,
    r.n_registros,
    r.pct_registros
FROM r
LEFT JOIN {schema}.concept c ON c.concept_id = r.concepto
WHERE r.rango <= 15
ORDER BY tipo_visita, r.rango;
