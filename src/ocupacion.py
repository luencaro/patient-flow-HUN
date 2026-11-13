"""Ocupación de urgencias y del piso: intervalos, censo horario, ocupación relativa y saturación.

Un intervalo ocupa un área desde ``inicio`` hasta ``fin`` (sin incluir ``fin``). El censo de una hora
en punto ``t`` es el número de intervalos con ``inicio <= t < fin``. Todo es vectorizado: no hay
bucles por hora ni por paciente.
"""

import numpy as np
import pandas as pd

from .config import (
    ANIO_NACIMIENTO_MINIMO,
    CAPACIDAD_ACTUAL,
    CAPACIDAD_PISO_CON_ESPECIALES,
    EDAD_PEDIATRIA,
    FECHA_INICIO_CENSO,
    GRUPOS,
    GRUPOS_TIEMPOS,
    HORAS_DIA_SATURADO,
    PERCENTIL_SATURACION,
    UMBRAL_OPERATIVO_H,
)
from .estadistica import tabla_los

G1, G2, G3 = GRUPOS
GRUPOS_EDAD = ("adultos", "pediatria")


# --- Intervalos ------------------------------------------------------------------------------------
def grupo_edad(edad: pd.Series) -> pd.Series:
    """``pediatria`` si la edad es menor a ``EDAD_PEDIATRIA``, ``adultos`` si no; vacío si la edad es NaN."""
    edad = pd.to_numeric(edad, errors="coerce")
    return pd.Series(np.where(edad.isna(), None, np.where(edad < EDAD_PEDIATRIA, "pediatria", "adultos")),
                     index=edad.index, dtype=object)


def preparar_estancias_piso(estancias: pd.DataFrame, fin_si_falta: pd.Timestamp) -> pd.DataFrame:
    """Ajusta la extracción ``06_estancias_piso``: tipos, edad y fines.

    - ``edad`` queda NaN si ``year_of_birth < 1900`` o si es negativa (misma regla que las visitas).
    - Las estancias sin fin siguen abiertas: su fin se completa con ``fin_si_falta``.
    - Un fin anterior al inicio se lleva al inicio (la estancia no suma tiempo).
    """
    e = estancias.copy()
    for columna in ("inicio", "fin"):
        e[columna] = pd.to_datetime(e[columna])
        if e[columna].dt.tz is not None:
            e[columna] = e[columna].dt.tz_localize(None)
    e["sin_fin"] = e["fin"].isna()
    e["fin"] = e["fin"].fillna(fin_si_falta)
    e["fin"] = e["fin"].where(e["fin"] >= e["inicio"], e["inicio"])
    edad = pd.to_numeric(e["edad"], errors="coerce")
    invalida = edad.lt(0)
    if "year_of_birth" in e.columns:
        invalida |= pd.to_numeric(e["year_of_birth"], errors="coerce").lt(ANIO_NACIMIENTO_MINIMO)
    e["edad"] = edad.where(~invalida)
    e["fin_fraccion_segundo"] = e["fin_fraccion_segundo"].eq(True)
    return e


def fusionar_intervalos(df: pd.DataFrame, por: str = "person_id", inicio: str = "inicio",
                        fin: str = "fin") -> pd.DataFrame:
    """Une los intervalos del mismo ``por`` que se traslapan o son contiguos, para no contar dos veces
    a un mismo paciente. Devuelve un intervalo por fila con el inicio mínimo y el fin máximo; las demás
    columnas toman el valor del primer intervalo, salvo las booleanas, que usan «alguno»."""
    d = df.sort_values([por, inicio, fin], kind="mergesort").reset_index(drop=True)
    fin_acumulado = d.groupby(por, sort=False)[fin].cummax()
    misma = d[por].eq(d[por].shift(1))
    fin_previo = fin_acumulado.shift(1).where(misma)
    nuevo = fin_previo.isna() | (d[inicio] > fin_previo)
    d["_isla"] = nuevo.cumsum()
    agregaciones = {inicio: "min", fin: "max", por: "first"}
    for columna in d.columns:
        if columna in agregaciones or columna == "_isla":
            continue
        agregaciones[columna] = "any" if pd.api.types.is_bool_dtype(d[columna]) else "first"
    return d.groupby("_isla", sort=True).agg(agregaciones).reset_index(drop=True)


