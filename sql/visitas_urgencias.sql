-- Extracción a nivel de visita para construir episodios (notebook 02).
-- ÚNICA consulta que devuelve filas por visita: su resultado solo se guarda en data/raw/ y nunca se muestra.
-- Parte de TODAS las visitas 9203 (LEFT JOIN con las etapas) para incluir las visitas sin etapas (D10).
-- Etapas: 9203 = ingreso por urgencias, 3045729 = movimiento o etapa, 9201 = hospitalización en piso.
-- previo (D2): la etapa empieza más de 1 hora antes de la llegada. Es un evento previo asociado a la
-- visita: no se usa para tiempos ni para definir hospitalización (D3).
-- fin y fin_urg quedan NULL si no hay etapas no previas; preparar_visitas los rellena con la llegada (D10).
WITH urg AS (
    SELECT v.visit_occurrence_id, v.person_id, v.visit_start_datetime AS llegada
    FROM {schema}.visit_occurrence v
    WHERE v.visit_concept_id = 9203
), d AS (
    SELECT d.visit_occurrence_id,
           d.visit_detail_concept_id     AS c,
           d.visit_detail_start_datetime AS ini,
           d.visit_detail_end_datetime   AS fin,
           u.llegada,
           COALESCE(d.visit_detail_start_datetime < u.llegada - INTERVAL '1 hour', FALSE) AS previo
    FROM {schema}.visit_detail d
    JOIN urg u ON u.visit_occurrence_id = d.visit_occurrence_id
), etapas AS (
    SELECT visit_occurrence_id,
           MAX(fin) FILTER (WHERE NOT previo)                  AS fin,
           MAX(fin) FILTER (WHERE NOT previo AND c <> 9201)    AS fin_urg,
           MIN(ini) FILTER (WHERE NOT previo AND c = 9201)     AS inicio_piso,
           MAX(fin) FILTER (WHERE NOT previo AND c = 9201)     AS fin_piso,
           BOOL_OR(NOT previo AND c = 9201)                    AS hosp,
           BOOL_OR(NOT previo AND c = 9203)                    AS tiene_9203,
           COUNT(*) FILTER (WHERE NOT previo)                  AS n_etapas,
           COUNT(*) FILTER (WHERE NOT previo AND c = 3045729)  AS n_segmentos,
           COUNT(*) FILTER (WHERE previo)                      AS n_eventos_previos,
           -- D11: algún 9201 previo cuyo fin está en los 30 días antes de la llegada.
           BOOL_OR(previo AND c = 9201 AND fin <= llegada AND fin >= llegada - INTERVAL '30 days')
                                                               AS hosp_previa_30d
    FROM d
    GROUP BY visit_occurrence_id
), conceptos_nota AS (
    -- D11: el concepto se busca por nombre en concept; no se escribe el concept_id a mano.
    SELECT concept_id
    FROM {schema}.concept
    WHERE concept_name = 'Emergency department Consult note'
), visitas_nota AS (
    -- Conjunto pre-agregado de visitas con ese procedimiento (evita una subconsulta correlacionada).
    SELECT DISTINCT po.visit_occurrence_id
    FROM {schema}.procedure_occurrence po
    JOIN conceptos_nota cn ON cn.concept_id = po.procedure_concept_id
    WHERE po.visit_occurrence_id IS NOT NULL
)
SELECT u.visit_occurrence_id,
       u.person_id,
       u.llegada,
       e.fin,
       e.fin_urg,
       e.inicio_piso,
       e.fin_piso,
       COALESCE(e.hosp, FALSE)               AS hosp,
       COALESCE(e.tiene_9203, FALSE)         AS tiene_9203,
       COALESCE(e.n_etapas, 0)               AS n_etapas,
       COALESCE(e.n_segmentos, 0)            AS n_segmentos,
       COALESCE(e.n_eventos_previos, 0)      AS n_eventos_previos,
       COALESCE(e.hosp_previa_30d, FALSE)    AS hosp_previa_30d,
       vn.visit_occurrence_id IS NOT NULL    AS nota_consulta_urg,
       p.year_of_birth,
       cs.concept_name                       AS sexo
FROM urg u
LEFT JOIN etapas e        ON e.visit_occurrence_id = u.visit_occurrence_id
LEFT JOIN visitas_nota vn ON vn.visit_occurrence_id = u.visit_occurrence_id
LEFT JOIN {schema}.person p   ON p.person_id = u.person_id
LEFT JOIN {schema}.concept cs ON cs.concept_id = p.gender_concept_id;
