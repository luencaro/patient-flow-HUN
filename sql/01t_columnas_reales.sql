-- Columnas reales de las tablas del modelo, desde information_schema (para compararlas con el diccionario).
SELECT
    table_name        AS tabla,
    column_name       AS columna,
    data_type         AS tipo_dato,
    ordinal_position  AS posicion
FROM information_schema.columns
WHERE table_schema = '{schema}'
  AND table_name IN ('person', 'visit_occurrence', 'visit_detail', 'condition_occurrence',
                     'procedure_occurrence', 'measurement', 'concept', 'cups')
ORDER BY tabla, posicion;
