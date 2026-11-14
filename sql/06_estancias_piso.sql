-- Estancias en piso (etapas 9201) de cualquier tipo de visita, para el censo horario del notebook 06.
-- Devuelve una fila por etapa (con person_id): su resultado solo se guarda en data/raw/ con consultar() y
-- nunca se muestra.
-- Se excluyen las etapas que empiezan más de 1 hora antes del inicio de su visita (eventos previos).
-- Ventana: etapas con fin posterior al 2023-01-01 (o sin fin) y comienzo anterior al 2026-04-01.
-- Columnas:
--   person_id, visit_concept_id (tipo de la visita), inicio, fin (puede ser NULL),
--   edad: año de inicio de la etapa - year_of_birth (sin depurar; los valores inválidos se tratan en pandas),
--   fin_fraccion_segundo: el fin tiene microsegundos distintos de 0.
SELECT
    v.person_id,
    v.visit_concept_id,
    d.visit_detail_start_datetime                                                   AS inicio,
    d.visit_detail_end_datetime                                                     AS fin,
    CAST(EXTRACT(YEAR FROM d.visit_detail_start_datetime) AS integer) - p.year_of_birth AS edad,
    p.year_of_birth,
    COALESCE(MOD(CAST(EXTRACT(MICROSECONDS FROM d.visit_detail_end_datetime) AS bigint), 1000000) <> 0, FALSE)
                                                                                    AS fin_fraccion_segundo
FROM {schema}.visit_detail d
JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
LEFT JOIN {schema}.person p ON p.person_id = v.person_id
WHERE d.visit_detail_concept_id = 9201
  AND NOT COALESCE(d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour', FALSE)
  AND (d.visit_detail_end_datetime > DATE '2023-01-01' OR d.visit_detail_end_datetime IS NULL)
  AND d.visit_detail_start_datetime < DATE '2026-04-01';
