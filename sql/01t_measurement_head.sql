-- head(): primeras 5 filas reales de measurement, con todas las columnas, ordenadas por measurement_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.measurement
ORDER BY measurement_id
LIMIT 5;
