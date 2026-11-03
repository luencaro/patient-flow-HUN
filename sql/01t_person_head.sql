-- head(): primeras 5 filas reales de person, con todas las columnas, ordenadas por person_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.person
ORDER BY person_id
LIMIT 5;
