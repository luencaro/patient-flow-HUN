"""Construcción de episodios de urgencias a partir de visitas (decisiones D1–D8)."""

import numpy as np
import pandas as pd

from .config import (
    CONTACTO_BREVE,
    GRUPOS,
    UMBRAL_FUSION_MIN,
    UMBRALES_LOS_H,
    VENTANAS_RECONSULTA,
)

COLUMNAS_VISITA = (
    "visit_occurrence_id",
    "person_id",
    "llegada",
    "fin",
    "fin_urg",
    "inicio_piso",
    "fin_piso",
    "hosp",
    "tiene_9203",
    "n_segmentos",
    "n_desplazados",
    "year_of_birth",
    "sexo",
)
COLUMNAS_FECHA = ("llegada", "fin", "fin_urg", "inicio_piso", "fin_piso")
COLUMNAS_BOOL = ("hosp", "tiene_9203")
COLUMNAS_ENTERAS = ("n_segmentos", "n_desplazados")

EDAD_MAXIMA = 110
MAPA_SEXO = {"FEMALE": "femenino", "MALE": "masculino"}

G1, G2, G3, G4 = GRUPOS


def _horas(delta: pd.Series) -> pd.Series:
    """Convierte una serie de ``Timedelta`` a horas (float)."""
    return delta.dt.total_seconds() / 3600


