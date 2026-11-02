"""Tema visual del proyecto (paleta B · Petróleo y ciruela) para las figuras del EDA.

Cada color tiene un solo significado en todo el proyecto. Solo se implementa el
modo claro, que es el indicado para impresión y proyección; los valores del modo
oscuro y el semáforo quedan para el dashboard.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from .config import FIGURAS, GRUPOS, UMBRAL_OPERATIVO_H

# --- Neutros ---------------------------------------------------------------------
FONDO = "#FFFFFF"
PANEL = "#F6F7F9"
TEXTO_PRIMARIO = "#1B2430"
TEXTO_SECUNDARIO = "#5B6573"
EJES = "#8A939E"
CUADRICULA = "#E4E7EB"

# --- Grupos principales ------------------------------------------------------------
COLOR_BASE = "#008A9E"  # petróleo: no hospitalizado con atención (grupo de referencia)
COLOR_HOSP = "#8F326A"  # ciruela: hospitalizado (foco del hallazgo)
COLOR_APOYO = "#A090E3"  # lavanda: tercer grupo cuando haga falta (siempre con etiqueta)
COLOR_CONTEXTO = "#ADAAA7"  # gris: contactos breves y hospitalizados sin hora de piso

COLORES_GRUPO = {
    GRUPOS[0]: COLOR_CONTEXTO,
    GRUPOS[1]: COLOR_BASE,
    GRUPOS[2]: COLOR_HOSP,
    GRUPOS[3]: COLOR_CONTEXTO,
}
ETIQUETAS_GRUPO = {
    GRUPOS[0]: "1. Contacto breve (< 5 min)",
    GRUPOS[1]: "2. No hospitalizado con atención",
    GRUPOS[2]: "3. Hospitalizado con hora de piso",
    GRUPOS[3]: "4. Hospitalizado sin hora de piso",
}
ETIQUETAS_CORTAS_GRUPO = {
    GRUPOS[0]: "Contacto breve",
    GRUPOS[1]: "No hospitalizado",
    GRUPOS[2]: "Hospitalizado",
    GRUPOS[3]: "Hosp. sin hora de piso",
}

# --- Grupos de edad (escala ordenada claro → oscuro) y sexo -------------------------
COLORES_EDAD = {"pediatria": "#98B3D7", "adulto": "#5C88C1", "adulto_mayor": "#225899"}
COLORES_SEXO = {"femenino": "#A4622A", "masculino": "#A9AB4A"}  # oliva: siempre con etiqueta

# --- Series técnicas (inventario de calidad, sin significado de grupo) ---------------
# Grises de oscuro a claro; se distinguen además por marcador y etiqueta directa.
GRISES_TECNICOS = [TEXTO_PRIMARIO, TEXTO_SECUNDARIO, EJES, COLOR_CONTEXTO]
MARCADORES = ["o", "s", "^", "D"]

# --- Heatmap secuencial (7 pasos, menor → mayor) --------------------------------------
PASOS_HEATMAP = ["#EAF8FB", "#C5E5EC", "#91C9D4", "#55A9BA", "#00869A", "#006678", "#004555"]
RAMPA_HEATMAP = ListedColormap(PASOS_HEATMAP, name="petroleo_7_pasos")
RAMPA_HEATMAP.set_bad(FONDO)

# --- Trazos ---------------------------------------------------------------------------
ANCHO_LINEA = 2.0
ANCHO_LINEA_HOSP = 2.5

DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def aplicar_estilo() -> None:
    """Aplica el tema claro: cuadrícula solo horizontal, sin bordes superior ni derecho."""
    mpl.rcParams.update(
        {
            "figure.figsize": (10, 5.5),
            "figure.dpi": 100,
            "figure.facecolor": FONDO,
            "axes.facecolor": FONDO,
            "font.size": 13,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlecolor": TEXTO_PRIMARIO,
            "axes.labelsize": 13,
            "axes.labelcolor": TEXTO_SECUNDARIO,
            "axes.edgecolor": EJES,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "axes.prop_cycle": mpl.cycler(color=GRISES_TECNICOS),
            "grid.color": CUADRICULA,
            "grid.linewidth": 0.8,
            "xtick.color": EJES,
            "ytick.color": EJES,
            "xtick.labelcolor": TEXTO_SECUNDARIO,
            "ytick.labelcolor": TEXTO_SECUNDARIO,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "legend.fontsize": 11,
            "legend.frameon": False,
            "legend.labelcolor": TEXTO_PRIMARIO,
            "lines.linewidth": ANCHO_LINEA,
            "lines.markersize": 6,
            "patch.edgecolor": FONDO,
            "text.color": TEXTO_PRIMARIO,
            "savefig.bbox": "tight",
            "savefig.facecolor": FONDO,
            "svg.fonttype": "none",
        }
    )


def guardar_figura(fig: plt.Figure, nombre: str) -> None:
    """Guarda la figura en ``reports/figures/{nombre}.png`` (300 dpi) y ``.svg``."""
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / f"{nombre}.png", dpi=300)
    fig.savefig(FIGURAS / f"{nombre}.svg")


def ancho_linea(grupo: str | None = None) -> float:
    """2 px para todas las series y 2,5 px para hospitalizado."""
    return ANCHO_LINEA_HOSP if grupo == GRUPOS[2] else ANCHO_LINEA


def marcar_umbrales(ax: plt.Axes, umbrales, eje: str = "x") -> None:
    """Líneas de referencia con etiqueta.

    El umbral operativo (12 h) va punteado en el color de texto principal con la
    etiqueta «Umbral 12 h»; los demás, discontinuos y en texto secundario.
    """
    for umbral in umbrales:
        if umbral == UMBRAL_OPERATIVO_H:
            color, estilo, ancho, texto = TEXTO_PRIMARIO, ":", 1.6, f"Umbral {umbral} h"
        else:
            color, estilo, ancho, texto = TEXTO_SECUNDARIO, "--", 1.0, f"{umbral} h"
        if eje == "x":
            ax.axvline(umbral, color=color, linestyle=estilo, linewidth=ancho, zorder=1)
            ax.annotate(texto, xy=(umbral, 1), xycoords=("data", "axes fraction"), xytext=(3, -14),
                        textcoords="offset points", color=color, fontsize=10)
        else:
            ax.axhline(umbral, color=color, linestyle=estilo, linewidth=ancho, zorder=1)
            ax.annotate(texto, xy=(1, umbral), xycoords=("axes fraction", "data"), xytext=(-3, 3),
                        textcoords="offset points", color=color, fontsize=10, ha="right")


def etiquetar_final(ax: plt.Axes, x, y, texto: str, color: str = TEXTO_PRIMARIO) -> None:
    """Etiqueta directa al final de una línea (último punto no nulo)."""
    x = list(x)  # conserva Timestamp en ejes de fechas
    y = np.asarray(y, dtype=float)
    validos = np.flatnonzero(~np.isnan(y))
    if validos.size == 0:
        return
    i = validos[-1]
    ax.annotate(texto, xy=(x[i], y[i]), xytext=(6, 0), textcoords="offset points",
                va="center", color=color, fontsize=10, annotation_clip=False)


def rotular_barras(ax: plt.Axes, barras, valores, formato: str = "{:.1f}", alturas=None) -> None:
    """Escribe el valor sobre cada barra; ``alturas`` permite subir la etiqueta (p. ej., sobre el IC)."""
    valores = np.asarray(valores, dtype=float)
    alturas = valores if alturas is None else np.asarray(alturas, dtype=float)
    for barra, valor, altura in zip(barras, valores, alturas):
        if np.isnan(valor):
            continue
        ax.annotate(formato.format(valor), xy=(barra.get_x() + barra.get_width() / 2, altura),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    color=TEXTO_PRIMARIO, fontsize=10)


def heatmap_hora_dia(ax: plt.Axes, matriz, titulo: str, etiqueta_barra: str):
    """Mapa de calor hora (filas 0–23) × día de la semana (columnas 0–6) en 7 pasos.

    Las celdas en ``NaN`` (suprimidas por tamaño) quedan del color del fondo, y las
    celdas se separan con un borde de 1,5 px del color del fondo.
    """
    matriz = matriz.reindex(index=range(24), columns=range(7))
    datos = np.ma.masked_invalid(matriz.to_numpy(dtype=float))
    minimo, maximo = (datos.min(), datos.max()) if datos.count() else (0.0, 1.0)
    if minimo == maximo:
        maximo = minimo + 1
    norma = BoundaryNorm(np.linspace(minimo, maximo, len(PASOS_HEATMAP) + 1), RAMPA_HEATMAP.N)
    malla = ax.pcolormesh(np.arange(8) - 0.5, np.arange(25) - 0.5, datos, cmap=RAMPA_HEATMAP, norm=norma,
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
    barra = ax.figure.colorbar(malla, ax=ax, shrink=0.85, format="%.1f")
    barra.set_label(etiqueta_barra)
    barra.outline.set_visible(False)
    return malla
