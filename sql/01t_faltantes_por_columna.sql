-- Faltantes por tabla y columna (tablas completas), para info() y las barras de faltantes.
-- Una fila por tabla y columna: n (filas), n_nulos, n_concepto_0 (solo columnas *_concept_id),
-- valores_distintos (todas las columnas) y es_constante
-- (MIN = MAX: un solo valor distinto; NULL si la columna es toda nula).
-- Archivo generado; cada tabla se recorre una sola vez. Lo usan info() y las barras de faltantes del notebook 01.
-- AVISO: cuenta valores distintos de todas las columnas (incluidos IDs y fechas) en tablas de decenas de
-- millones de filas (condition_occurrence, procedure_occurrence, measurement): puede tardar varios minutos.
WITH
pe AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(person_id) AS nulos__person_id
        , MIN(person_id) = MAX(person_id) AS constante__person_id
        , COUNT(DISTINCT person_id) AS distintos__person_id
        , COUNT(*) - COUNT(gender_concept_id) AS nulos__gender_concept_id
        , MIN(gender_concept_id) = MAX(gender_concept_id) AS constante__gender_concept_id
        , COUNT(*) FILTER (WHERE gender_concept_id = 0) AS cero__gender_concept_id
        , COUNT(DISTINCT gender_concept_id) AS distintos__gender_concept_id
        , COUNT(*) - COUNT(year_of_birth) AS nulos__year_of_birth
        , MIN(year_of_birth) = MAX(year_of_birth) AS constante__year_of_birth
        , COUNT(DISTINCT year_of_birth) AS distintos__year_of_birth
        , COUNT(*) - COUNT(race_concept_id) AS nulos__race_concept_id
        , MIN(race_concept_id) = MAX(race_concept_id) AS constante__race_concept_id
        , COUNT(*) FILTER (WHERE race_concept_id = 0) AS cero__race_concept_id
        , COUNT(DISTINCT race_concept_id) AS distintos__race_concept_id
        , COUNT(*) - COUNT(ethnicity_concept_id) AS nulos__ethnicity_concept_id
        , MIN(ethnicity_concept_id) = MAX(ethnicity_concept_id) AS constante__ethnicity_concept_id
        , COUNT(*) FILTER (WHERE ethnicity_concept_id = 0) AS cero__ethnicity_concept_id
        , COUNT(DISTINCT ethnicity_concept_id) AS distintos__ethnicity_concept_id
    FROM {schema}.person
),
vo AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(visit_occurrence_id) AS nulos__visit_occurrence_id
        , MIN(visit_occurrence_id) = MAX(visit_occurrence_id) AS constante__visit_occurrence_id
        , COUNT(DISTINCT visit_occurrence_id) AS distintos__visit_occurrence_id
        , COUNT(*) - COUNT(person_id) AS nulos__person_id
        , MIN(person_id) = MAX(person_id) AS constante__person_id
        , COUNT(DISTINCT person_id) AS distintos__person_id
        , COUNT(*) - COUNT(visit_concept_id) AS nulos__visit_concept_id
        , MIN(visit_concept_id) = MAX(visit_concept_id) AS constante__visit_concept_id
        , COUNT(*) FILTER (WHERE visit_concept_id = 0) AS cero__visit_concept_id
        , COUNT(DISTINCT visit_concept_id) AS distintos__visit_concept_id
        , COUNT(*) - COUNT(visit_start_datetime) AS nulos__visit_start_datetime
        , MIN(visit_start_datetime) = MAX(visit_start_datetime) AS constante__visit_start_datetime
        , COUNT(DISTINCT visit_start_datetime) AS distintos__visit_start_datetime
        , COUNT(*) - COUNT(visit_end_datetime) AS nulos__visit_end_datetime
        , MIN(visit_end_datetime) = MAX(visit_end_datetime) AS constante__visit_end_datetime
        , COUNT(DISTINCT visit_end_datetime) AS distintos__visit_end_datetime
        , COUNT(*) - COUNT(provider_id) AS nulos__provider_id
        , MIN(provider_id) = MAX(provider_id) AS constante__provider_id
        , COUNT(DISTINCT provider_id) AS distintos__provider_id
    FROM {schema}.visit_occurrence
),
vd AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(visit_detail_id) AS nulos__visit_detail_id
        , MIN(visit_detail_id) = MAX(visit_detail_id) AS constante__visit_detail_id
        , COUNT(DISTINCT visit_detail_id) AS distintos__visit_detail_id
        , COUNT(*) - COUNT(visit_occurrence_id) AS nulos__visit_occurrence_id
        , MIN(visit_occurrence_id) = MAX(visit_occurrence_id) AS constante__visit_occurrence_id
        , COUNT(DISTINCT visit_occurrence_id) AS distintos__visit_occurrence_id
        , COUNT(*) - COUNT(visit_detail_concept_id) AS nulos__visit_detail_concept_id
        , MIN(visit_detail_concept_id) = MAX(visit_detail_concept_id) AS constante__visit_detail_concept_id
        , COUNT(*) FILTER (WHERE visit_detail_concept_id = 0) AS cero__visit_detail_concept_id
        , COUNT(DISTINCT visit_detail_concept_id) AS distintos__visit_detail_concept_id
        , COUNT(*) - COUNT(visit_detail_start_datetime) AS nulos__visit_detail_start_datetime
        , MIN(visit_detail_start_datetime) = MAX(visit_detail_start_datetime) AS constante__visit_detail_start_datetime
        , COUNT(DISTINCT visit_detail_start_datetime) AS distintos__visit_detail_start_datetime
        , COUNT(*) - COUNT(visit_detail_end_datetime) AS nulos__visit_detail_end_datetime
        , MIN(visit_detail_end_datetime) = MAX(visit_detail_end_datetime) AS constante__visit_detail_end_datetime
        , COUNT(DISTINCT visit_detail_end_datetime) AS distintos__visit_detail_end_datetime
        , COUNT(*) - COUNT(provider_id) AS nulos__provider_id
        , MIN(provider_id) = MAX(provider_id) AS constante__provider_id
        , COUNT(DISTINCT provider_id) AS distintos__provider_id
    FROM {schema}.visit_detail
),
co AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(condition_occurrence_id) AS nulos__condition_occurrence_id
        , MIN(condition_occurrence_id) = MAX(condition_occurrence_id) AS constante__condition_occurrence_id
        , COUNT(DISTINCT condition_occurrence_id) AS distintos__condition_occurrence_id
        , COUNT(*) - COUNT(person_id) AS nulos__person_id
        , MIN(person_id) = MAX(person_id) AS constante__person_id
        , COUNT(DISTINCT person_id) AS distintos__person_id
        , COUNT(*) - COUNT(visit_occurrence_id) AS nulos__visit_occurrence_id
        , MIN(visit_occurrence_id) = MAX(visit_occurrence_id) AS constante__visit_occurrence_id
        , COUNT(DISTINCT visit_occurrence_id) AS distintos__visit_occurrence_id
        , COUNT(*) - COUNT(condition_concept_id) AS nulos__condition_concept_id
        , MIN(condition_concept_id) = MAX(condition_concept_id) AS constante__condition_concept_id
        , COUNT(*) FILTER (WHERE condition_concept_id = 0) AS cero__condition_concept_id
        , COUNT(DISTINCT condition_concept_id) AS distintos__condition_concept_id
        , COUNT(*) - COUNT(condition_start_datetime) AS nulos__condition_start_datetime
        , MIN(condition_start_datetime) = MAX(condition_start_datetime) AS constante__condition_start_datetime
        , COUNT(DISTINCT condition_start_datetime) AS distintos__condition_start_datetime
        , COUNT(*) - COUNT(condition_type_concept_id) AS nulos__condition_type_concept_id
        , MIN(condition_type_concept_id) = MAX(condition_type_concept_id) AS constante__condition_type_concept_id
        , COUNT(*) FILTER (WHERE condition_type_concept_id = 0) AS cero__condition_type_concept_id
        , COUNT(DISTINCT condition_type_concept_id) AS distintos__condition_type_concept_id
    FROM {schema}.condition_occurrence
),
po AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(procedure_occurrence_id) AS nulos__procedure_occurrence_id
        , MIN(procedure_occurrence_id) = MAX(procedure_occurrence_id) AS constante__procedure_occurrence_id
        , COUNT(DISTINCT procedure_occurrence_id) AS distintos__procedure_occurrence_id
        , COUNT(*) - COUNT(person_id) AS nulos__person_id
        , MIN(person_id) = MAX(person_id) AS constante__person_id
        , COUNT(DISTINCT person_id) AS distintos__person_id
        , COUNT(*) - COUNT(visit_occurrence_id) AS nulos__visit_occurrence_id
        , MIN(visit_occurrence_id) = MAX(visit_occurrence_id) AS constante__visit_occurrence_id
        , COUNT(DISTINCT visit_occurrence_id) AS distintos__visit_occurrence_id
        , COUNT(*) - COUNT(procedure_concept_id) AS nulos__procedure_concept_id
        , MIN(procedure_concept_id) = MAX(procedure_concept_id) AS constante__procedure_concept_id
        , COUNT(*) FILTER (WHERE procedure_concept_id = 0) AS cero__procedure_concept_id
        , COUNT(DISTINCT procedure_concept_id) AS distintos__procedure_concept_id
        , COUNT(*) - COUNT(procedure_date) AS nulos__procedure_date
        , MIN(procedure_date) = MAX(procedure_date) AS constante__procedure_date
        , COUNT(DISTINCT procedure_date) AS distintos__procedure_date
    FROM {schema}.procedure_occurrence
),
me AS (
    SELECT
        COUNT(*) AS n
        , COUNT(*) - COUNT(measurement_id) AS nulos__measurement_id
        , MIN(measurement_id) = MAX(measurement_id) AS constante__measurement_id
        , COUNT(DISTINCT measurement_id) AS distintos__measurement_id
        , COUNT(*) - COUNT(person_id) AS nulos__person_id
        , MIN(person_id) = MAX(person_id) AS constante__person_id
        , COUNT(DISTINCT person_id) AS distintos__person_id
        , COUNT(*) - COUNT(visit_occurrence_id) AS nulos__visit_occurrence_id
        , MIN(visit_occurrence_id) = MAX(visit_occurrence_id) AS constante__visit_occurrence_id
        , COUNT(DISTINCT visit_occurrence_id) AS distintos__visit_occurrence_id
        , COUNT(*) - COUNT(measurement_concept_id) AS nulos__measurement_concept_id
        , MIN(measurement_concept_id) = MAX(measurement_concept_id) AS constante__measurement_concept_id
        , COUNT(*) FILTER (WHERE measurement_concept_id = 0) AS cero__measurement_concept_id
        , COUNT(DISTINCT measurement_concept_id) AS distintos__measurement_concept_id
        , COUNT(*) - COUNT(measurement_datetime) AS nulos__measurement_datetime
        , MIN(measurement_datetime) = MAX(measurement_datetime) AS constante__measurement_datetime
        , COUNT(DISTINCT measurement_datetime) AS distintos__measurement_datetime
        , COUNT(*) - COUNT(value_as_number) AS nulos__value_as_number
        , MIN(value_as_number) = MAX(value_as_number) AS constante__value_as_number
        , COUNT(DISTINCT value_as_number) AS distintos__value_as_number
        , COUNT(*) - COUNT(measurement_source_value_extended) AS nulos__measurement_source_value_extended
        , MIN(measurement_source_value_extended) = MAX(measurement_source_value_extended) AS constante__measurement_source_value_extended
        , COUNT(DISTINCT measurement_source_value_extended) AS distintos__measurement_source_value_extended
    FROM {schema}.measurement
)
SELECT 'person' AS tabla, x.posicion, x.columna, pe.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM pe
CROSS JOIN LATERAL (VALUES
    (1, 'person_id', pe.nulos__person_id, CAST(NULL AS bigint), pe.distintos__person_id, pe.constante__person_id),
    (2, 'gender_concept_id', pe.nulos__gender_concept_id, pe.cero__gender_concept_id, pe.distintos__gender_concept_id, pe.constante__gender_concept_id),
    (3, 'year_of_birth', pe.nulos__year_of_birth, CAST(NULL AS bigint), pe.distintos__year_of_birth, pe.constante__year_of_birth),
    (4, 'race_concept_id', pe.nulos__race_concept_id, pe.cero__race_concept_id, pe.distintos__race_concept_id, pe.constante__race_concept_id),
    (5, 'ethnicity_concept_id', pe.nulos__ethnicity_concept_id, pe.cero__ethnicity_concept_id, pe.distintos__ethnicity_concept_id, pe.constante__ethnicity_concept_id)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
UNION ALL
SELECT 'visit_occurrence' AS tabla, x.posicion, x.columna, vo.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM vo
CROSS JOIN LATERAL (VALUES
    (1, 'visit_occurrence_id', vo.nulos__visit_occurrence_id, CAST(NULL AS bigint), vo.distintos__visit_occurrence_id, vo.constante__visit_occurrence_id),
    (2, 'person_id', vo.nulos__person_id, CAST(NULL AS bigint), vo.distintos__person_id, vo.constante__person_id),
    (3, 'visit_concept_id', vo.nulos__visit_concept_id, vo.cero__visit_concept_id, vo.distintos__visit_concept_id, vo.constante__visit_concept_id),
    (4, 'visit_start_datetime', vo.nulos__visit_start_datetime, CAST(NULL AS bigint), vo.distintos__visit_start_datetime, vo.constante__visit_start_datetime),
    (5, 'visit_end_datetime', vo.nulos__visit_end_datetime, CAST(NULL AS bigint), vo.distintos__visit_end_datetime, vo.constante__visit_end_datetime),
    (6, 'provider_id', vo.nulos__provider_id, CAST(NULL AS bigint), vo.distintos__provider_id, vo.constante__provider_id)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
UNION ALL
SELECT 'visit_detail' AS tabla, x.posicion, x.columna, vd.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM vd
CROSS JOIN LATERAL (VALUES
    (1, 'visit_detail_id', vd.nulos__visit_detail_id, CAST(NULL AS bigint), vd.distintos__visit_detail_id, vd.constante__visit_detail_id),
    (2, 'visit_occurrence_id', vd.nulos__visit_occurrence_id, CAST(NULL AS bigint), vd.distintos__visit_occurrence_id, vd.constante__visit_occurrence_id),
    (3, 'visit_detail_concept_id', vd.nulos__visit_detail_concept_id, vd.cero__visit_detail_concept_id, vd.distintos__visit_detail_concept_id, vd.constante__visit_detail_concept_id),
    (4, 'visit_detail_start_datetime', vd.nulos__visit_detail_start_datetime, CAST(NULL AS bigint), vd.distintos__visit_detail_start_datetime, vd.constante__visit_detail_start_datetime),
    (5, 'visit_detail_end_datetime', vd.nulos__visit_detail_end_datetime, CAST(NULL AS bigint), vd.distintos__visit_detail_end_datetime, vd.constante__visit_detail_end_datetime),
    (6, 'provider_id', vd.nulos__provider_id, CAST(NULL AS bigint), vd.distintos__provider_id, vd.constante__provider_id)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
UNION ALL
SELECT 'condition_occurrence' AS tabla, x.posicion, x.columna, co.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM co
CROSS JOIN LATERAL (VALUES
    (1, 'condition_occurrence_id', co.nulos__condition_occurrence_id, CAST(NULL AS bigint), co.distintos__condition_occurrence_id, co.constante__condition_occurrence_id),
    (2, 'person_id', co.nulos__person_id, CAST(NULL AS bigint), co.distintos__person_id, co.constante__person_id),
    (3, 'visit_occurrence_id', co.nulos__visit_occurrence_id, CAST(NULL AS bigint), co.distintos__visit_occurrence_id, co.constante__visit_occurrence_id),
    (4, 'condition_concept_id', co.nulos__condition_concept_id, co.cero__condition_concept_id, co.distintos__condition_concept_id, co.constante__condition_concept_id),
    (5, 'condition_start_datetime', co.nulos__condition_start_datetime, CAST(NULL AS bigint), co.distintos__condition_start_datetime, co.constante__condition_start_datetime),
    (6, 'condition_type_concept_id', co.nulos__condition_type_concept_id, co.cero__condition_type_concept_id, co.distintos__condition_type_concept_id, co.constante__condition_type_concept_id)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
UNION ALL
SELECT 'procedure_occurrence' AS tabla, x.posicion, x.columna, po.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM po
CROSS JOIN LATERAL (VALUES
    (1, 'procedure_occurrence_id', po.nulos__procedure_occurrence_id, CAST(NULL AS bigint), po.distintos__procedure_occurrence_id, po.constante__procedure_occurrence_id),
    (2, 'person_id', po.nulos__person_id, CAST(NULL AS bigint), po.distintos__person_id, po.constante__person_id),
    (3, 'visit_occurrence_id', po.nulos__visit_occurrence_id, CAST(NULL AS bigint), po.distintos__visit_occurrence_id, po.constante__visit_occurrence_id),
    (4, 'procedure_concept_id', po.nulos__procedure_concept_id, po.cero__procedure_concept_id, po.distintos__procedure_concept_id, po.constante__procedure_concept_id),
    (5, 'procedure_date', po.nulos__procedure_date, CAST(NULL AS bigint), po.distintos__procedure_date, po.constante__procedure_date)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
UNION ALL
SELECT 'measurement' AS tabla, x.posicion, x.columna, me.n, x.n_nulos, x.n_concepto_0, x.valores_distintos, x.es_constante
FROM me
CROSS JOIN LATERAL (VALUES
    (1, 'measurement_id', me.nulos__measurement_id, CAST(NULL AS bigint), me.distintos__measurement_id, me.constante__measurement_id),
    (2, 'person_id', me.nulos__person_id, CAST(NULL AS bigint), me.distintos__person_id, me.constante__person_id),
    (3, 'visit_occurrence_id', me.nulos__visit_occurrence_id, CAST(NULL AS bigint), me.distintos__visit_occurrence_id, me.constante__visit_occurrence_id),
    (4, 'measurement_concept_id', me.nulos__measurement_concept_id, me.cero__measurement_concept_id, me.distintos__measurement_concept_id, me.constante__measurement_concept_id),
    (5, 'measurement_datetime', me.nulos__measurement_datetime, CAST(NULL AS bigint), me.distintos__measurement_datetime, me.constante__measurement_datetime),
    (6, 'value_as_number', me.nulos__value_as_number, CAST(NULL AS bigint), me.distintos__value_as_number, me.constante__value_as_number),
    (7, 'measurement_source_value_extended', me.nulos__measurement_source_value_extended, CAST(NULL AS bigint), me.distintos__measurement_source_value_extended, me.constante__measurement_source_value_extended)
) AS x(posicion, columna, n_nulos, n_concepto_0, valores_distintos, es_constante)
ORDER BY 1, 2;
