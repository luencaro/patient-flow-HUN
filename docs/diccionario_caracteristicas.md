# Diccionario de características por episodio

Columnas de `data/interim/episodios_caracteristicas.parquet`, generado por `notebooks/07_caracteristicas.ipynb` a partir de `data/interim/episodios_final.parquet` (notebook 05) y de la extracción `sql/06_estancias_piso.sql`. Una fila por episodio de la población de análisis (`en_poblacion == True`).

**Principio:** toda característica con rol «predictor» se calcula con información anterior a la llegada del episodio. Los desenlaces llevan el prefijo `y_` y nunca deben usarse como predictores. Las variables de historia y de cola usan todos los episodios del dataset, no solo los de la población.

**Rol:** «predictor» (se conoce a la llegada; entra a los modelos), «estrato» (para estratificar, no es predictor), «descriptiva» (se conoce después de la llegada; solo para describir), «control» (marca de calidad de los datos; no es predictor) o «desenlace» (prefijo `y_`). El identificador, la fecha de llegada y el filtro de tiempos no tienen rol (—). La misma información está en `ROLES_CARACTERISTICAS` de `src/config.py`.

**Ocupación a la llegada:** urgencias y piso se miden en el instante exacto de la llegada (episodios o estancias con inicio < llegada < fin, con `censo_en_instantes`); el percentil se calcula frente al censo horario del trimestre.

`episodio_id` es un identificador interno: nunca se muestra ni se exporta fuera de `data/`.

