"""Construcción de episodios de urgencias a partir de visitas (decisiones D1–D11)."""

import numpy as np
import pandas as pd

from .config import (
    ANIO_NACIMIENTO_MINIMO,
    CONTACTO_BREVE,
    EDAD_MAXIMA,
    FECHA_CORTE_ANALISIS,
    FECHA_INICIO_ANALISIS,
    GRUPOS,
    GRUPOS_TIEMPOS,
    UMBRAL_FUSION_MIN,
    UMBRAL_OPERATIVO_H,
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
    "n_etapas",
    "n_segmentos",
    "n_eventos_previos",
    "hosp_previa_30d",
    "nota_consulta_urg",
    "year_of_birth",
    "sexo",
)
COLUMNAS_FECHA = ("llegada", "fin", "fin_urg", "inicio_piso", "fin_piso")
COLUMNAS_BOOL = ("hosp", "tiene_9203", "hosp_previa_30d", "nota_consulta_urg")
COLUMNAS_ENTERAS = ("n_etapas", "n_segmentos", "n_eventos_previos")

MAPA_SEXO = {"FEMALE": "femenino", "MALE": "masculino"}

G1, G2, G3 = GRUPOS


def _horas(delta: pd.Series) -> pd.Series:
    """Convierte una serie de ``Timedelta`` a horas (float)."""
    return delta.dt.total_seconds() / 3600