def intervalos_urgencias(episodios: pd.DataFrame, con_atencion: bool = False) -> pd.DataFrame:
    """Intervalos de ocupación de urgencias desde los episodios de la población válidos para tiempos.

    Cada episodio ocupa urgencias desde ``llegada`` hasta su salida: ``inicio_piso`` si está
    hospitalizado, ``fin_urg`` si no. Las salidas anteriores a la llegada se llevan a la llegada.
    Con ``con_atencion``, solo atención en urgencias y hospitalizados. Los hospitalizados sin
    ``inicio_piso`` no tienen salida y quedan fuera.
    """
    e = episodios[episodios["en_poblacion"]]
    if "valido_para_tiempos" in e.columns:
        e = e[e["valido_para_tiempos"].astype(bool)]
    if con_atencion:
        e = e[e["grupo"].isin(list(GRUPOS_TIEMPOS))]
    salida = e["inicio_piso"].where(e["grupo"].eq(G3), e["fin_urg"])
    intervalos = pd.DataFrame({
        "inicio": e["llegada"],
        "fin": salida.where(salida >= e["llegada"], e["llegada"]),
        "grupo": e["grupo"],
        "edad": e["edad"],
    })
    intervalos = intervalos[intervalos["fin"].notna()]
    intervalos["grupo_edad"] = grupo_edad(intervalos["edad"])
    return intervalos


# --- Censo ------------------------------------------------------------------------------------------
def horas_del_periodo(desde, hasta) -> pd.DatetimeIndex:
    """Horas en punto entre ``desde`` y ``hasta`` (incluidas)."""
    return pd.date_range(pd.Timestamp(desde).ceil("h"), pd.Timestamp(hasta).floor("h"), freq="h")


def censo_horario(inicios, fines, desde, hasta) -> pd.Series:
    """Número de intervalos activos en cada hora en punto (``inicio <= t < fin``), con
    ``np.searchsorted`` sobre inicios y fines ordenados."""
    horas = horas_del_periodo(desde, hasta)
    inicios = np.sort(pd.to_datetime(pd.Series(inicios)).dropna().to_numpy(dtype="datetime64[ns]"))
    fines = np.sort(pd.to_datetime(pd.Series(fines)).dropna().to_numpy(dtype="datetime64[ns]"))
    t = horas.to_numpy(dtype="datetime64[ns]")
    activos = np.searchsorted(inicios, t, side="right") - np.searchsorted(fines, t, side="right")
    return pd.Series(activos, index=horas, name="censo")


def sin_calentamiento(datos, columna: str | None = None, desde=FECHA_INICIO_CENSO):
    """Quita el periodo de calentamiento: deja las filas desde ``desde`` (por defecto
    ``FECHA_INICIO_CENSO``), según el índice de fechas o según ``columna``."""
    if columna is None:
        return datos[datos.index >= desde]
    return datos[datos[columna] >= desde]


def censos_por_edad(intervalos: pd.DataFrame, desde, hasta) -> pd.DataFrame:
    """Censo horario en total, adultos y pediatría. Los intervalos sin edad solo cuentan en el total."""
    censos = {"total": censo_horario(intervalos["inicio"], intervalos["fin"], desde, hasta)}
    for grupo in GRUPOS_EDAD:
        parte = intervalos[intervalos["grupo_edad"].eq(grupo)]
        censos[grupo] = censo_horario(parte["inicio"], parte["fin"], desde, hasta)
    return pd.DataFrame(censos).rename_axis("hora")


def percentil_en_periodo(serie: pd.Series, periodo: str = "Q") -> pd.Series:
    """Para cada hora, el percentil (0–100) de su valor dentro de las horas de su mismo periodo
    (por defecto, el trimestre): % de horas del periodo con un valor menor o igual."""
    claves = serie.index.to_period(periodo)
    return serie.groupby(claves).rank(pct=True, method="max") * 100


def umbral_en_periodo(serie: pd.Series, percentil: float = PERCENTIL_SATURACION, periodo: str = "Q") -> pd.Series:
    """Percentil ``percentil`` de la serie dentro de cada periodo, repetido en cada hora."""
    claves = serie.index.to_period(periodo)
    return serie.groupby(claves).transform(lambda s: s.quantile(percentil / 100))


def horas_saturadas(serie: pd.Series, percentil: float = PERCENTIL_SATURACION, periodo: str = "Q") -> pd.Series:
    """Hora saturada: su valor supera el percentil ``percentil`` de su trimestre."""
    return serie.gt(umbral_en_periodo(serie, percentil, periodo))


def dias_saturados(horas: pd.Series, minimo: int = HORAS_DIA_SATURADO) -> pd.Series:
    """Día saturado: tiene ``minimo`` o más horas saturadas. Una fila por día."""
    return horas.astype(int).groupby(horas.index.normalize()).sum().ge(minimo).rename_axis("fecha")


