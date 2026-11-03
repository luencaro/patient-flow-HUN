"""Gráficos del EDA con el sistema visual del proyecto (tokens en ``src/estilo.py``).

Cuatro familias de color con significado fijo (``estilo.FAMILIAS``): azul = urgencias,
ciruela = hospitalización, ocre = ambulatorio y verde azulado = general (base completa o
variables sin rol). El gris queda para contexto o ausencia de dato. El texto nunca va del
color de la serie. El semáforo de ``estilo.SEMAFORO`` no se usa en el EDA.

``guardar_figura`` aplica de forma automática el formato de números colombiano a
los ejes, el formato de los ejes de fechas, la separación de etiquetas directas y
la revisión de textos superpuestos.
"""

import textwrap
import warnings

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.text import Annotation, Text
from matplotlib.ticker import FuncFormatter, LogFormatter, NullFormatter, ScalarFormatter

from . import estilo
from .estilo import fmt_entero, fmt_mes, fmt_numero, fmt_pct  # noqa: F401 (reexportados)

# Las etiquetas de grupo viven en estilo/config y se reexportan aquí para los notebooks.
from .config import (  # noqa: F401
    ETIQUETAS_CORTAS_GRUPO,
    ETIQUETAS_GRUPO,
    FIGURAS,
    GRUPOS,
    MIN_CELDA,
    UMBRAL_OPERATIVO_H,
)

# --- Neutros (nombres de la versión anterior, ahora leídos de estilo) ----------------------
FONDO = estilo.FONDO_FIGURA
PANEL = estilo.FONDO_PAGINA
TEXTO_PRIMARIO = estilo.TEXTO
TEXTO_SECUNDARIO = estilo.TEXTO_SECUNDARIO
EJES = estilo.EJES
CUADRICULA = estilo.BORDE

# --- Grupos ------------------------------------------------------------------------------
COLOR_BASE = estilo.AZUL  # atención en urgencias
COLOR_HOSP = estilo.CIRUELA  # hospitalizado
COLOR_CONTEXTO = estilo.GRIS_CONTEXTO  # contacto breve
COLORES_GRUPO = dict(estilo.COLOR_ROL)

# Series técnicas (calidad, tipos de visita): grises de oscuro a claro, con marcador distinto.
GRISES_TECNICOS = [estilo.GRISES[0], estilo.GRISES[1], estilo.GRISES[2], estilo.GRISES[0]]
MARCADORES = ["o", "s", "^", "D"]

ANCHO_LINEA = estilo.GROSOR_ROL[estilo.ROL_ATENCION]
ANCHO_LINEA_HOSP = estilo.GROSOR_ROL[estilo.ROL_HOSPITALIZADO]
DIAS_SEMANA = list(estilo.DIAS_SEMANA)

# Relleno de "sin dato" / faltante / concepto 0: rayado gris claro (nunca rojo).
ESTILO_SIN_DATO = {"facecolor": FONDO, "edgecolor": estilo.COLOR_SIN_DATO, "hatch": "///", "linewidth": 0.8}

ALTO_POR_BARRA_IN = 0.35
GID_ETIQUETA_FINAL = "etiqueta_final"
GID_TITULO = "titulo_hallazgo"
GID_SUBTITULO = "subtitulo_hallazgo"


