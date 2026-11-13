"""Constantes, umbrales y rutas del proyecto."""

import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from . import estilo

# --- Rutas -----------------------------------------------------------------
# Se calculan desde la ubicación de este archivo, no desde el directorio de trabajo.
RAIZ = Path(__file__).resolve().parent.parent

DATA_RAW = RAIZ / "data" / "raw"
DATA_INTERIM = RAIZ / "data" / "interim"
DATA_PROCESSED = RAIZ / "data" / "processed"
FIGURAS = RAIZ / "reports" / "figures"
SQL_DIR = RAIZ / "sql"

# --- Base de datos -----------------------------------------------------------
# Solo se lee el esquema; las credenciales se leen en src/db.py y nunca se guardan aquí.
load_dotenv(RAIZ / ".env")

SCHEMA = (os.getenv("DB_SCHEMA") or "uninorte_omop").split("#")[0].strip() or "uninorte_omop"
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", SCHEMA):
    raise ValueError("DB_SCHEMA debe ser un identificador SQL simple (letras, números y guion bajo).")

# --- Conceptos OMOP ----------------------------------------------------------
# --- Conceptos OMOP (significado confirmado por el hospital, tabla 2.1) ------
CONCEPTO_URGENCIAS = 9203  # visita: urgencias / etapa: ingreso al hospital por urgencias
CONCEPTO_SEGMENTO = 3045729  # etapa: cada movimiento o etapa del paciente en el hospital
CONCEPTO_PISO = 9201  # etapa: hospitalización en piso
CONCEPTO_AMBULATORIO = 581479  # visita: consulta externa / etapa: ingreso ambulatorio (dura 0)

# --- Construcción de episodios -----------------------------------------------
# Evento previo: una etapa que empieza más de 1 h antes de la llegada es un evento previo
# asociado a la visita; no se usa para tiempos ni para definir hospitalización.
TOLERANCIA_EVENTO_PREVIO = pd.Timedelta("1h")
VENTANA_HOSP_PREVIA = pd.Timedelta("30D")  # variable hosp_previa_30d
UMBRAL_FUSION_MIN = 60  # fusión de visitas en episodios
UMBRALES_SENSIBILIDAD = [30, 60, 120]  # sensibilidad de la fusión de visitas
CONTACTO_BREVE = pd.Timedelta("5min")  # grupos de análisis: contacto breve

# Grupos de análisis: tres grupos, evaluados en este orden. Nombres, etiquetas y colores viven en src/estilo.py.
GRUPOS = estilo.ROLES
GRUPOS_TIEMPOS = GRUPOS[1:]  # los tiempos solo se analizan en los grupos 2 y 3
ETIQUETAS_GRUPO = estilo.ETIQUETA_ROL
ETIQUETAS_CORTAS_GRUPO = estilo.ETIQUETA_CORTA_ROL

# --- Edad al llegar -----------------------------------------------------------------
# La edad es inválida (NaN) solo si year_of_birth < 1900 o si es negativa. Las edades mayores a
# EDAD_MAYOR_REVISION se conservan y solo se marcan (regla edad_mayor_110).
ANIO_NACIMIENTO_MINIMO = 1900
EDAD_MAYOR_REVISION = 110
GRUPOS_ETARIOS = ("pediatria", "adulto", "adulto_mayor")

# --- Indicadores ---------------------------------------------------------------
UMBRAL_OPERATIVO_H = 12  # umbral del hospital para permanencia en urgencias
UMBRALES_LOS_H = [4, 6, 8, 12, 24, 72]
VENTANAS_RECONSULTA = {"72h": pd.Timedelta("72h"), "7d": pd.Timedelta("7D")}  # reconsulta

# Población de análisis. Desde abril de 2026 los datos están incompletos;
# los episodios posteriores se construyen (para reconsultas) pero no se analizan.
FECHA_INICIO_ANALISIS = pd.Timestamp("2023-01-01 00:00:00")
FECHA_CORTE_ANALISIS = pd.Timestamp("2026-03-31 23:59:59")

# --- Privacidad ----------------------------------------------------------------
MIN_CELDA = 10  # conteos menores se muestran como "<10"

# --- Referencia de DBeaver (reglas anteriores, umbral de 60 min) -----------------
# Sin visitas sin etapas y sin corte temporal. Con las reglas nuevas (definición de hospitalizado,
# población de análisis y visitas sin etapas) los números cambian: la comparación del notebook 03
# es informativa, no un error.
REFERENCIA_SQL_60MIN = {
    "episodios": 440_202,
    "hosp_con_hora_piso": 36_382,
    "mediana_los_hosp_h": 24.0,
    "pct_mas_12h_hosp": 68.2,
    "pct_mas_24h_hosp": 50.0,
    "mediana_los_atencion_h": 7.0,
    "pct_mas_12h_atencion": 28.0,
    "pct_reconsulta_72h": 5.4,
}
# Robustez (referencia de DBeaver): con 30, 60 y 120 min el % > 12 h de
# hospitalizados cambia menos de este número de puntos.
REFERENCIA_VARIACION_SENSIBILIDAD_PP = 0.1

