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
# D2: una etapa que empieza más de 1 h antes de la llegada es un evento previo
# asociado a la visita; no se usa para tiempos ni para definir hospitalización.
TOLERANCIA_EVENTO_PREVIO = pd.Timedelta("1h")
VENTANA_HOSP_PREVIA = pd.Timedelta("30D")  # D11, hosp_previa_30d
UMBRAL_FUSION_MIN = 60  # D4
UMBRALES_SENSIBILIDAD = [30, 60, 120]  # D4
CONTACTO_BREVE = pd.Timedelta("5min")  # D6, grupo 1

# D6: tres grupos, evaluados en este orden. Nombres, etiquetas y colores viven en src/estilo.py.
GRUPOS = estilo.ROLES
GRUPOS_TIEMPOS = GRUPOS[1:]  # los tiempos solo se analizan en los grupos 2 y 3
ETIQUETAS_GRUPO = estilo.ETIQUETA_ROL
ETIQUETAS_CORTAS_GRUPO = estilo.ETIQUETA_CORTA_ROL

# --- Edad (D8) -------------------------------------------------------------------
ANIO_NACIMIENTO_MINIMO = 1900
EDAD_MAXIMA = 110
GRUPOS_ETARIOS = ("pediatria", "adulto", "adulto_mayor")

# --- Indicadores ---------------------------------------------------------------
UMBRAL_OPERATIVO_H = 12  # umbral del hospital para permanencia en urgencias
UMBRALES_LOS_H = [4, 6, 8, 12, 24, 72]
VENTANAS_RECONSULTA = {"72h": pd.Timedelta("72h"), "7d": pd.Timedelta("7D")}  # D7

# D9: población de análisis. Desde abril de 2026 los datos están incompletos;
# los episodios posteriores se construyen (para reconsultas) pero no se analizan.
FECHA_INICIO_ANALISIS = pd.Timestamp("2023-01-01 00:00:00")
FECHA_CORTE_ANALISIS = pd.Timestamp("2026-03-31 23:59:59")

# --- Privacidad ----------------------------------------------------------------
MIN_CELDA = 10  # conteos menores se muestran como "<10"

# --- Referencia de DBeaver (reglas anteriores, umbral de 60 min) -----------------
# Sin visitas sin etapas y sin corte temporal. Con las reglas nuevas (D3, D9, D10)
# los números cambian: la comparación del notebook 02 es informativa, no un error.
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