def aplicar_estilo() -> None:
    """Configura matplotlib con los tokens de ``estilo``: fondo blanco, sin bordes superior
    ni derecho, cuadrícula horizontal, una sola fuente, tamaños mínimos de 9 pt y
    ``constrained_layout`` en todas las figuras (no usar ``tight_layout``)."""
    mpl.rcParams.update(
        {
            "figure.figsize": (10, 5.5),
            "figure.dpi": 100,
            "figure.facecolor": FONDO,
            "figure.constrained_layout.use": True,
            "figure.titlesize": estilo.TAMANO_TITULO,
            "figure.titleweight": "bold",
            "axes.facecolor": FONDO,
            "font.family": "sans-serif",
            "font.sans-serif": estilo.FUENTES,
            "font.size": estilo.TAMANO_EJES,
            "axes.titlesize": estilo.TAMANO_SUBTITULO + 1,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlecolor": TEXTO_PRIMARIO,
            "axes.labelsize": estilo.TAMANO_EJES,
            "axes.labelcolor": TEXTO_SECUNDARIO,
            "axes.edgecolor": EJES,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "axes.prop_cycle": mpl.cycler(color=list(estilo.FAMILIAS["general"]["barras"][1:])),
            "axes.formatter.limits": (-99, 99),  # nunca notación científica
            "axes.formatter.useoffset": False,
            "grid.color": CUADRICULA,
            "grid.linewidth": 0.8,
            "xtick.color": EJES,
            "ytick.color": EJES,
            "xtick.labelcolor": TEXTO_SECUNDARIO,
            "ytick.labelcolor": TEXTO_SECUNDARIO,
            "xtick.labelsize": estilo.TAMANO_EJES,
            "ytick.labelsize": estilo.TAMANO_EJES,
            "legend.fontsize": estilo.TAMANO_EJES,
            "legend.frameon": False,
            "legend.labelcolor": TEXTO_PRIMARIO,
            "lines.linewidth": ANCHO_LINEA,
            "lines.markersize": 5,
            "patch.edgecolor": FONDO,
            "hatch.color": estilo.COLOR_SIN_DATO,
            "text.color": TEXTO_PRIMARIO,
            "savefig.bbox": "tight",
            "savefig.facecolor": FONDO,
            "svg.fonttype": "none",
        }
    )


# --- Formato de números en tablas ---------------------------------------------------------
_COLUMNAS_SIN_MILES = ("concepto", "anio", "hora", "dia", "posicion", "rango", "edad", "banda", "umbral")


def formatear_tabla(tabla: pd.DataFrame) -> pd.DataFrame:
    """Copia de la tabla con los números como texto en formato colombiano (solo para mostrar).

    Enteros sin decimales; columnas ``pct_*`` e ``ic_*`` con un decimal; el resto de
    decimales con dos. Las columnas de códigos o años (``concepto``, ``anio``, ``hora``...)
    no llevan separador de miles. No se usa para exportar.
    """
    if not isinstance(tabla, pd.DataFrame):
        return tabla
    salida = tabla.copy()
    for columna in salida.columns:
        nombre = str(columna)
        if nombre.startswith(_COLUMNAS_SIN_MILES):
            continue
        decimales = 1 if nombre.startswith(("pct", "ic_")) else 2

        def _formato(v, decimales=decimales):
            if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating)):
                return v
            if pd.isna(v):
                return v
            return fmt_entero(v) if float(v).is_integer() and not nombre.startswith(("pct", "ic_")) else estilo.fmt_decimal(v, decimales)

        salida[columna] = salida[columna].map(_formato)
    return salida


def activar_formato_tablas() -> None:
    """Hace que Jupyter muestre todas las tablas con formato colombiano (miles con punto,
    decimales con coma). Solo cambia la visualización; los datos no se modifican."""
    try:
        from IPython import get_ipython
    except ImportError:
        return
    ip = get_ipython()
    if ip is None:
        return
    html = ip.display_formatter.formatters["text/html"]
    html.for_type(pd.DataFrame, lambda tabla: formatear_tabla(tabla).to_html())


# --- Textos de la figura ------------------------------------------------------------------
def titulo_hallazgo(objeto, titulo: str, subtitulo: str = "") -> None:
    """Título en negrita (el hallazgo) y subtítulo en gris (qué se mide).

    ``objeto`` puede ser una figura (título general) o un eje.
    """
    if isinstance(objeto, plt.Figure):
        texto = objeto.suptitle(titulo + ("\n" if subtitulo else ""), x=0.01, ha="left",
                                fontsize=estilo.TAMANO_TITULO, fontweight="bold", color=TEXTO_PRIMARIO)
        anfitrion = objeto
    else:
        texto = objeto.set_title(titulo + ("\n" if subtitulo else ""), loc="left",
                                 fontsize=estilo.TAMANO_TITULO, fontweight="bold", color=TEXTO_PRIMARIO)
        anfitrion = objeto
    texto.set_gid(GID_TITULO)
    if subtitulo:
        # El subtítulo ocupa la línea en blanco que se reservó al final del título.
        sub = Annotation(subtitulo, xy=(0, 0), xycoords=texto, xytext=(0, 2), textcoords="offset points",
                         ha="left", va="bottom", fontsize=estilo.TAMANO_SUBTITULO, color=TEXTO_SECUNDARIO,
                         annotation_clip=False)
        sub.set_clip_on(False)
        anfitrion.add_artist(sub)
        sub.set_gid(GID_SUBTITULO)
        sub.set_in_layout(False)


