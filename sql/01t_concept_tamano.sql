-- Tamaño de los catálogos: concept (vocabulario OMOP) y cups (procedimientos colombianos).
SELECT
    'concept'                       AS tabla,
    COUNT(*)                        AS n_filas,
    COUNT(DISTINCT concept_id)      AS distintos_codigo,
    COUNT(DISTINCT domain_id)       AS distintos_dominio,
    COUNT(DISTINCT vocabulary_id)   AS distintos_vocabulario,
    CAST(NULL AS bigint)            AS distintos_periodo
FROM {schema}.concept
UNION ALL
SELECT
    'cups',
    COUNT(*),
    COUNT(DISTINCT codigo),
    CAST(NULL AS bigint),
    CAST(NULL AS bigint),
    COUNT(DISTINCT periodo)
FROM {schema}.cups;