| Variable | Definición | Tipo | Fuente | Ventana temporal | Rol |
|---|---|---|---|---|---|
| `episodio_id` | Identificador interno del episodio | entero | `episodios_final` | — | — |
| `llegada` | Fecha y hora de llegada a urgencias | fecha y hora | `episodios_final` | — | — |
| `valido_para_tiempos` | El episodio entra a los cálculos de LOS (filtro de `REGLAS_EPISODIO`) | booleano | `episodios_final` | — | — |
| `grupo` | Grupo de análisis: contacto breve, atención en urgencias u hospitalizado | texto | `episodios_final` | Todo el episodio | estrato |
| `sexo` | `femenino`, `masculino` u `otro_o_sin_dato` | texto | `episodios_final` | — | predictor |
| `hosp_previa_30d` | Algún 9201 previo cuyo fin está en los 30 días antes de la llegada | booleano | `episodios_final` | 30 días antes de la llegada | predictor |
| `nota_consulta_urg` | El episodio tiene un procedimiento «Emergency department Consult note» | booleano | `episodios_final` | Todo el episodio | descriptiva |
| `n_visitas` | Visitas 9203 fusionadas en el episodio | entero | `episodios_final` | Todo el episodio | descriptiva |
| `hora` | Hora de la llegada (0–23) | entero | `variables_calendario` | Instante de llegada | predictor |
| `dia_semana` | Día de la semana de la llegada (0 = lunes) | entero | `variables_calendario` | Instante de llegada | predictor |
| `mes` | Mes de la llegada (1–12) | entero | `variables_calendario` | Instante de llegada | predictor |
| `anio` | Año de la llegada | entero | `variables_calendario` | Instante de llegada | predictor |
| `fin_de_semana` | La llegada es sábado o domingo | booleano | `variables_calendario` | Instante de llegada | predictor |
| `festivo` | La fecha de llegada es festivo en Colombia (paquete `holidays`) | booleano | `variables_calendario` | Instante de llegada | predictor |
| `franja` | Franja horaria de la llegada: 00–06, 06–12, 12–18 o 18–24 | categórica | `variables_calendario` (`tramo_horario`) | Instante de llegada | predictor |
| `edad_llegada` | Año de llegada − `year_of_birth` (la columna `edad` del dataset de episodios) | decimal | `variables_edad` | Instante de llegada | predictor |
| `pediatria` | `edad_llegada` < `EDAD_PEDIATRIA` (18); vacío si falta la edad | booleano nulable | `variables_edad` | Instante de llegada | predictor |
| `grupo_edad` | Grupo de `GRUPOS_EDAD`: <1, 1-4, 5-17, 18-44, 45-64, 65-79, 80+; vacío si falta la edad | categórica | `variables_edad` | Instante de llegada | predictor |
| `n_episodios_previos_30d` | Episodios del mismo paciente con llegada en `[llegada − 30 d, llegada)` | entero | `episodios_previos` (todos los episodios) | 30 días antes de la llegada | predictor |
| `historia_completa_30d` | La ventana de 30 días cae completa dentro de los datos (llegada ≥ 2023-01-31) | booleano | `historia_completa` | 30 días antes de la llegada | control |
| `n_episodios_previos_365d` | Episodios del mismo paciente con llegada en `[llegada − 365 d, llegada)` | entero | `episodios_previos` (todos los episodios) | 365 días antes de la llegada | predictor |
| `historia_completa_365d` | La ventana de 365 días cae completa dentro de los datos (llegada ≥ 2024-01-01) | booleano | `historia_completa` | 365 días antes de la llegada | control |
| `urg_atencion_presentes_llegada` | Episodios de atención en urgencias y hospitalizados presentes en urgencias en el instante de la llegada (inicio < llegada < fin), sin contar el propio; intervalo de urgencias como en el notebook 06, episodios válidos para tiempos | entero | `censo_en_instantes` (todos los episodios) | Instante de llegada | predictor |
| `urg_atencion_presentes_llegada_pct_trimestre` | Percentil de `urg_atencion_presentes_llegada` frente al censo horario con atención de su trimestre | decimal | `percentil_en_censo` | Trimestre de la llegada | predictor |
| `censo_calentamiento` | La llegada cae en el periodo de calentamiento del censo (antes de `FECHA_INICIO_CENSO`, 2023-02-01) | booleano | `FECHA_INICIO_CENSO` | Instante de llegada | control |
| `piso_censo_llegada` | Pacientes en el piso en el instante exacto de la llegada (inicio < llegada < fin; estancias 9201 unidas por paciente), igual que urgencias | entero | `censo_a_la_llegada` (`06_estancias_piso`) | Instante de llegada | predictor |
| `piso_censo_llegada_pct_trimestre` | Percentil de `piso_censo_llegada` frente al censo horario del piso de su trimestre, sin el periodo de calentamiento | decimal | `censo_a_la_llegada` | Trimestre de la llegada | predictor |
| `piso_grupo_censo_llegada` | Como `piso_censo_llegada`, en el piso del grupo de edad del paciente (adultos o pediatría); vacío si falta la edad | entero | `censo_de_su_grupo` | Instante de llegada | predictor |
| `piso_grupo_censo_llegada_pct_trimestre` | Percentil de `piso_grupo_censo_llegada` frente al censo de su grupo de edad en su trimestre | decimal | `censo_de_su_grupo` | Trimestre de la llegada | predictor |
| `los_reciente_promedio_h` | Promedio del LOS (horas) de los episodios de atención en urgencias y hospitalizados que salieron de urgencias en `[llegada − 8 h, llegada)`; vacío si no hubo salidas | decimal | `los_reciente` (todos los episodios) | `VENTANA_LOS_RECIENTE_H` = 8 h antes de la llegada | predictor |
| `los_reciente_mediana_h` | Mediana del LOS (horas) de esas salidas; vacío si no hubo salidas | decimal | `los_reciente` | 8 h antes de la llegada | predictor |
| `n_salidas_recientes` | Número de esas salidas | entero | `los_reciente` | 8 h antes de la llegada | predictor |
| `y_los_h` | Tiempo de permanencia en urgencias, en horas (`los_h`) | decimal | `episodios_final` | Después de la llegada | desenlace |
| `y_los_mas_12h` | LOS mayor a 12 h (`los_mas_12h`; solo atención en urgencias y hospitalizados) | booleano nulable | `episodios_final` | Después de la llegada | desenlace |
| `y_reconsulta_72h` | El siguiente episodio llega en 72 h o menos, con censura al final de los datos (`reconsulta_72h`) | booleano nulable | `episodios_final` | 72 h después del fin del episodio | desenlace |
| `y_reconsulta_72h_sin_censura` | Igual, sin censura (`reconsulta_72h_sin_censura`) | booleano | `episodios_final` | 72 h después del fin del episodio | desenlace |
| `y_reconsulta_7d` | El siguiente episodio llega en 7 días o menos, con censura (`reconsulta_7d`) | booleano nulable | `episodios_final` | 7 días después del fin del episodio | desenlace |
| `y_reconsulta_7d_sin_censura` | Igual, sin censura (`reconsulta_7d_sin_censura`) | booleano | `episodios_final` | 7 días después del fin del episodio | desenlace |