def recortar_etiqueta(texto, max_caracteres: int = 45) -> str:
    """Recorta una etiqueta larga y agrega «…» al final."""
    texto = str(texto)
    return texto if len(texto) <= max_caracteres else texto[: max_caracteres - 1].rstrip() + "…"


def envolver_etiqueta(texto, ancho: int = 40, lineas: int = 2) -> str:
    """Parte una etiqueta en ``lineas`` líneas de ``ancho`` caracteres como máximo, con «…» si se corta."""
    partes = textwrap.wrap(str(texto), ancho) or [""]
    if len(partes) > lineas:
        partes = partes[:lineas]
        partes[-1] = recortar_etiqueta(partes[-1] + " …", ancho)
    return "\n".join(partes)


def leyenda_fuera(ax: plt.Axes, posicion: str = "derecha", **kwargs):
    """Leyenda fuera del área de datos (a la derecha o debajo)."""
    if posicion == "debajo":
        opciones = {"loc": "upper left", "bbox_to_anchor": (0, -0.15), "ncol": 3}
    else:
        opciones = {"loc": "upper left", "bbox_to_anchor": (1.01, 1)}
    opciones.update(kwargs)
    return ax.legend(**opciones)


# --- Líneas de referencia y etiquetas ---------------------------------------------------------
def linea_umbral(ax: plt.Axes, horas: float = UMBRAL_OPERATIVO_H, etiqueta: str | None = None,
                 eje: str = "x", destacada: bool = True, fila: int = 0) -> None:
    """Línea punteada gris con etiqueta (por defecto, «Umbral HUN 12 h»).

    ``fila`` baja la etiqueta una línea por cada unidad, para que no choque con otras.
    """
    if etiqueta is None:
        etiqueta = f"Umbral HUN {fmt_numero(horas)} h"
    color = TEXTO_SECUNDARIO if destacada else EJES
    estilo_linea, ancho = (":", 1.6) if destacada else ("--", 1.0)
    if eje == "x":
        ax.axvline(horas, color=color, linestyle=estilo_linea, linewidth=ancho, zorder=1)
        ax.annotate(etiqueta, xy=(horas, 1), xycoords=("data", "axes fraction"), xytext=(3, -14 - 14 * fila),
                    textcoords="offset points", color=TEXTO_SECUNDARIO, fontsize=estilo.TAMANO_NOTA)
    else:
        ax.axhline(horas, color=color, linestyle=estilo_linea, linewidth=ancho, zorder=1)
        ax.annotate(etiqueta, xy=(1, horas), xycoords=("axes fraction", "data"), xytext=(-3, 3),
                    textcoords="offset points", color=TEXTO_SECUNDARIO, fontsize=estilo.TAMANO_NOTA, ha="right")


def marcar_umbrales(ax: plt.Axes, umbrales, eje: str = "x") -> None:
    """Varias líneas de referencia: el umbral operativo (12 h) destacado, los demás discretos."""
    for i, umbral in enumerate(umbrales):
        destacada = umbral == UMBRAL_OPERATIVO_H
        etiqueta = None if destacada else f"{fmt_numero(umbral)} h"
        linea_umbral(ax, umbral, etiqueta, eje=eje, destacada=destacada, fila=i % 2)


def etiquetar_final(ax: plt.Axes, x, y, texto: str, color: str = TEXTO_PRIMARIO, negrita: bool = False) -> None:
    """Etiqueta directa al final de una línea (último punto no nulo).

    El texto va en color de texto; ``color`` solo se usa para un punto al final de la
    serie. Si varias etiquetas quedan juntas, ``guardar_figura`` las separa.
    """
    x = list(x)  # conserva Timestamp en ejes de fechas
    y = np.asarray(y, dtype=float)
    validos = np.flatnonzero(~np.isnan(y))
    if validos.size == 0:
        return
    i = validos[-1]
    ax.plot([x[i]], [y[i]], "o", color=color, markersize=4, zorder=3)
    anotacion = ax.annotate(texto, xy=(x[i], y[i]), xytext=(6, 0), textcoords="offset points", va="center",
                            color=TEXTO_PRIMARIO, fontsize=estilo.TAMANO_EJES,
                            fontweight="bold" if negrita else "normal", annotation_clip=False)
    anotacion.set_gid(GID_ETIQUETA_FINAL)


