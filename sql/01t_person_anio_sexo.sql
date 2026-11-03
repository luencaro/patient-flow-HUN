-- Personas por año de nacimiento y sexo (traducido con concept). Incluye los años imposibles (D8).
SELECT
    p.year_of_birth                                AS anio_nacimiento,
    COALESCE(c.concept_name, '(sin concepto)')     AS sexo,
    COUNT(*)                                       AS n_personas
FROM {schema}.person p
LEFT JOIN {schema}.concept c ON c.concept_id = p.gender_concept_id
GROUP BY p.year_of_birth, COALESCE(c.concept_name, '(sin concepto)')
ORDER BY anio_nacimiento, sexo;
