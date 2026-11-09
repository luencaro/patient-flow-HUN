# Diccionario del dataset de episodios

Columnas de `data/interim/episodios_preliminar_60min.parquet`, generado por `notebooks/03_outliers_registros_y_dataset.ipynb`. El dataset final, `data/interim/episodios_final.parquet` (generado por `notebooks/05_outliers_episodios.ipynb`), tiene las mismas columnas más `valido_para_tiempos`. Una fila por episodio de urgencias, con fusión de visitas a 60 minutos. Antes de la fusión se quitan las visitas excluidas por `REGLAS_REGISTRO` (`src/config.py`): año de nacimiento < 1900, edad negativa y hospitalización que empieza antes de la llegada. La lista y los conteos quedan en el `.json` de metadatos.

**Origen:**
- **SQL**: `sql/visitas_urgencias.sql` (por visita), agregado al episodio en `fusionar_episodios`.
- **`preparar_visitas`**: calculada por visita en `src/episodios.py` y tomada de la primera visita del episodio.
- **`construir_episodios`**: calculada sobre el episodio en `src/episodios.py`.

**¿Se conoce a la llegada?** «Sí» si el valor está disponible en el momento en que el paciente llega a urgencias (sirve como variable predictora); «No» si depende de lo que ocurre después.

`episodio_id` y `person_id` son identificadores internos: nunca se muestran ni se exportan fuera de `data/`.

| Columna | Tipo | Descripción | Origen | ¿Se conoce a la llegada? |
|---|---|---|---|---|
| `episodio_id` | entero | Identificador interno del episodio | `construir_episodios` | Sí |
| `person_id` | entero | Identificador interno del paciente | SQL | Sí |
| `episodio_n` | entero | Número de orden del episodio dentro del paciente (1 = el primero) | `construir_episodios` | Sí |
| `llegada` | fecha y hora | Llegada a urgencias: `visit_start_datetime` de la primera visita | SQL | Sí |
| `fin_episodio` | fecha y hora | Máximo fin de las visitas del episodio (la llegada si la visita no tiene fin posterior) | `construir_episodios` | No |
| `fin` | fecha y hora | Máximo fin de las etapas no previas | SQL / `preparar_visitas` | No |
| `fin_urg` | fecha y hora | Máximo fin de las etapas no previas distintas de 9201 (fin de la atención en urgencias) | SQL / `preparar_visitas` | No |
| `inicio_piso` | fecha y hora | Inicio del primer 9201 no previo (subida a piso) | SQL | No |
| `fin_piso` | fecha y hora | Máximo fin de los 9201 no previos | SQL | No |
| `hosp` | booleano | Tiene al menos un 9201 que no es evento previo | SQL | No |
| `tiene_9203` | booleano | Tiene alguna etapa 9203 (ingreso por urgencias) no previa | SQL | No |
| `hosp_previa_30d` | booleano | Algún 9201 previo cuyo fin está en los 30 días antes de la llegada | SQL | Sí |
| `nota_consulta_urg` | booleano | Tiene un procedimiento «Emergency department Consult note» | SQL | No |
| `sin_etapas` | booleano | Ninguna visita del episodio tiene etapas no previas | `preparar_visitas` | No |
| `n_etapas` | entero | Etapas no previas (suma de las visitas) | SQL | No |
| `n_segmentos` | entero | Etapas 3045729 no previas (suma de las visitas) | SQL | No |
| `n_eventos_previos` | entero | Etapas que empiezan más de 1 h antes de la llegada (suma de las visitas) | SQL | Sí |
| `n_etapas_dur_0` | entero | Etapas no previas con duración 0 (suma de las visitas) | SQL | No |
| `max_dur_etapa_h` | decimal | Duración máxima de las etapas no previas, en horas | SQL | No |
| `max_dur_9203_h` | decimal | Duración máxima de las etapas 9203 (ingreso por urgencias) no previas, en horas | SQL | No |
| `max_dur_3045729_h` | decimal | Duración máxima de las etapas 3045729 (movimientos) no previas, en horas | SQL | No |
| `max_dur_9201_h` | decimal | Duración máxima de las etapas 9201 (piso) no previas, en horas | SQL | No |
| `fin_fraccion_segundo` | booleano | Alguna etapa no previa tiene un fin con fracción de segundo | SQL | No |
| `n_visitas` | entero | Visitas 9203 fusionadas en el episodio | `construir_episodios` | No |
| `edad` | decimal | Año de llegada − `year_of_birth`; `NaN` solo si no hay `year_of_birth` (las visitas con año < 1900 o edad negativa se excluyen; las edades > 110 se conservan) | `preparar_visitas` | Sí |
| `grupo_etario` | texto | `pediatria` (< 18), `adulto` (18–64), `adulto_mayor` (≥ 65) o `sin_dato` | `preparar_visitas` | Sí |
| `sexo` | texto | `femenino`, `masculino` u `otro_o_sin_dato` | SQL / `preparar_visitas` | Sí |
| `grupo` | texto | Grupo de análisis: `1_contacto_breve`, `2_atencion_urgencias` o `3_hospitalizado` | `construir_episodios` | No |
| `los_recortado` | booleano | Hospitalizado con `inicio_piso` anterior a la llegada: LOS recortado a 0 | `construir_episodios` | No |
| `los_h` | decimal | Tiempo de permanencia en urgencias, en horas (hospitalizado: `inicio_piso − llegada`; resto: `fin_urg − llegada`) | `construir_episodios` | No |
| `los_mas_4h` … `los_mas_72h` | booleano nulable | LOS por encima de 4, 6, 8, 12, 24 y 72 h (solo grupos 2 y 3) | `construir_episodios` | No |
| `horas_hasta_siguiente` | decimal | Horas entre `fin_episodio` y la llegada del siguiente episodio del paciente | `construir_episodios` | No |
| `reconsulta_72h_sin_censura` | booleano | El siguiente episodio llega en 72 h o menos | `construir_episodios` | No |
| `reconsulta_72h` | booleano nulable | Igual, con censura: vacío si la ventana pasa del final de los datos | `construir_episodios` | No |
| `reconsulta_7d_sin_censura` | booleano | El siguiente episodio llega en 7 días o menos | `construir_episodios` | No |
| `reconsulta_7d` | booleano nulable | Igual, con censura | `construir_episodios` | No |
| `en_poblacion` | booleano | Llegada entre `FECHA_INICIO_ANALISIS` y `FECHA_CORTE_ANALISIS` (población de análisis) | `construir_episodios` | Sí |
| `valido_para_tiempos` | booleano | El episodio entra a los cálculos de LOS. Lo crea `aplicar_reglas_episodio` según `REGLAS_EPISODIO`; con todas las reglas en «conservar», es True en todos. Solo en el dataset final | `aplicar_reglas_episodio` (notebook 05) | No |

Si alguna regla de `REGLAS_REGISTRO` tuviera la acción `marcar`, el dataset tendría además la columna `marca_<regla>`.