def etiquetas_directas(ax: plt.Axes, x, series: dict, negrita=()) -> None:
    """Etiqueta al final de cada serie, en lugar de leyenda (para 4 series o menos).

    ``series`` es ``{etiqueta: (valores, color)}``; ``negrita`` lista las etiquetas del foco.
    """
    for texto, (valores, color) in series.items():
        etiquetar_final(ax, x, valores, texto, color=color, negrita=texto in negrita)


def rotular_barras(ax: plt.Axes, barras, valores, formato=fmt_numero, alturas=None, horizontal: bool = False) -> None:
    """Escribe el valor de cada barra (formato colombiano). ``formato`` es una función o una
    plantilla de ``str.format`` (se convierte al formato colombiano)."""
    valores = np.asarray(valores, dtype=float)
    alturas = valores if alturas is None else np.asarray(alturas, dtype=float)
    if isinstance(formato, str):
        plantilla = formato

        def formato(v):
            return estilo._colombiano(plantilla.format(v))

    for barra, valor, altura in zip(barras, valores, alturas):
        if np.isnan(valor):
            continue
        if horizontal:
            ax.annotate(formato(valor), xy=(altura, barra.get_y() + barra.get_height() / 2), xytext=(3, 0),
                        textcoords="offset points", ha="left", va="center", color=TEXTO_PRIMARIO,
                        fontsize=estilo.TAMANO_MINIMO)
        else:
            ax.annotate(formato(valor), xy=(barra.get_x() + barra.get_width() / 2, altura), xytext=(0, 3),
                        textcoords="offset points", ha="center", va="bottom", color=TEXTO_PRIMARIO,
                        fontsize=estilo.TAMANO_MINIMO)


def marcar_sin_dato(artistas) -> None:
    """Aplica el relleno rayado gris claro de «Sin dato» a barras o parches."""
    for artista in artistas:
        artista.set_facecolor(ESTILO_SIN_DATO["facecolor"])
        artista.set_edgecolor(ESTILO_SIN_DATO["edgecolor"])
        artista.set_hatch(ESTILO_SIN_DATO["hatch"])
        artista.set_linewidth(ESTILO_SIN_DATO["linewidth"])


# --- Barras top-N ---------------------------------------------------------------------------
def figura_top(n_barras: int, ancho: float = 11, extra_in: float = 1.8):
    """Figura para barras horizontales con alto proporcional al número de barras."""
    return plt.subplots(figsize=(ancho, ALTO_POR_BARRA_IN * max(n_barras, 2) + extra_in))


