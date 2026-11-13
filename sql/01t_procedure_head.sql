-- head(): primeras 5 filas reales de procedure_occurrence, con todas las columnas, ordenadas por procedure_occurrence_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.procedure_occurrence
ORDER BY procedure_occurrence_id
LIMIT 5;
