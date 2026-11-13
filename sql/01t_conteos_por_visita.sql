-- Frecuencias EXACTAS de conteos por visita, según el tipo de visita (para histogramas y cajas):
--   etapas                    : registros de visit_detail
--   registros_diagnostico     : registros de condition_occurrence con concepto distinto de 0
--   diagnosticos_distintos    : conceptos distintos de condition_occurrence (sin el concepto 0)
--   procedimientos            : registros de procedure_occurrence
-- Incluye las visitas con 0. Una fila por (tipo de visita, variable, k) con el número de visitas.
WITH et AS (
    SELECT visit_occurrence_id, COUNT(*) AS k
    FROM {schema}.visit_detail
    GROUP BY visit_occurrence_id
), dx AS (
    SELECT visit_occurrence_id,
           COUNT(*) FILTER (WHERE condition_concept_id <> 0)                    AS k_registros,
           COUNT(DISTINCT condition_concept_id) FILTER (WHERE condition_concept_id <> 0) AS k_distintos
    FROM {schema}.condition_occurrence
    WHERE visit_occurrence_id IS NOT NULL
    GROUP BY visit_occurrence_id
), pr AS (
    SELECT visit_occurrence_id, COUNT(*) AS k
    FROM {schema}.procedure_occurrence
    WHERE visit_occurrence_id IS NOT NULL
    GROUP BY visit_occurrence_id
), v AS (
    SELECT
        vo.visit_concept_id,
        COALESCE(et.k, 0)           AS etapas,
        COALESCE(dx.k_registros, 0) AS registros_diagnostico,
        COALESCE(dx.k_distintos, 0) AS diagnosticos_distintos,
        COALESCE(pr.k, 0)           AS procedimientos
    FROM {schema}.visit_occurrence vo
    LEFT JOIN et ON et.visit_occurrence_id = vo.visit_occurrence_id
    LEFT JOIN dx ON dx.visit_occurrence_id = vo.visit_occurrence_id
    LEFT JOIN pr ON pr.visit_occurrence_id = vo.visit_occurrence_id
), largo AS (
    SELECT v.visit_concept_id, x.variable, x.k
    FROM v
    CROSS JOIN LATERAL (VALUES
        ('etapas', v.etapas),
        ('registros_diagnostico', v.registros_diagnostico),
        ('diagnosticos_distintos', v.diagnosticos_distintos),
        ('procedimientos', v.procedimientos)
    ) AS x(variable, k)
)
SELECT
    l.visit_concept_id                              AS concepto_visita,
    COALESCE(c.concept_name, '(sin concepto)')      AS tipo_visita,
    l.variable,
    l.k,
    COUNT(*)                                        AS n_visitas
FROM largo l
LEFT JOIN {schema}.concept c ON c.concept_id = l.visit_concept_id
GROUP BY 1, 2, 3, 4
ORDER BY 1, 3, 4;