def barras_top_n(ax: plt.Axes, serie: pd.Series, color=estilo.COLOR_TOP_TABLA, n: int = 15, otros: bool = True,
                 total: float | None = None, formato=fmt_entero, sin_dato=(), ancho_etiqueta: int = 40,
                 familia: str | None = None) -> None:
    """Barras horizontales ordenadas de mayor a menor, con el valor escrito.

    - Si ``serie`` tiene más de ``n`` categorías y ``otros`` es ``True``, el resto se
      agrupa en «Otros (k)», en gris claro y al final. Si se da ``total`` (por ejemplo,
      cuando la serie es un top de SQL), «Otros» es la diferencia con el total.
    - Las etiquetas largas se parten en dos líneas de ~40 caracteres.
    - Los valores ``NaN`` (suprimidos) quedan sin barra y con «<10».
    - Las categorías de ``sin_dato`` llevan relleno rayado gris claro.
    - ``color`` puede ser un color o una lista de colores (uno por barra, en el orden recibido).
    - Con ``familia``, el color sigue el puesto (``estilo.colores_por_rango``) y ``color`` se ignora.
    """
    serie = serie.astype(float)
    # Los colores se asocian a las categorías en el orden recibido, antes de ordenar.
    lista = list(color) if isinstance(color, (list, tuple, np.ndarray, pd.Series)) else [color] * len(serie)
    colores = dict(zip(serie.index, lista)) if len(lista) == len(serie) else {k: lista[0] for k in serie.index}
    serie = serie.sort_values(ascending=False, na_position="last")
    mostrar = serie.iloc[:n]
    resto = serie.iloc[n:]
    if familia is not None:
        colores = dict(zip(mostrar.index, estilo.colores_por_rango(len(mostrar), familia)))
    if otros:
        if total is not None and total > mostrar.sum(skipna=True):
            valor_otros = total - mostrar.sum(skipna=True)
            etiqueta_otros = f"Otros ({fmt_entero(len(resto))})" if len(resto) else "Otros"
            mostrar = pd.concat([mostrar, pd.Series({etiqueta_otros: valor_otros})])
        elif len(resto):
            mostrar = pd.concat([mostrar, pd.Series({f"Otros ({fmt_entero(len(resto))})": resto.sum(skipna=True)})])
    y = np.arange(len(mostrar))[::-1]
    for yi, (categoria, valor) in zip(y, mostrar.items()):
        es_otros = str(categoria).startswith("Otros") and categoria not in colores
        c = estilo.COLOR_OTROS if es_otros else colores.get(categoria, estilo.COLOR_TOP_TABLA)
        barra = ax.barh(yi, 0 if np.isnan(valor) else valor, height=0.7, color=c)
        if categoria in sin_dato:
            marcar_sin_dato(barra)
    maximo = np.nanmax(mostrar.to_numpy()) if mostrar.notna().any() else 1.0
    if isinstance(formato, str):
        plantilla = formato

        def formato(v):
            return estilo._colombiano(plantilla.format(v))

    for yi, valor in zip(y, mostrar):
        texto = f"<{MIN_CELDA}" if np.isnan(valor) else formato(valor)
        ax.annotate(texto, xy=(0 if np.isnan(valor) else valor, yi), xytext=(3, 0), textcoords="offset points",
                    va="center", ha="left", color=TEXTO_PRIMARIO, fontsize=estilo.TAMANO_MINIMO)
    ax.set_yticks(y, [envolver_etiqueta(e, ancho_etiqueta) for e in mostrar.index])
    ax.set_xlim(0, maximo * 1.15)
    ax.tick_params(axis="y", labelsize=estilo.TAMANO_MINIMO)
    ax.grid(False)
    ax.grid(axis="x")


def barras_faltantes(ax: plt.Axes, faltantes: pd.DataFrame, ancho_etiqueta: int = 40) -> None:
    """Barras horizontales de % faltante por columna, ordenadas de mayor a menor (incluidas las de 0 %).

    ``faltantes`` tiene una fila por columna (índice) con ``pct_nulos`` y ``pct_sin_informacion``
    (concepto 0 o columna constante). Cada barra se apila en dos tramos: nulo en ``#006c60`` y
    sin información en ``#c3c2b7``; el total se escribe al final de la barra.
    """
    color_nulo = estilo.FAMILIAS["general"]["oscuro"]  # #006c60
    color_sin_info = estilo.GRISES[2]  # #c3c2b7
    datos = faltantes[["pct_nulos", "pct_sin_informacion"]].astype(float).fillna(0)
    datos = datos.assign(total=datos.sum(axis=1)).sort_values("total", ascending=False)
    y = np.arange(len(datos))[::-1]
    ax.barh(y, datos["pct_nulos"], height=0.7, color=color_nulo, label="Nulo")
    ax.barh(y, datos["pct_sin_informacion"], left=datos["pct_nulos"], height=0.7, color=color_sin_info,
            label="Sin información (concepto 0 o columna constante)")
    for yi, total in zip(y, datos["total"]):
        ax.annotate(fmt_pct(total), xy=(total, yi), xytext=(3, 0), textcoords="offset points", va="center",
                    ha="left", color=TEXTO_PRIMARIO, fontsize=estilo.TAMANO_MINIMO)
    ax.set_yticks(y, [envolver_etiqueta(c, ancho_etiqueta) for c in datos.index])
    ax.set_xlim(0, 115)  # deja espacio para el total escrito al final de la barra
    ax.set_xticks(range(0, 101, 20))
    ax.xaxis.set_major_formatter(FuncFormatter(estilo.tick_pct))
    ax.set_xlabel("% de filas de la tabla")
    ax.tick_params(axis="y", labelsize=estilo.TAMANO_MINIMO)
    ax.grid(False)
    ax.grid(axis="x")
    leyenda_fuera(ax, "debajo", ncol=2)


