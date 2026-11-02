-- Extracción a nivel de visita para construir episodios (notebook 02).
-- ÚNICA consulta que devuelve filas por visita: su resultado solo se guarda en data/raw/ y nunca se muestra.
-- 9203 = urgencias, 9201 = piso, 3045729 = segmento de atención en urgencias.
-- desp (D2): la etapa empieza más de 1 hora antes de la llegada.
WITH d AS (
  SELECT d.visit_occurrence_id,
         d.visit_detail_concept_id AS c,
         d.visit_detail_start_datetime AS ini,
         d.visit_detail_end_datetime   AS fin,
         d.visit_detail_start_datetime < v.visit_start_datetime - INTERVAL '1 hour' AS desp
  FROM {schema}.visit_detail d
  JOIN {schema}.visit_occurrence v ON v.visit_occurrence_id = d.visit_occurrence_id
  WHERE v.visit_concept_id = 9203
)
SELECT v.visit_occurrence_id,
       v.person_id,
       v.visit_start_datetime AS llegada,
       MAX(d.fin) FILTER (WHERE NOT d.desp)                AS fin,
       MAX(d.fin) FILTER (WHERE NOT d.desp AND d.c <> 9201) AS fin_urg,
       MIN(d.ini) FILTER (WHERE NOT d.desp AND d.c = 9201)  AS inicio_piso,
       MAX(d.fin) FILTER (WHERE NOT d.desp AND d.c = 9201)  AS fin_piso,
       BOOL_OR(d.c = 9201)                                  AS hosp,
       BOOL_OR(d.c = 9203 AND NOT d.desp)                   AS tiene_9203,
       COUNT(*) FILTER (WHERE d.c = 3045729 AND NOT d.desp) AS n_segmentos,
       COUNT(*) FILTER (WHERE d.desp)                       AS n_desplazados,
       p.year_of_birth,
       c.concept_name AS sexo
FROM {schema}.visit_occurrence v
JOIN d ON d.visit_occurrence_id = v.visit_occurrence_id
JOIN {schema}.person p ON p.person_id = v.person_id
LEFT JOIN {schema}.concept c ON c.concept_id = p.gender_concept_id
WHERE v.visit_concept_id = 9203
GROUP BY v.visit_occurrence_id, v.person_id, v.visit_start_datetime, p.year_of_birth, c.concept_name
HAVING COUNT(*) FILTER (WHERE NOT d.desp) > 0;