def valor_en_instante(censo: pd.Series, instantes) -> np.ndarray:
    """Valor del censo en la hora en punto anterior o igual a cada instante (NaN si cae fuera)."""
    horas = censo.index.to_numpy(dtype="datetime64[ns]")
    t = pd.to_datetime(pd.Series(instantes)).to_numpy(dtype="datetime64[ns]")
    posicion = np.searchsorted(horas, t, side="right") - 1
    valido = (posicion >= 0) & (posicion < len(horas)) & ~np.isnat(t)
    valores = np.full(len(t), np.nan)
    valores[valido] = censo.to_numpy(dtype=float)[posicion[valido]]
    return valores


def promedio_en_intervalo(censo: pd.Series, inicios, fines) -> np.ndarray:
    """Promedio del censo durante cada intervalo, con sumas acumuladas del censo horario.

    Se promedian las horas en punto dentro de ``[inicio, fin)``. Si el intervalo no contiene ninguna
    hora en punto (dura menos de una hora), se usa el valor de la hora en punto anterior a su inicio.
    """
    horas = censo.index.to_numpy(dtype="datetime64[ns]")
    acumulado = np.concatenate([[0.0], np.cumsum(censo.to_numpy(dtype=float))])
    ini = pd.to_datetime(pd.Series(inicios)).to_numpy(dtype="datetime64[ns]")
    fin = pd.to_datetime(pd.Series(fines)).to_numpy(dtype="datetime64[ns]")
    a = np.searchsorted(horas, ini, side="left")
    b = np.searchsorted(horas, fin, side="left")
    n = b - a
    with np.errstate(invalid="ignore", divide="ignore"):
        promedio = (acumulado[b] - acumulado[a]) / n
    sin_horas = n <= 0
    promedio[sin_horas] = valor_en_instante(censo, ini[sin_horas])
    promedio[np.isnat(ini) | np.isnat(fin)] = np.nan
    return promedio


# --- Resúmenes -------------------------------------------------------------------------------------
def resumen_ocupacion(serie: pd.Series, capacidades: dict) -> dict:
    """Promedio, mediana, percentil 90 y máximo del censo, y % de horas por encima del 90 % y del
    100 % de cada capacidad actual (2026) de ``capacidades`` (``{etiqueta: camas}``)."""
    fila = {"promedio": serie.mean(), "mediana": serie.median(), "p90": serie.quantile(0.9), "maximo": serie.max()}
    for etiqueta, camas in capacidades.items():
        fila[f"pct_horas_sobre_90_capacidad_actual_2026_{etiqueta}"] = 100 * serie.gt(0.9 * camas).mean()
        fila[f"pct_horas_sobre_100_capacidad_actual_2026_{etiqueta}"] = 100 * serie.gt(camas).mean()
    return fila


def resumen_diario(serie: pd.Series) -> pd.DataFrame:
    """Promedio, percentil 90 y máximo del censo por día."""
    por_dia = serie.groupby(serie.index.normalize())
    return pd.DataFrame({"promedio": por_dia.mean(), "p90": por_dia.quantile(0.9),
                         "maximo": por_dia.max()}).rename_axis("fecha")


def resumen_mensual(serie: pd.Series) -> pd.DataFrame:
    """Promedio, percentil 90, percentil 95 y máximo del censo por mes."""
    por_mes = serie.groupby(serie.index.to_period("M").to_timestamp())
    return pd.DataFrame({"promedio": por_mes.mean(), "p90": por_mes.quantile(0.9), "p95": por_mes.quantile(0.95),
                         "maximo": por_mes.max()}).rename_axis("mes")


def matriz_hora_dia(serie: pd.Series) -> pd.DataFrame:
    """Promedio del censo por hora del día (filas 0–23) y día de la semana (columnas 0 = lunes)."""
    return serie.groupby([serie.index.hour, serie.index.dayofweek]).mean().unstack().rename_axis(
        index="hora", columns="dia_semana")


def distribucion_hora(instantes, excluir=None) -> pd.Series:
    """% de los instantes en cada hora del día (0–23). ``excluir`` (booleano) quita instantes."""
    t = pd.to_datetime(pd.Series(instantes)).reset_index(drop=True)
    if excluir is not None:
        t = t[~pd.Series(excluir).reset_index(drop=True).astype(bool)]
    t = t.dropna()
    conteo = t.dt.hour.value_counts().reindex(range(24), fill_value=0)
    return (100 * conteo / conteo.sum()).rename_axis("hora")