def preparar_visitas(df: pd.DataFrame) -> pd.DataFrame:
    """Ajusta tipos y calcula edad (D8), estado de la edad y grupo etario.

    - Fechas a ``datetime64`` (sin zona horaria), booleanos y enteros.
    - ``edad`` = año de llegada − ``year_of_birth``; valores < 0 o > 110 quedan ``NaN``.
    - ``estado_edad``: ``valida``, ``negativa``, ``mayor_110`` o ``sin_dato``.
    - ``grupo_etario``: ``pediatria`` (< 18), ``adulto`` (18–64), ``adulto_mayor`` (≥ 65)
      o ``sin_dato``.
    - ``sexo``: ``femenino``, ``masculino`` u ``otro_o_sin_dato``.
    """
    faltantes = [c for c in COLUMNAS_VISITA if c not in df.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas en las visitas: {faltantes}")

    v = df.copy()
    for columna in COLUMNAS_FECHA:
        v[columna] = pd.to_datetime(v[columna])
        if v[columna].dt.tz is not None:
            v[columna] = v[columna].dt.tz_localize(None)
    for columna in COLUMNAS_BOOL:
        v[columna] = v[columna].eq(True)
    for columna in COLUMNAS_ENTERAS:
        v[columna] = pd.to_numeric(v[columna]).fillna(0).astype("int64")
    v["visit_occurrence_id"] = v["visit_occurrence_id"].astype("int64")
    v["person_id"] = v["person_id"].astype("int64")
    v["year_of_birth"] = pd.to_numeric(v["year_of_birth"], errors="coerce")

    edad_bruta = v["llegada"].dt.year - v["year_of_birth"]
    v["estado_edad"] = np.select(
        [edad_bruta.isna(), edad_bruta < 0, edad_bruta > EDAD_MAXIMA],
        ["sin_dato", "negativa", "mayor_110"],
        default="valida",
    )
    v["edad"] = edad_bruta.where(v["estado_edad"] == "valida").astype(float)
    v["grupo_etario"] = np.select(
        [v["edad"].isna(), v["edad"] < 18, v["edad"] < 65],
        ["sin_dato", "pediatria", "adulto"],
        default="adulto_mayor",
    )

    sexo = v["sexo"].astype(str).str.strip().str.upper()
    v["sexo"] = sexo.map(MAPA_SEXO).fillna("otro_o_sin_dato")
    return v


def reportar_edades(visitas: pd.DataFrame) -> pd.DataFrame:
    """Tabla agregada con el número y porcentaje de visitas por ``estado_edad``."""
    tabla = (
        visitas["estado_edad"]
        .value_counts()
        .rename("n_visitas")
        .rename_axis("estado_edad")
        .to_frame()
    )
    tabla["pct_visitas"] = 100 * tabla["n_visitas"] / tabla["n_visitas"].sum()
    return tabla


def fusionar_episodios(visitas: pd.DataFrame, umbral_min: int = UMBRAL_FUSION_MIN) -> pd.DataFrame:
    """Une visitas 9203 del mismo paciente en episodios (D4) con lógica de islas.

    Una visita abre un episodio nuevo si es la primera del paciente o si su llegada
    es posterior a (máximo fin acumulado de las anteriores + umbral). Para el fin
    de cada visita se usa ``fin`` y, si falta o es anterior a la llegada, la llegada
    (``fin_ref``). Es vectorizada: no recorre pacientes con bucles.

    Devuelve un episodio por fila con ``episodio_id`` (entero interno, nunca se muestra).
    """
    umbral = pd.Timedelta(minutes=umbral_min)
    v = visitas.sort_values(
        ["person_id", "llegada", "visit_occurrence_id"], kind="mergesort"
    ).reset_index(drop=True)

    fin_ref = v["fin"].where(v["fin"] >= v["llegada"], v["llegada"])
    fin_acumulado = fin_ref.groupby(v["person_id"], sort=False).cummax()
    misma_persona = v["person_id"].eq(v["person_id"].shift(1))
    fin_prev = fin_acumulado.shift(1).where(misma_persona)

    nueva_isla = fin_prev.isna() | (v["llegada"] > fin_prev + umbral)
    v["fin_ref"] = fin_ref
    # Como las filas están ordenadas por paciente, la suma acumulada global ya
    # identifica cada episodio de forma única.
    v["episodio_id"] = nueva_isla.cumsum().astype("int64")
    v["episodio_n"] = nueva_isla.astype("int64").groupby(v["person_id"], sort=False).cumsum()

    episodios = v.groupby("episodio_id", sort=True).agg(
        person_id=("person_id", "first"),
        episodio_n=("episodio_n", "first"),
        llegada=("llegada", "min"),
        fin_episodio=("fin_ref", "max"),
        fin=("fin", "max"),
        fin_urg=("fin_urg", "max"),
        inicio_piso=("inicio_piso", "min"),
        fin_piso=("fin_piso", "max"),
        hosp=("hosp", "any"),
        tiene_9203=("tiene_9203", "any"),
        n_segmentos=("n_segmentos", "sum"),
        n_desplazados=("n_desplazados", "sum"),
        n_visitas=("visit_occurrence_id", "count"),
        edad=("edad", "first"),
        grupo_etario=("grupo_etario", "first"),
        sexo=("sexo", "first"),
    )
    return episodios.reset_index()


def asignar_grupo(ep: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna ``grupo`` (D6), evaluada en este orden:

    1. ``1_contacto_breve``: no hospitalizado y ``fin_urg − llegada < 5 min``.
    2. ``2_no_hosp_atencion``: no hospitalizado y ≥ 5 min (o sin ``fin_urg``).
    3. ``3_hosp_con_hora_piso``: hospitalizado con ``inicio_piso ≥ llegada``.
    4. ``4_hosp_sin_hora_piso``: el resto de hospitalizados.
    """
    e = ep.copy()
    no_hosp = ~e["hosp"]
    duracion_urg = e["fin_urg"] - e["llegada"]
    condiciones = [
        no_hosp & (duracion_urg < CONTACTO_BREVE),
        no_hosp,
        e["hosp"] & e["inicio_piso"].notna() & (e["inicio_piso"] >= e["llegada"]),
    ]
    e["grupo"] = np.select(condiciones, [G1, G2, G3], default=G4)
    return e


def calcular_los(ep: pd.DataFrame, umbrales: list = UMBRALES_LOS_H) -> pd.DataFrame:
    """Agrega ``los_h`` (D5) y columnas ``los_mas_{u}h`` (booleano nulable) por umbral.

    - Grupo 3: ``inicio_piso − llegada``.
    - Grupos 1 y 2: ``fin_urg − llegada``.
    - Grupo 4: ``NaN``.
    """
    e = ep.copy()
    los_piso = _horas(e["inicio_piso"] - e["llegada"])
    los_urg = _horas(e["fin_urg"] - e["llegada"])
    e["los_h"] = np.where(
        e["grupo"].eq(G3),
        los_piso,
        np.where(e["grupo"].isin([G1, G2]), los_urg, np.nan),
    )
    for umbral in umbrales:
        e[f"los_mas_{umbral}h"] = (e["los_h"] > umbral).astype("boolean").mask(e["los_h"].isna())
    return e


def calcular_reconsultas(
    ep: pd.DataFrame,
    fecha_fin_datos: pd.Timestamp | None = None,
    ventanas: dict = VENTANAS_RECONSULTA,
) -> pd.DataFrame:
    """Marca si el siguiente episodio del paciente llega dentro de cada ventana (D7).

    El tiempo se mide desde ``fin_episodio`` hasta la llegada del siguiente.
    Columnas agregadas:

    - ``horas_hasta_siguiente`` (``NaN`` si no hay siguiente episodio).
    - ``reconsulta_{ventana}_sin_censura``: booleano.
    - ``reconsulta_{ventana}``: con censura; queda nulo si ``fin_episodio + ventana``
      supera ``fecha_fin_datos`` (por defecto, la última llegada de los datos).
    """
    e = ep.copy()
    if fecha_fin_datos is None:
        fecha_fin_datos = e["llegada"].max()

    orden = e.sort_values(["person_id", "llegada", "episodio_id"], kind="mergesort")
    misma_persona = orden["person_id"].eq(orden["person_id"].shift(-1))
    llegada_siguiente = orden["llegada"].shift(-1).where(misma_persona)
    e["horas_hasta_siguiente"] = _horas(llegada_siguiente - orden["fin_episodio"])

    for nombre, ventana in ventanas.items():
        limite_h = ventana / pd.Timedelta(hours=1)
        sin_censura = e["horas_hasta_siguiente"].le(limite_h)
        censurado = (e["fin_episodio"] + ventana) > fecha_fin_datos
        e[f"reconsulta_{nombre}_sin_censura"] = sin_censura
        e[f"reconsulta_{nombre}"] = sin_censura.astype("boolean").mask(censurado)
    return e


def construir_episodios(visitas: pd.DataFrame, umbral_min: int = UMBRAL_FUSION_MIN) -> pd.DataFrame:
    """Fusiona, asigna grupos y calcula LOS y reconsultas. ``visitas`` debe venir de ``preparar_visitas``."""
    faltantes = {"edad", "grupo_etario", "sexo", "estado_edad"} - set(visitas.columns)
    if faltantes:
        raise ValueError("Primero aplica preparar_visitas() a las visitas.")
    ep = fusionar_episodios(visitas, umbral_min)
    ep = asignar_grupo(ep)
    ep = calcular_los(ep)
    ep = calcular_reconsultas(ep, fecha_fin_datos=visitas["llegada"].max())
    return ep


def valores_comparables(ep: pd.DataFrame) -> dict:
    """Métricas con la misma definición que los valores de referencia de SQL (ver config)."""
    hosp = ep["hosp"]
    return {
        "episodios": int(len(ep)),
        "no_hospitalizados": int((~hosp).sum()),
        "hospitalizados": int(hosp.sum()),
        "hosp_sin_hora_piso": int((hosp & ep["inicio_piso"].isna()).sum()),
        "hosp_con_hora_piso_valida": int(ep["grupo"].eq(G3).sum()),
        "pct_reconsulta_72h_no_hosp_sin_censura": float(
            100 * ep.loc[~hosp, "reconsulta_72h_sin_censura"].mean()
        ),
        "pct_reconsulta_72h_hosp_sin_censura": float(
            100 * ep.loc[hosp, "reconsulta_72h_sin_censura"].mean()
        ),
    }


def resumen_sensibilidad(visitas: pd.DataFrame, umbrales: list) -> pd.DataFrame:
    """Métricas clave de los episodios para cada umbral de fusión (una fila por umbral).

    Incluye episodios, % hospitalizados, % con más de una visita, máximo de visitas
    por episodio, tamaño de cada grupo, mediana y % > 12 h del grupo 3, y
    reconsulta a 72 h sin y con censura. Solo contiene agregados.
    """
    filas = []
    for umbral in umbrales:
        ep = construir_episodios(visitas, umbral)
        g3 = ep[ep["grupo"].eq(G3)]
        tamanos = ep["grupo"].value_counts()
        fila = {
            "umbral_min": umbral,
            "n_episodios": int(len(ep)),
            "pct_hospitalizados": 100 * ep["hosp"].mean(),
            "pct_multivisita": 100 * ep["n_visitas"].gt(1).mean(),
            "max_visitas_episodio": int(ep["n_visitas"].max()),
        }
        for grupo in GRUPOS:
            fila[f"n_{grupo}"] = int(tamanos.get(grupo, 0))
        fila["mediana_los_g3_h"] = g3["los_h"].median()
        fila["pct_mas_12h_g3"] = 100 * g3["los_mas_12h"].mean()
        fila["pct_reconsulta_72h_sin_censura"] = 100 * ep["reconsulta_72h_sin_censura"].mean()
        fila["pct_reconsulta_72h_con_censura"] = 100 * ep["reconsulta_72h"].mean()
        filas.append(fila)
    return pd.DataFrame(filas).set_index("umbral_min")
