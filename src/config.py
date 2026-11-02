"""Constantes, umbrales y rutas del proyecto."""

import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

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
CONCEPTO_URGENCIAS = 9203  # Emergency Room Visit (visita) / ingreso o triage (etapa)
CONCEPTO_SEGMENTO = 3045729  # Treatment urgency: segmentos de atención en urgencias
CONCEPTO_PISO = 9201  # Inpatient Visit: hospitalización en piso
CONCEPTO_AMBULATORIO = 581479  # Ambulatory Rehabilitation Visit

# --- Construcción de episodios -----------------------------------------------
TOLERANCIA_DESPLAZAMIENTO = pd.Timedelta("1h")  # D2
UMBRAL_FUSION_MIN = 60  # D4
UMBRALES_SENSIBILIDAD = [30, 60, 120]  # D4
CONTACTO_BREVE = pd.Timedelta("5min")  # D6, grupo 1

GRUPOS = (
    "1_contacto_breve",
    "2_no_hosp_atencion",
    "3_hosp_con_hora_piso",
    "4_hosp_sin_hora_piso",
)
GRUPOS_TIEMPOS = ("2_no_hosp_atencion", "3_hosp_con_hora_piso")  # D6

# --- Indicadores ---------------------------------------------------------------
UMBRAL_OPERATIVO_H = 12  # umbral del hospital para permanencia en urgencias
UMBRALES_LOS_H = [4, 6, 8, 12, 24, 72]
VENTANAS_RECONSULTA = {"72h": pd.Timedelta("72h"), "7d": pd.Timedelta("7D")}  # D7

# D9: último instante con meses completos para tendencias mensuales y anuales.
FECHA_CORTE_TENDENCIAS = pd.Timestamp("2026-06-30 23:59:59")

# --- Privacidad ----------------------------------------------------------------
MIN_CELDA = 10  # conteos menores se muestran como "<10"

# --- Referencia obtenida en DBeaver (24-10-2026) con umbral de 60 min -----------
# Sirve para que el notebook 02 compare la implementación en pandas.
REFERENCIA_SQL_60MIN = {
    "episodios": 440_202,
    "no_hospitalizados": 397_528,
    "hospitalizados": 42_674,
    "hosp_sin_hora_piso": 6_290,
    "hosp_con_hora_piso_valida": 36_382,
    "pct_reconsulta_72h_no_hosp_sin_censura": 5.65,
    "pct_reconsulta_72h_hosp_sin_censura": 3.27,
}
TOLERANCIA_REFERENCIA_PCT = 1.0  # diferencia relativa máxima antes de advertir
