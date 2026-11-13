-- head(): primeras 5 filas reales de visit_occurrence, con todas las columnas, ordenadas por visit_occurrence_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.visit_occurrence
ORDER BY visit_occurrence_id
LIMIT 5;