def ancho_linea(grupo: str | None = None) -> float:
    """3 px para hospitalizado (foco) y 2 px para el resto."""
    return estilo.GROSOR_ROL.get(grupo, ANCHO_LINEA)


# --- Cajas (boxplots) desde estadísticos agregados ---------------------------------------------
def estilo_caja(familia: str, borde: str | None = None, anillo: bool = False) -> tuple[str, str]:
    """(relleno, borde) de una caja: relleno con ``rampa[2]`` de la familia y borde y mediana en
    su tono ``oscuro`` (o en ``borde``). Con ``anillo``, la caja va sin relleno."""
    f = estilo.familia(familia)
    return (FONDO if anillo else f["rampa"][2], borde or f["oscuro"])


def dibujar_cajas(ax: plt.Axes, estadisticos: list, etiquetas: list, familias, horizontal: bool = True,
                  escala_log: bool = False, bordes=None, anillos=None) -> None:
    """Cajas calculadas desde agregados (ver ``estadistica.estadisticos_caja_*``).

    ``familias`` es una familia o una lista (una por caja). Cada caja va rellena con un tono
    claro de su familia, con borde y mediana en el tono oscuro (o en ``bordes``), y bigotes en
    gris. ``anillos`` (lista de bool) deja cajas sin relleno. No dibuja atípicos individuales:
    marca el mínimo y el máximo con un rombo y escribe el número de atípicos.
    """
    k = len(estadisticos)
    familias = list(familias) if isinstance(familias, (list, tuple)) else [familias] * k
    bordes = list(bordes) if bordes is not None else [None] * k
    anillos = list(anillos) if anillos is not None else [False] * k
    estilos = [estilo_caja(f, b, a) for f, b, a in zip(familias, bordes, anillos)]
    cajas = [
        {"med": e["med"], "q1": e["q1"], "q3": e["q3"], "whislo": e["whislo"], "whishi": e["whishi"],
         "fliers": [], "label": etiqueta}
        for e, etiqueta in zip(estadisticos, etiquetas)
    ]
    gris = estilo.GRISES[0]
    opciones = dict(showfliers=False, patch_artist=True, widths=0.55, medianprops={"linewidth": 2},
                    whiskerprops={"color": gris}, capprops={"color": gris})
    try:
        artistas = ax.bxp(cajas, orientation="horizontal" if horizontal else "vertical", **opciones)
    except TypeError:  # matplotlib < 3.10
        artistas = ax.bxp(cajas, vert=not horizontal, **opciones)
    for caja, mediana, (relleno, borde) in zip(artistas["boxes"], artistas["medians"], estilos):
        caja.set_facecolor(relleno)
        caja.set_edgecolor(borde)
        caja.set_linewidth(1.5)
        mediana.set_color(borde)
    if escala_log:
        (ax.set_xscale if horizontal else ax.set_yscale)("log")
    for posicion, e in enumerate(estadisticos, start=1):
        extremos = [v for v in (e.get("minimo"), e.get("maximo")) if v is not None and not np.isnan(v)]
        if escala_log:
            extremos = [v for v in extremos if v > 0]
        if horizontal:
            ax.plot(extremos, [posicion] * len(extremos), "D", color=gris, markersize=4, zorder=3)
        else:
            ax.plot([posicion] * len(extremos), extremos, "D", color=gris, markersize=4, zorder=3)
        n_atipicos = e.get("n_atipicos")
        if n_atipicos is not None and not np.isnan(n_atipicos):
            texto = f"{fmt_entero(n_atipicos)} atípicos" if n_atipicos >= MIN_CELDA or n_atipicos == 0 else f"<{MIN_CELDA} atípicos"
            if horizontal:
                ax.annotate(texto, xy=(1, posicion), xycoords=("axes fraction", "data"), xytext=(4, 0),
                            textcoords="offset points", va="center", ha="left", fontsize=estilo.TAMANO_MINIMO,
                            color=TEXTO_SECUNDARIO, annotation_clip=False)
            else:
                ax.annotate(texto, xy=(posicion, 1), xycoords=("data", "axes fraction"), xytext=(0, 4),
                            textcoords="offset points", va="bottom", ha="center", fontsize=estilo.TAMANO_MINIMO,
                            color=TEXTO_SECUNDARIO, annotation_clip=False)
    if horizontal:
        ax.grid(False)
        ax.grid(axis="x")