def tramo_horario(instantes) -> pd.Series:
    """Tramo horario de cada instante: 00–06, 06–12, 12–18 o 18–24."""
    hora = pd.to_datetime(pd.Series(instantes)).dt.hour
    return pd.cut(hora, bins=[0, 6, 12, 18, 24], right=False, labels=["00–06", "06–12", "12–18", "18–24"])


def distribucion_dia_semana(instantes, excluir=None) -> pd.Series:
    """% de los instantes en cada día de la semana (0 = lunes). ``excluir`` (booleano) quita instantes."""
    t = pd.to_datetime(pd.Series(instantes)).reset_index(drop=True)
    if excluir is not None:
        t = t[~pd.Series(excluir).reset_index(drop=True).astype(bool)]
    conteo = t.dropna().dt.dayofweek.value_counts().reindex(range(7), fill_value=0)
    return (100 * conteo / conteo.sum()).rename_axis("dia_semana")


def decil(valores, relativo: bool = True) -> pd.Series:
    """Decil (1–10) de cada valor. Con ``relativo``, los valores son percentiles (0–100) y se cortan en
    tramos de 10 puntos; si no, se usan los deciles de los propios valores (``qcut``)."""
    valores = pd.Series(valores, dtype=float)
    if relativo:
        return pd.cut(valores, bins=np.arange(0, 101, 10), labels=range(1, 11), include_lowest=True).astype("Int64")
    return (pd.qcut(valores, 10, labels=False, duplicates="drop") + 1).astype("Int64")


def capacidades_actuales() -> dict:
    """Capacidad actual (2026) por área y grupo de edad: ``{area: {grupo: {etiqueta: camas}}}``.

    Urgencias usa las camas de observación (adultos = hombres + mujeres). El piso total tiene dos
    referencias: solo piso (72) y piso más cuidados especiales (102).
    """
    piso = CAPACIDAD_ACTUAL["piso"]
    observacion = CAPACIDAD_ACTUAL["observacion_urgencias"]
    urgencias = {
        "total": {"observacion": observacion["total"]},
        "adultos": {"observacion": observacion["adultos_hombres"] + observacion["adultos_mujeres"]},
        "pediatria": {"observacion": observacion["pediatria"]},
    }
    return {
        "urgencias_todos": urgencias,
        "urgencias_atencion": urgencias,
        "piso": {
            "total": {"piso": piso["total"], "piso_y_especiales": CAPACIDAD_PISO_CON_ESPECIALES},
            "adultos": {"piso": piso["adultos"]},
            "pediatria": {"piso": piso["pediatria"]},
        },
    }


# --- Episodios y saturación -----------------------------------------------------------------------
def ocupacion_en_episodios(episodios: pd.DataFrame, censo: pd.Series, periodo: str = "Q") -> pd.DataFrame:
    """Ocupación de un área para cada episodio: en la hora de llegada y en promedio durante su
    permanencia en urgencias (``llegada`` → ``llegada + los_h``). Absoluta (pacientes presentes,
    ``abs_*``) y relativa (percentil de la hora dentro de su trimestre, ``rel_*``)."""
    llegada = episodios["llegada"]
    fin = llegada + pd.to_timedelta(episodios["los_h"], unit="h")
    relativo = percentil_en_periodo(censo, periodo)
    return pd.DataFrame({
        "abs_llegada": valor_en_instante(censo, llegada),
        "rel_llegada": valor_en_instante(relativo, llegada),
        "abs_estancia": promedio_en_intervalo(censo, llegada, fin),
        "rel_estancia": promedio_en_intervalo(relativo, llegada, fin),
    }, index=episodios.index)


def tabla_por_decil(episodios: pd.DataFrame, deciles: pd.Series, umbral: float = UMBRAL_OPERATIVO_H) -> pd.DataFrame:
    """Por grupo de paciente y decil de ocupación: n, mediana del LOS y % con LOS mayor a ``umbral``
    con IC de Wilson (en %)."""
    sufijo = f"mas_{umbral}h"
    tabla = tabla_los(episodios.assign(decil=deciles), ["grupo", "decil"], umbrales=[umbral]).reset_index()
    return tabla[["grupo", "decil", "n", "mediana_h", f"n_{sufijo}", f"pct_{sufijo}",
                  f"ic_inf_{sufijo}", f"ic_sup_{sufijo}"]]


def pct_dias_por(dias: pd.Series, por: str = "mes") -> pd.Series:
    """% de días marcados (``True``) por mes (``por="mes"``) o por día de la semana (``"dia_semana"``)."""
    indice = pd.DatetimeIndex(dias.index)
    clave = indice.to_period("M").to_timestamp() if por == "mes" else indice.dayofweek
    return (100 * dias.astype(float).groupby(clave).mean()).rename_axis(por)