# --- Reglas de limpieza (decididas por el equipo) ---------------------------------------
# Las reglas de registro decididas por el equipo se aplican en el notebook 03, a nivel de visita y
# antes de la fusión en episodios. Todas las reglas de registro
# están decididas; las que están en "conservar" con varias formas de detección no necesitan "criterio".
# Ninguna acción se aplica mientras la regla esté en "pendiente". Para decidir una regla, el equipo cambia su
# "accion" (y su "criterio", si la regla tiene más de una forma de detección) y vuelve a correr
# desde el notebook 03. Las funciones que aplican las acciones están en src/limpieza.py.
ACCIONES_REGISTRO = ("pendiente", "conservar", "marcar", "nan", "excluir", "excluir_visita_sin_diagnostico")
ACCIONES_EPISODIO = ("pendiente", "conservar", "excluir_de_tiempos", "excluir")

# Reglas a nivel de visita. "columnas_nan": columnas que se ponen en NaN si la acción es "nan"
# (lista vacía: la acción "nan" no aplica a esa regla). "criterios": formas de detección posibles.
REGLAS_REGISTRO = {
    "anio_nacimiento_imposible": {
        "descripcion": "Año de nacimiento imposible",
        "deteccion": "year_of_birth < 1900 (incluye el año 1)",
        "columnas_nan": ["edad"],
        "accion": "excluir",
    },
    "edad_negativa": {
        "descripcion": "Edad negativa",
        "deteccion": "año de llegada − year_of_birth < 0 (con year_of_birth ≥ 1900)",
        "columnas_nan": ["edad"],
        "accion": "excluir",
    },
    "edad_mayor_110": {
        "descripcion": "Edad mayor a 110",
        "deteccion": "año de llegada − year_of_birth > 110; la edad se conserva (no se pone en NaN)",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "sexo_sin_dato": {
        "descripcion": "Sexo sin dato",
        "deteccion": "gender_concept_id = 0 o sin traducción (sexo distinto de FEMALE y MALE)",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "etapas_duracion_0": {
        "descripcion": "Etapas de duración 0",
        "deteccion": "la visita tiene al menos una etapa no previa con fin igual al inicio",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "etapas_duracion_extrema": {
        "descripcion": "Etapas de duración extrema",
        "deteccion": ("duración máxima de alguna etapa no previa (9203, 3045729 o 9201) por encima del límite "
                      "de su tipo de etapa"),
        "criterios": ("p99_9", "tukey_log"),
        "criterio": "pendiente",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "fin_fraccion_segundo": {
        "descripcion": "Fines de etapa con fracción de segundo",
        "deteccion": "alguna etapa no previa tiene un fin con microsegundos distintos de 0",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "hosp_antes_de_llegada": {
        "descripcion": "Hospitalización que empieza antes de la llegada",
        "deteccion": "inicio_piso < llegada (dentro de la tolerancia de 1 h)",
        "columnas_nan": [],
        "accion": "excluir",
    },
    "visitas_sin_etapas": {
        "descripcion": "Visitas sin etapas",
        "deteccion": "la visita no tiene etapas no previas",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "ingresos_9203_largos": {
        "descripcion": "Ingresos por urgencias de duración larga",
        "deteccion": "alguna etapa 9203 no previa de la visita dura más de 22 minutos",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "etapas_por_visita_extremas": {
        "descripcion": "Número extremo de etapas por visita",
        "deteccion": "n_etapas por encima del límite",
        "criterios": ("p99_9", "tukey_log"),
        "criterio": "pendiente",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "paciente_muchas_visitas": {
        "descripcion": "Pacientes con muchísimas visitas",
        "deteccion": "visitas de urgencias del paciente en el año por encima del límite",
        "criterios": ("p99_9", "tukey_log"),
        "criterio": "pendiente",
        "columnas_nan": [],
        "accion": "conservar",
    },
    "recorridos_identicos_otro_paciente": {
        "descripcion": "Recorridos idénticos entre pacientes distintos",
        "deteccion": ("par de visitas 9203 de 2 pacientes distintos con la misma llegada y las mismas etapas "
                      "(tipo, inicio y fin idénticos); se marca la visita sin diagnósticos cuando la otra sí tiene "
                      "(sql/03_recorridos_identicos_marcas.sql)"),
        "columnas_nan": [],
        # Solo en los pares donde exactamente una visita tiene diagnósticos se excluye la que no tiene; los
        # pares donde ninguna o ambas tienen diagnósticos se conservan.
        "accion": "excluir_visita_sin_diagnostico",
    },
}

# Reglas a nivel de episodio (decididas por el equipo en el notebook 05). "excluir_de_tiempos" deja
# valido_para_tiempos = False en los episodios marcados.
REGLAS_EPISODIO = {
    "los_extremo": {
        "descripcion": "LOS extremo",
        "deteccion": "LOS por encima del percentil 99 o 99,9 de su grupo (atención en urgencias u hospitalizado)",
        "criterios": ("p99", "p99_9"),
        "accion": "conservar",
    },
    "fin_fraccion_segundo": {
        "descripcion": "Fines con fracción de segundo",
        "deteccion": "alguna visita del episodio tiene un fin de etapa con fracción de segundo",
        "accion": "conservar",
    },
    "muchas_visitas_en_episodio": {
        "descripcion": "Muchas visitas unidas en un episodio",
        "deteccion": "n_visitas por encima del percentil 99,9",
        "accion": "conservar",
    },
    "los_recortado": {
        "descripcion": "LOS recortado a 0",
        "deteccion": "hospitalizado con inicio_piso anterior a la llegada (LOS recortado a 0)",
        "accion": "conservar",
    },
    "hosp_etapas_urg_despues_de_piso": {
        "descripcion": "Hospitalizado con etapas de urgencias después de subir a piso",
        "deteccion": "hospitalizado con fin_urg > inicio_piso",
        "accion": "conservar",
    },
    "contacto_breve_por_visitas_unidas": {
        "descripcion": "Contacto breve por visitas unidas",
        "deteccion": ("contacto breve con LOS ≥ 5 min: visitas sin etapas unidas en un mismo episodio "
                      "(el LOS va de la primera a la última llegada)"),
        "accion": "conservar",
    },
    "hosp_sin_inicio_piso": {
        "descripcion": "Hospitalizado sin inicio de piso",
        "deteccion": "hospitalizado con inicio_piso vacío",
        "accion": "conservar",
    },
    "atencion_menos_5min": {
        "descripcion": "Atención en urgencias con LOS < 5 min",
        "deteccion": "grupo de atención en urgencias con LOS menor a 5 minutos",
        "accion": "conservar",
    },
    "fin_urg_antes_llegada": {
        "descripcion": "Fin de urgencias antes de la llegada",
        "deteccion": "fin_urg < llegada",
        "accion": "conservar",
    },
    "paciente_muchos_episodios": {
        "descripcion": "Pacientes con muchísimos episodios",
        "deteccion": "episodios del paciente en el año por encima del percentil 99,9",
        "accion": "conservar",
    },
    "edad_nan": {
        "descripcion": "Edad en NaN",
        "deteccion": "edad sin dato (sin year_of_birth; los años < 1900 y las edades negativas se excluyen en el notebook 03)",
        "accion": "conservar",
    },
}

# Ingresos por urgencias (etapa 9203) de duración larga.
UMBRAL_INGRESO_LARGO_MIN = 22
UMBRAL_INGRESO_MUY_LARGO_H = 24

# Percentiles de detección de extremos.
PERCENTILES_EXTREMOS = {"p99": 0.99, "p99_9": 0.999}
FACTOR_TUKEY_LOG = 3.0  # Q3 + 3 × RIC sobre el logaritmo

# --- Ocupación (notebook 06) -------------------------------------------------------------
# Capacidad ACTUAL (2026) entregada por el hospital. Pudo ser distinta en años anteriores: por eso
# el % sobre la capacidad es una medida complementaria y siempre se rotula «capacidad actual (2026)».
CAPACIDAD_ACTUAL = {
    "piso": {"pediatria": 8, "adultos": 64, "total": 72},
    "cuidados_especiales": {"intermedia_adultos": 6, "intensiva_adultos": 14,
                            "incubadora_intermedia_neonatal": 6, "incubadora_intensiva_neonatal": 3,
                            "incubadora_basico_neonatal": 1, "total": 30},
    "tpr": 4,
    "observacion_urgencias": {"pediatria": 14, "adultos_hombres": 18, "adultos_mujeres": 26, "total": 58},
}
CAPACIDAD_PISO_CON_ESPECIALES = 102  # 72 de piso + 30 de cuidados especiales
# Periodo de calentamiento: los datos empiezan el 2023-01-01 y no incluyen a los pacientes que ya
# estaban en urgencias o en piso ese día (llegaron en 2022), así que el censo de enero de 2023 sale
# artificialmente bajo (en piso puede durar semanas). Los censos se calculan desde
# FECHA_INICIO_ANALISIS, pero tablas, gráficos, percentiles, saturación, deciles y exportaciones del
# notebook 06 usan solo horas y episodios desde FECHA_INICIO_CENSO.
FECHA_INICIO_CENSO = pd.Timestamp("2023-02-01")
EDAD_PEDIATRIA = 18  # menores de esta edad: pediatría; el resto, adultos
PERCENTIL_SATURACION = 90  # hora saturada: por encima de este percentil de su trimestre
HORAS_DIA_SATURADO = 3  # día saturado: al menos estas horas saturadas
# El censo 9201 supera sistemáticamente la capacidad informada; desactivado hasta confirmar con el hospital la
# cobertura del concepto 9201 y la capacidad total.
USAR_CAPACIDAD_PISO = False
