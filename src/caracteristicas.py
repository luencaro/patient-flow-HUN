"""Características por episodio para el análisis de factores (notebook 07).

Principio: cada característica de un episodio se calcula solo con información disponible en el momento
de su llegada (``llegada``). Nada usa datos posteriores a ese instante. Los desenlaces se copian con el
prefijo ``y_`` para que nunca se confundan con predictores.

Las variables de historia y de cola usan todos los episodios del dataset (no solo los de la población de
análisis), porque los episodios previos o simultáneos existen aunque no entren al análisis.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

from . import estilo
from .config import (
    EDAD_PEDIATRIA,
    FECHA_INICIO_ANALISIS,
    GRUPOS_EDAD,
    GRUPOS_TIEMPOS,
    MIN_CELDA,
    ROLES_CARACTERISTICAS,
    VENTANA_LOS_RECIENTE_H,
)
from .ocupacion import GRUPOS_EDAD as GRUPOS_EDAD_OCUPACION
from .ocupacion import censo_en_instantes, percentil_en_censo, tramo_horario

PREFIJO_DESENLACE = "y_"

# Desenlaces del dataset de episodios: {columna de origen: columna en la tabla de características}.
DESENLACES = {
    "los_h": "y_los_h",
    "los_mas_12h": "y_los_mas_12h",
    "reconsulta_72h": "y_reconsulta_72h",
    "reconsulta_72h_sin_censura": "y_reconsulta_72h_sin_censura",
    "reconsulta_7d": "y_reconsulta_7d",
    "reconsulta_7d_sin_censura": "y_reconsulta_7d_sin_censura",
}
# Columnas del dataset de episodios que se copian sin cambios.
COPIADAS = ("episodio_id", "llegada", "grupo", "sexo", "hosp_previa_30d", "nota_consulta_urg", "n_visitas",
            "valido_para_tiempos")
# Columnas que no son predictores ni desenlaces: identificador, fecha de llegada y filtro de tiempos.
NO_PREDICTORES = ("episodio_id", "llegada", "valido_para_tiempos")


def columnas_con_rol(*roles: str, tabla: dict = ROLES_CARACTERISTICAS) -> list[str]:
    """Columnas de ``ROLES_CARACTERISTICAS`` con alguno de los ``roles``, en el orden de la constante."""
    return [columna for columna, rol in tabla.items() if rol in roles]


# --- Calendario y edad ------------------------------------------------------------------------------
def variables_calendario(llegada: pd.Series) -> pd.DataFrame:
    """Hora, día de la semana (0 = lunes), mes, año, fin de semana, festivo de Colombia y franja horaria
    de la llegada. Los festivos se toman del paquete ``holidays``."""
    import holidays  # import local: solo este cálculo lo necesita

    t = pd.to_datetime(llegada)
    anios = t.dt.year.dropna().astype(int)
    festivos = holidays.country_holidays("CO", years=range(anios.min(), anios.max() + 1)) if len(anios) else {}
    return pd.DataFrame({
        "hora": t.dt.hour,
        "dia_semana": t.dt.dayofweek,
        "mes": t.dt.month,
        "anio": t.dt.year,
        "fin_de_semana": t.dt.dayofweek.ge(5),
        "festivo": t.dt.date.isin(list(festivos)),
        "franja": tramo_horario(t),
    }, index=t.index)


def variables_edad(edad: pd.Series) -> pd.DataFrame:
    """Edad a la llegada (año de llegada − ``year_of_birth``, ya calculada en ``edad``), pediatría
    (edad < ``EDAD_PEDIATRIA``) y grupo de edad según ``GRUPOS_EDAD``. Si la edad falta, las tres faltan."""
    edad = pd.to_numeric(edad, errors="coerce")
    limites = list(GRUPOS_EDAD.values())
    cortes = [desde for desde, _ in limites] + [limites[-1][1]]
    return pd.DataFrame({
        "edad_llegada": edad,
        "pediatria": edad.lt(EDAD_PEDIATRIA).astype("boolean").mask(edad.isna()),
        "grupo_edad": pd.cut(edad, bins=cortes, right=False, labels=list(GRUPOS_EDAD)),
    }, index=edad.index)


# --- Historia del paciente --------------------------------------------------------------------------
def episodios_previos(todos: pd.DataFrame, objetivo: pd.DataFrame, dias: int) -> pd.Series:
    """Para cada episodio de ``objetivo``, número de episodios del mismo paciente en ``todos`` con llegada
    en ``[llegada − dias, llegada)``. No cuenta al propio episodio.

    Vectorizado: cada episodio se codifica como ``paciente × escala + segundos desde el origen`` (con una
    escala mayor que todo el rango de fechas más la ventana), y se cuenta con ``np.searchsorted``.
    """
    todos = todos[todos["llegada"].notna()]
    personas = pd.Index(todos["person_id"].unique())
    origen = todos["llegada"].min()
    ventana = int(dias) * 86_400
    escala = int((todos["llegada"].max() - origen).total_seconds()) + ventana + 1

    def clave(df):
        codigo = personas.get_indexer(df["person_id"]).astype(np.int64)
        segundos = np.floor((df["llegada"] - origen).dt.total_seconds().to_numpy()).astype(np.int64)
        return codigo * escala + segundos

    referencia = np.sort(clave(todos))
    validos = objetivo["llegada"].notna() & objetivo["person_id"].isin(personas)
    conteo = pd.Series(np.nan, index=objetivo.index)
    t = clave(objetivo[validos])
    conteo[validos] = np.searchsorted(referencia, t, side="left") - np.searchsorted(referencia, t - ventana,
                                                                                    side="left")
    return conteo.astype("Int64")


def historia_completa(llegada: pd.Series, dias: int, inicio=FECHA_INICIO_ANALISIS) -> pd.Series:
    """``True`` si la ventana de ``dias`` días antes de la llegada cae completa dentro de los datos
    (llegada ≥ inicio de los datos + ``dias``); ``False`` si la ventana queda recortada."""
    return pd.to_datetime(llegada).ge(pd.Timestamp(inicio) + pd.Timedelta(days=dias))


# --- Ocupación a la llegada -------------------------------------------------------------------------
def censo_a_la_llegada(intervalos: pd.DataFrame, referencia: pd.Series,
                       llegada: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Pacientes presentes en el instante exacto de la llegada (``inicio < t`` y ``fin > t``, con
    ``censo_en_instantes`` sobre ``intervalos``, igual que urgencias) y su percentil frente a las horas de su
    trimestre en el censo horario ``referencia`` (``percentil_en_censo``; la referencia puede excluir el
    periodo de calentamiento)."""
    valores = censo_en_instantes(intervalos["inicio"], intervalos["fin"], llegada)
    return valores, percentil_en_censo(referencia, valores, llegada)


