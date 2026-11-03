-- head(): primeras 5 filas reales de visit_detail, con todas las columnas, ordenadas por visit_detail_id.
-- ÚNICA excepción autorizada a la regla de no mostrar filas individuales (ficha del dataset, notebook 01).
SELECT *
FROM {schema}.visit_detail
ORDER BY visit_detail_id
LIMIT 5;