# --- Heatmaps ------------------------------------------------------------------------------
def heatmap_hora_dia(ax: plt.Axes, matriz, titulo: str, etiqueta_barra: str, familia: str = "urgencias",
                     formato=estilo.tick_numero):
    """Mapa de calor hora (filas 0–23) × día de la semana (columnas 0–6) en 7 pasos de la
    rampa de la familia del dato (urgencias, hospitalizacion o general). Las celdas
    suprimidas quedan en blanco."""
    pasos = list(estilo.familia(familia)["rampa"])
    mapa = ListedColormap(pasos, name=f"{familia}_7_pasos")
    mapa.set_bad(FONDO)
    matriz = matriz.reindex(index=range(24), columns=range(7))
    datos = np.ma.masked_invalid(matriz.to_numpy(dtype=float))
    minimo, maximo = (datos.min(), datos.max()) if datos.count() else (0.0, 1.0)
    if minimo == maximo:
        maximo = minimo + 1
    norma = BoundaryNorm(np.linspace(minimo, maximo, len(pasos) + 1), mapa.N)
    malla = ax.pcolormesh(np.arange(8) - 0.5, np.arange(25) - 0.5, datos, cmap=mapa, norm=norma,
                          edgecolors=FONDO, linewidth=1.5)
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(23.5, -0.5)
    ax.set_xticks(range(7), DIAS_SEMANA)
    ax.set_yticks(range(0, 24, 2), [f"{h:02d}:00" for h in range(0, 24, 2)])
    ax.set_xlabel("Día de llegada")
    ax.set_ylabel("Hora de llegada")
    ax.set_title(titulo)
    ax.grid(False)
    for borde in ax.spines.values():
        borde.set_visible(False)
    barra = ax.figure.colorbar(malla, ax=ax, shrink=0.85, format=FuncFormatter(formato))
    barra.set_label(etiqueta_barra)
    barra.outline.set_visible(False)
    return malla


# --- Formato automático de ejes, etiquetas y revisión de solapes --------------------------
_FORMATEADORES_FECHA = (mdates.AutoDateFormatter, mdates.ConciseDateFormatter, mdates.DateFormatter)


def formato_eje_anios(eje) -> None:
    """Años sin separador de miles (2024, no 2.024). Llamar antes de ``guardar_figura``."""
    eje.set_major_formatter(FuncFormatter(lambda x, _pos: f"{x:.0f}"))


