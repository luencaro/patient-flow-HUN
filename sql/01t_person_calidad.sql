-- Calidad de person en una sola fila (tabla completa).
-- Convención de nombres que lee src/eda_tablas.perfil_calidad:
--   nulos__<columna>, distintos__<columna>, chequeo__<nombre>, rango__<nombre>.
SELECT
    COUNT(*)                                                        AS n_filas,
    COUNT(*) - COUNT(person_id)                                     AS nulos__person_id,
    COUNT(*) - COUNT(gender_concept_id)                             AS nulos__gender_concept_id,
    COUNT(*) - COUNT(year_of_birth)                                 AS nulos__year_of_birth,
    COUNT(*) - COUNT(race_concept_id)                               AS nulos__race_concept_id,
    COUNT(*) - COUNT(ethnicity_concept_id)                          AS nulos__ethnicity_concept_id,
    COUNT(DISTINCT person_id)                                       AS distintos__person_id,
    COUNT(DISTINCT gender_concept_id)                               AS distintos__gender_concept_id,
    COUNT(DISTINCT year_of_birth)                                   AS distintos__year_of_birth,
    COUNT(DISTINCT race_concept_id)                                 AS distintos__race_concept_id,
    COUNT(DISTINCT ethnicity_concept_id)                            AS distintos__ethnicity_concept_id,
    COUNT(*) - COUNT(DISTINCT person_id)                            AS chequeo__id_paciente_repetido,
    COUNT(*) FILTER (WHERE year_of_birth = 1)                       AS chequeo__anio_nacimiento_igual_a_1,
    COUNT(*) FILTER (WHERE year_of_birth < 1900)                    AS chequeo__anio_nacimiento_antes_de_1900,
    COUNT(*) FILTER (WHERE year_of_birth > EXTRACT(YEAR FROM CURRENT_DATE))
                                                                    AS chequeo__anio_nacimiento_futuro,
    COUNT(*) FILTER (WHERE gender_concept_id = 0)                   AS chequeo__sexo_concepto_0,
    COUNT(*) FILTER (WHERE race_concept_id = 0)                     AS chequeo__raza_concepto_0,
    COUNT(*) FILTER (WHERE ethnicity_concept_id = 0)                AS chequeo__etnia_concepto_0,
    MIN(year_of_birth) FILTER (WHERE year_of_birth >= 1900)         AS rango__anio_nacimiento_minimo_valido,
    MAX(year_of_birth)                                              AS rango__anio_nacimiento_maximo
FROM {schema}.person;