def preparar_visitas(df: pd.DataFrame) -> pd.DataFrame:
    """Ajusta tipos, rellena los fines de las visitas sin etapas (D10) y calcula la edad (D8).

    - Fechas a ``datetime64`` (sin zona horaria), booleanos y enteros.
    - ``sin_etapas``: la visita no tiene ninguna etapa que no sea evento previo (D10).
      ``fin`` y ``fin_urg`` nulos se rellenan con ``llegada``.
    - ``edad`` = año de llegada − ``year_of_birth``. Queda ``NaN`` si ``year_of_birth`` es
      menor a 1900, o si la edad es negativa o mayor a 110.
    - ``estado_edad``: ``valida``, ``sin_dato``, ``anio_invalido``, ``negativa`` o ``mayor_110``.
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

    # D10: visitas sin etapas (o solo con eventos previos) terminan en su llegada.
    v["sin_etapas"] = v["n_etapas"].eq(0)
    v["fin"] = v["fin"].fillna(v["llegada"])
    v["fin_urg"] = v["fin_urg"].fillna(v["llegada"])

    edad_bruta = v["llegada"].dt.year - v["year_of_birth"]
    v["estado_edad"] = np.select(
        [
            v["year_of_birth"].isna(),
            v["year_of_birth"] < ANIO_NACIMIENTO_MINIMO,
            edad_bruta < 0,
            edad_bruta > EDAD_MAXIMA,
        ],
        ["sin_dato", "anio_invalido", "negativa", "mayor_110"],
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
    de cada visita se usa ``fin`` y, si es anterior a la llegada, la llegada
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
        hosp_previa_30d=("hosp_previa_30d", "any"),
        nota_consulta_urg=("nota_consulta_urg", "any"),
        sin_etapas=("sin_etapas", "all"),
        n_etapas=("n_etapas", "sum"),
        n_segmentos=("n_segmentos", "sum"),
        n_eventos_previos=("n_eventos_previos", "sum"),
        n_visitas=("visit_occurrence_id", "count"),
        edad=("edad", "first"),
        grupo_etario=("grupo_etario", "first"),
        sexo=("sexo", "first"),
    )
    return episodios.reset_index()


def asignar_grupo(ep: pd.DataFrame) -> pd.DataFrame:
    """Agrega la columna ``grupo`` (D6), evaluada en este orden:

    1. ``1_contacto_breve``: sin ninguna etapa no previa, o no hospitalizado y
       ``fin_urg − llegada < 5 min``.
    2. ``2_atencion_urgencias``: no hospitalizado y ≥ 5 min.
    3. ``3_hospitalizado``: tiene al menos un 9201 que no es evento previo (D3).
    """
    e = ep.copy()
    no_hosp = ~e["hosp"]
    duracion_urg = e["fin_urg"] - e["llegada"]
    condiciones = [
        e["sin_etapas"] | (no_hosp & (duracion_urg < CONTACTO_BREVE)),
        no_hosp,
    ]
    e["grupo"] = np.select(condiciones, [G1, G2], default=G3)
    return e


def calcular_los(ep: pd.DataFrame, umbrales: list = UMBRALES_LOS_H) -> pd.DataFrame:
    """Agrega ``los_h`` (D5), ``los_recortado`` y columnas ``los_mas_{u}h`` por umbral.

    - Grupo 3: ``inicio_piso − llegada``. Si ``inicio_piso`` es anterior a la llegada
      (dentro de la tolerancia de 1 h de D2), el LOS se recorta a 0 y
      ``los_recortado`` queda en ``True`` (D3).
    - Grupos 1 y 2: ``fin_urg − llegada``. Los tiempos del grupo 1 no se analizan.

    Las columnas ``los_mas_{u}h`` son booleanas nulables y solo tienen valor en los
    grupos 2 y 3.
    """
    e = ep.copy()
    los_piso = _horas(e["inicio_piso"] - e["llegada"])
    los_urg = _horas(e["fin_urg"] - e["llegada"])
    es_g3 = e["grupo"].eq(G3)

    e["los_recortado"] = es_g3 & los_piso.lt(0)
    e["los_h"] = np.where(es_g3, los_piso.clip(lower=0), los_urg)
    con_tiempos = e["grupo"].isin(list(GRUPOS_TIEMPOS)) & e["los_h"].notna()
    for umbral in umbrales:
        e[f"los_mas_{umbral}h"] = (e["los_h"] > umbral).astype("boolean").where(con_tiempos)
    return e


def contar_los_recortados(ep: pd.DataFrame) -> pd.DataFrame:
    """Tabla agregada: episodios del grupo 3 y cuántos tienen el LOS recortado a 0 (D3)."""
    g3 = ep[ep["grupo"].eq(G3)]
    tabla = pd.DataFrame(
        {"n": [len(g3)], "n_recortados": [int(g3["los_recortado"].sum())]},
        index=pd.Index([G3], name="grupo"),
    )
    tabla["pct_recortados"] = 100 * tabla["n_recortados"] / tabla["n"]
    return tabla


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


def marcar_poblacion(ep: pd.DataFrame) -> pd.DataFrame:
    """Agrega ``en_poblacion``: llegada entre ``FECHA_INICIO_ANALISIS`` y ``FECHA_CORTE_ANALISIS`` (D9)."""
    e = ep.copy()
    e["en_poblacion"] = e["llegada"].between(FECHA_INICIO_ANALISIS, FECHA_CORTE_ANALISIS)
    return e


def construir_episodios(visitas: pd.DataFrame, umbral_min: int = UMBRAL_FUSION_MIN) -> pd.DataFrame:
    """Fusiona, asigna grupos y calcula LOS, reconsultas y ``en_poblacion``.

    Devuelve todos los episodios (también los posteriores al corte, que sirven
    como episodio siguiente en las reconsultas). ``visitas`` debe venir de
    ``preparar_visitas``.
    """
    faltantes = {"edad", "grupo_etario", "sexo", "estado_edad", "sin_etapas"} - set(visitas.columns)
    if faltantes:
        raise ValueError("Primero aplica preparar_visitas() a las visitas.")
    ep = fusionar_episodios(visitas, umbral_min)
    ep = asignar_grupo(ep)
    ep = calcular_los(ep)
    ep = calcular_reconsultas(ep, fecha_fin_datos=visitas["llegada"].max())
    ep = marcar_poblacion(ep)
    return ep


def valores_comparables(ep: pd.DataFrame) -> dict:
    """Métricas con la misma forma que la referencia de DBeaver (ver ``config.REFERENCIA_SQL_60MIN``).

    Para acercarse a la definición de la referencia se usan todos los episodios
    (sin corte temporal) excepto los que no tienen ninguna etapa. Las reglas no son
    idénticas (D3, D10), así que la comparación es solo informativa.
    """
    e = ep[~ep["sin_etapas"]]
    g2 = e.loc[e["grupo"].eq(G2), "los_h"]
    g3 = e.loc[e["grupo"].eq(G3), "los_h"]
    return {
        "episodios": int(len(e)),
        "hosp_con_hora_piso": int(e["grupo"].eq(G3).sum()),
        "mediana_los_hosp_h": float(g3.median()),
        "pct_mas_12h_hosp": float(100 * g3.gt(12).mean()),
        "pct_mas_24h_hosp": float(100 * g3.gt(24).mean()),
        "mediana_los_atencion_h": float(g2.median()),
        "pct_mas_12h_atencion": float(100 * g2.gt(12).mean()),
        "pct_reconsulta_72h": float(100 * e["reconsulta_72h_sin_censura"].mean()),
    }


def resumen_sensibilidad(visitas: pd.DataFrame, umbrales: list) -> pd.DataFrame:
    """Métricas clave de los episodios de la población (D9) para cada umbral de fusión.

    Una fila por umbral: episodios, % hospitalizados, % con más de una visita,
    máximo de visitas por episodio, tamaño de cada uno de los tres grupos, mediana
    y % > 12 h de los grupos 2 y 3, y reconsulta a 72 h sin y con censura. Solo
    contiene agregados.
    """
    filas = []
    for umbral in umbrales:
        ep = construir_episodios(visitas, umbral)
        ep = ep[ep["en_poblacion"]]
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
        for grupo, sufijo in [(G2, "g2"), (G3, "g3")]:
            los = ep.loc[ep["grupo"].eq(grupo), "los_h"]
            fila[f"mediana_los_{sufijo}_h"] = los.median()
            fila[f"pct_mas_{UMBRAL_OPERATIVO_H}h_{sufijo}"] = 100 * los.gt(UMBRAL_OPERATIVO_H).mean()
        fila["pct_reconsulta_72h_sin_censura"] = 100 * ep["reconsulta_72h_sin_censura"].mean()
        fila["pct_reconsulta_72h_con_censura"] = 100 * ep["reconsulta_72h"].mean()
        filas.append(fila)
    return pd.DataFrame(filas).set_index("umbral_min")