def formato_eje_fechas(eje) -> None:
    """Ticks mensuales, bimestrales, trimestrales, semestrales o anuales (según el rango),
    con formato «ene 2024» y rotados 45°."""
    vmin, vmax = eje.get_view_interval()
    meses = max(1.0, (vmax - vmin) / 30.44)
    paso = next((p for p in (1, 2, 3, 6, 12, 24) if meses / p <= 16), 24)
    if paso >= 12:
        eje.set_major_locator(mdates.YearLocator(paso // 12))
    else:
        eje.set_major_locator(mdates.MonthLocator(bymonth=range(1, 13, paso)))
    eje.set_minor_locator(mdates.MonthLocator() if paso <= 3 else mdates.MonthLocator(bymonth=(1, 7)))
    eje.set_major_formatter(FuncFormatter(lambda x, _pos: fmt_mes(mdates.num2date(x))))
    eje.set_tick_params(which="major", labelrotation=45)


def aplicar_formato_ejes(fig: plt.Figure) -> None:
    """Números colombianos (sin notación científica) en todos los ejes numéricos y formato
    «ene 2024» en los ejes de fechas. Respeta los formateadores fijados a mano."""
    for ax in fig.axes:
        for eje in (ax.xaxis, ax.yaxis):
            mayor = eje.get_major_formatter()
            if isinstance(mayor, _FORMATEADORES_FECHA):
                formato_eje_fechas(eje)
            elif isinstance(mayor, (ScalarFormatter, LogFormatter)):
                eje.set_major_formatter(FuncFormatter(estilo.tick_numero))
                if isinstance(eje.get_minor_formatter(), LogFormatter):
                    eje.set_minor_formatter(NullFormatter())


def _alinear_fechas(fig: plt.Figure) -> None:
    for ax in fig.axes:
        if isinstance(ax.xaxis.get_major_formatter(), FuncFormatter) and ax.xaxis.get_major_locator().__class__ in (
            mdates.MonthLocator, mdates.YearLocator
        ):
            for etiqueta in ax.get_xticklabels():
                etiqueta.set_ha("right")
                etiqueta.set_rotation_mode("anchor")


def separar_etiquetas_finales(fig: plt.Figure, separacion_px: float = 2.0) -> None:
    """Separa verticalmente las etiquetas directas (``etiquetar_final``) que quedaron juntas."""
    renderer = fig.canvas.get_renderer()
    for ax in fig.axes:
        anotaciones = [t for t in ax.texts if t.get_gid() == GID_ETIQUETA_FINAL]
        if len(anotaciones) < 2:
            continue
        posiciones = []
        for a in anotaciones:
            punto = (ax.convert_xunits(a.xy[0]), ax.convert_yunits(a.xy[1]))
            y_px = ax.transData.transform(punto)[1]
            alto = a.get_window_extent(renderer).height
            posiciones.append([y_px, alto, a])
        posiciones.sort(key=lambda p: p[0])
        objetivo = [p[0] for p in posiciones]
        for i in range(1, len(posiciones)):
            minimo = objetivo[i - 1] + (posiciones[i - 1][1] + posiciones[i][1]) / 2 + separacion_px
            objetivo[i] = max(objetivo[i], minimo)
        for (y_px, _alto, a), y_nuevo in zip(posiciones, objetivo):
            desplazamiento_pt = (y_nuevo - y_px) * 72 / fig.dpi
            a.xyann = (a.xyann[0], desplazamiento_pt)


def _textos_visibles(fig: plt.Figure, renderer):
    excluir = set()
    for ax in fig.axes:
        for eje, limites in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
            bajo, alto = sorted(limites)
            margen = (alto - bajo) * 1e-6
            for tick in eje.get_major_ticks() + eje.get_minor_ticks():
                posicion = tick.get_loc()
                if posicion is None or not (bajo - margen <= posicion <= alto + margen):
                    excluir.update({id(tick.label1), id(tick.label2)})
    textos = []
    for t in fig.findobj(Text):
        if id(t) in excluir or not t.get_visible() or not t.get_text().strip():
            continue
        caja = t.get_window_extent(renderer)
        if caja.width > 0 and caja.height > 0:
            textos.append((t, caja))
    return textos


def revisar_solapes(fig: plt.Figure, nombre: str = "") -> list:
    """Dibuja la figura y advierte (sin detener la ejecución) si dos textos se superponen.

    Devuelve la lista de pares superpuestos (como textos)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    textos = _textos_visibles(fig, renderer)
    pares = []
    for i in range(len(textos)):
        t1, c1 = textos[i]
        for j in range(i + 1, len(textos)):
            t2, c2 = textos[j]
            if {t1.get_gid(), t2.get_gid()} == {GID_TITULO, GID_SUBTITULO}:
                continue
            ancho = min(c1.x1, c2.x1) - max(c1.x0, c2.x0)
            alto = min(c1.y1, c2.y1) - max(c1.y0, c2.y0)
            if ancho > 1 and alto > 1:
                pares.append((t1.get_text()[:40], t2.get_text()[:40]))
    if pares:
        ejemplos = "; ".join(f"«{a}» y «{b}»" for a, b in pares[:5])
        warnings.warn(f"Figura {nombre}: {len(pares)} pares de textos superpuestos, por ejemplo {ejemplos}.",
                      stacklevel=2)
    return pares


def guardar_figura(fig: plt.Figure, nombre: str) -> None:
    """Aplica el formato automático, revisa solapes y guarda ``reports/figures/{nombre}.png``
    (300 dpi) y ``.svg``."""
    aplicar_formato_ejes(fig)
    fig.canvas.draw()
    _alinear_fechas(fig)
    separar_etiquetas_finales(fig)
    revisar_solapes(fig, nombre)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / f"{nombre}.png", dpi=300)
    fig.savefig(FIGURAS / f"{nombre}.svg")
