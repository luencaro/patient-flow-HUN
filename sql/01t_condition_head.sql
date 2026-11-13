-- head(): primeras 5 filas reales de condition_occurrence, con todas las columnas, ordenadas por condition_occurrence_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.condition_occurrence
ORDER BY condition_occurrence_id
LIMIT 5;