def censo_de_su_grupo(intervalos: pd.DataFrame, referencias: pd.DataFrame, llegada: pd.Series,
                      grupos: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Como ``censo_a_la_llegada``, pero cada episodio se compara con los intervalos y el censo de su grupo
    de edad (``grupo_edad`` de los intervalos: adultos o pediatría). Sin grupo de edad, NaN."""
    absoluto = np.full(len(llegada), np.nan)
    percentil = np.full(len(llegada), np.nan)
    for grupo in GRUPOS_EDAD_OCUPACION:
        filas = grupos.eq(grupo).to_numpy()
        if filas.any():
            absoluto[filas], percentil[filas] = censo_a_la_llegada(
                intervalos[intervalos["grupo_edad"].eq(grupo)], referencias[grupo], llegada[filas])
    return absoluto, percentil


# --- LOS reciente -----------------------------------------------------------------------------------
def los_reciente(todos: pd.DataFrame, instantes, ventana_h: float = VENTANA_LOS_RECIENTE_H) -> pd.DataFrame:
    """LOS de los episodios que SALIERON de urgencias en ``[t − ventana_h, t)`` para cada instante ``t``.

    Se usan los episodios de atención en urgencias y hospitalizados válidos para tiempos con LOS; su salida
    es ``llegada + los_h`` (inicio del piso o fin de urgencias, como en el notebook 06). No se usa el LOS de
    quienes llegaron en la ventana, porque muchos siguen en urgencias. Devuelve el promedio y la mediana
    del LOS (horas) y el número de salidas; sin salidas, el promedio y la mediana quedan en NaN.
    """
    e = todos[todos["valido_para_tiempos"].astype(bool) & todos["grupo"].isin(list(GRUPOS_TIEMPOS))
              & todos["los_h"].notna() & todos["llegada"].notna()]
    salida = (e["llegada"] + pd.to_timedelta(e["los_h"], unit="h")).to_numpy(dtype="datetime64[ns]")
    orden = np.argsort(salida, kind="mergesort")
    salida = salida[orden]
    los = e["los_h"].to_numpy(dtype=float)[orden]
    acumulado = np.concatenate([[0.0], np.cumsum(los)])

    indice = pd.Series(instantes).index if isinstance(instantes, pd.Series) else None
    t = pd.to_datetime(pd.Series(instantes)).to_numpy(dtype="datetime64[ns]")
    desde = np.searchsorted(salida, t - np.timedelta64(int(ventana_h * 3600), "s"), side="left")
    hasta = np.searchsorted(salida, t, side="left")
    n = np.where(np.isnat(t), 0, hasta - desde)
    with np.errstate(invalid="ignore", divide="ignore"):
        promedio = np.where(n > 0, (acumulado[hasta] - acumulado[desde]) / n, np.nan)
    mediana = np.full(len(t), np.nan)
    for i in np.flatnonzero(n > 0):  # ventanas de tamaño variable: la mediana se calcula por episodio
        mediana[i] = np.median(los[desde[i]:hasta[i]])
    return pd.DataFrame({"los_reciente_promedio_h": promedio, "los_reciente_mediana_h": mediana,
                         "n_salidas_recientes": n}, index=indice)


# --- Revisión de las características ----------------------------------------------------------------
def tipo_variable(serie: pd.Series) -> str:
    """``booleana``, ``numerica`` o ``categorica``."""
    if pd.api.types.is_bool_dtype(serie):
        return "booleana"
    if pd.api.types.is_numeric_dtype(serie):
        return "numerica"
    return "categorica"


def resumen_variables(df: pd.DataFrame, columnas) -> pd.DataFrame:
    """Por variable: tipo, % faltante, mínimo, mediana y máximo (numéricas) y número de categorías
    (booleanas y categóricas)."""
    filas = []
    for columna in columnas:
        s = df[columna]
        tipo = tipo_variable(s)
        fila = {"variable": columna, "tipo": tipo, "pct_faltante": 100 * s.isna().mean(),
                "minimo": np.nan, "mediana": np.nan, "maximo": np.nan, "categorias": np.nan}
        if tipo == "numerica":
            valores = s.astype(float)
            fila.update(minimo=valores.min(), mediana=valores.median(), maximo=valores.max())
        else:
            fila["categorias"] = s.dropna().nunique()
        filas.append(fila)
    return pd.DataFrame(filas).set_index("variable")


def _barras_ocultas(ax, x, conteos, color, ancho: float = 0.8) -> None:
    """Barras con los conteos menores a ``MIN_CELDA`` ocultos (sin barra)."""
    conteos = np.asarray(conteos, dtype=float)
    visibles = np.where((conteos > 0) & (conteos < MIN_CELDA), np.nan, conteos)
    ax.bar(x, visibles, color=color, width=ancho)


def graficar_distribuciones(df: pd.DataFrame, columnas, color: str = estilo.VERDE, columnas_grilla: int = 3):
    """Histograma (numéricas con muchos valores) o barras (discretas, booleanas y categóricas) de cada
    variable, en una grilla. Los intervalos o categorías con menos de ``MIN_CELDA`` episodios no se dibujan.
    Devuelve la figura."""
    columnas = list(columnas)
    filas = int(np.ceil(len(columnas) / columnas_grilla))
    fig, ejes = plt.subplots(filas, columnas_grilla, figsize=(14, 3.6 * filas), squeeze=False)
    fig.get_layout_engine().set(hspace=0.12, wspace=0.08)  # aire entre paneles para títulos y ejes
    for ax, columna in zip(ejes.flat, columnas):
        s = df[columna].dropna()
        tipo = tipo_variable(s)
        if tipo == "numerica" and s.nunique() > 30:
            conteos, bordes = np.histogram(s.astype(float), bins=30)
            _barras_ocultas(ax, (bordes[:-1] + bordes[1:]) / 2, conteos, color, ancho=0.95 * (bordes[1] - bordes[0]))
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        elif tipo == "numerica":
            conteos = s.value_counts().sort_index()
            _barras_ocultas(ax, conteos.index.astype(float), conteos.to_numpy(), color)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        else:
            conteos = s.astype(str).value_counts().sort_index()
            posiciones = np.arange(len(conteos))
            _barras_ocultas(ax, posiciones, conteos.to_numpy(), color)
            rotar = len(conteos) > 3 or conteos.index.str.len().max() > 6
            ax.set_xticks(posiciones, conteos.index, rotation=45 if rotar else 0, ha="right" if rotar else "center",
                          rotation_mode="anchor")
        ax.tick_params(axis="x", labelsize=estilo.TAMANO_MINIMO)
        ax.set_title(columna, loc="left", fontsize=estilo.TAMANO_EJES)
        ax.yaxis.set_major_formatter(FuncFormatter(estilo.tick_entero))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    for ax in list(ejes.flat)[len(columnas):]:
        ax.set_visible(False)
    return fig


def heatmap_correlacion(ax, matriz: pd.DataFrame, familia: str = "general"):
    """Matriz de correlación (−1 a 1) con la rampa de la familia y el valor en cada celda."""
    valores = matriz.to_numpy(dtype=float)
    malla = ax.pcolormesh(valores, cmap=estilo.colormap(familia), vmin=-1, vmax=1, edgecolors=estilo.FONDO_FIGURA,
                          linewidth=1)
    n = len(matriz)
    ax.set_xticks(np.arange(n) + 0.5, matriz.columns, rotation=45, ha="right", rotation_mode="anchor",
                  fontsize=estilo.TAMANO_MINIMO)
    ax.set_yticks(np.arange(n) + 0.5, matriz.index, fontsize=estilo.TAMANO_MINIMO)
    ax.set_aspect("equal")
    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)
    ax.grid(False)
    for i in range(n):
        for j in range(n):
            if not np.isnan(valores[i, j]):
                ax.text(j + 0.5, i + 0.5, estilo.fmt_decimal(valores[i, j], 2), ha="center", va="center",
                        fontsize=estilo.TAMANO_MINIMO,
                        color=estilo.FONDO_FIGURA if valores[i, j] > 0.4 else estilo.TEXTO)
    barra = ax.figure.colorbar(malla, ax=ax, shrink=0.8, format=FuncFormatter(estilo.tick_numero))
    barra.set_label("Correlación de Spearman")
    barra.outline.set_visible(False)
    return malla


def comparar_por_marca(df: pd.DataFrame, columnas, marca: str,
                       nombres: dict | None = None) -> pd.DataFrame:
    """Compara cada variable numérica o booleana entre los episodios con ``marca`` True y False: n con dato
    y mediana (numéricas) o % verdadero (booleanas) en cada grupo. Las categóricas se omiten."""
    nombres = nombres or {True: "completa", False: "recortada"}
    filas = []
    for columna in columnas:
        s = df[columna]
        tipo = tipo_variable(s)
        if tipo == "categorica" or columna == marca:
            continue
        fila = {"variable": columna, "estadistico": "% verdadero" if tipo == "booleana" else "mediana"}
        for valor, nombre in nombres.items():
            parte = s[df[marca].eq(valor)].dropna()
            fila[f"n_{nombre}"] = len(parte)
            fila[f"valor_{nombre}"] = (100 * parte.astype(float).mean() if tipo == "booleana"
                                       else parte.astype(float).median())
        filas.append(fila)
    return pd.DataFrame(filas).set_index("variable")
