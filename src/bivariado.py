"""Análisis bivariado de los predictores frente a la estancia en urgencias (notebook 08), sin modelos.

Cada predictor se categoriza (categorías, valores discretos, conteos 0/1/2/3+ o deciles dentro del grupo)
y, para cada categoría y grupo (atención en urgencias y hospitalizado, siempre por separado), se calcula
n, % con LOS > 12 h con IC de Wilson y la mediana del LOS con sus percentiles 25 y 75.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from . import estilo
from .config import GRUPOS, MIN_CELDA, ROLES_CARACTERISTICAS, UMBRAL_OPERATIVO_H
from .estadistica import comparar_categorica, ic_wilson
from .estilo import fmt_numero
from .graficos import guardar_figura, titulo_hallazgo
from .privacidad import suprimir_pequenos
from .tablas import mostrar_tabla

G1, G2, G3 = GRUPOS
GRUPOS_BIVARIADO = (G2, G3)
DESENLACE_BINARIO = "y_los_mas_12h"
DESENLACE_LOS = "y_los_h"
SUFIJO = f"mas_{UMBRAL_OPERATIVO_H}h"

# Familias de predictores (cada predictor de ROLES_CARACTERISTICAS debe estar en una).
FAMILIAS = {
    "calendario": ("hora", "dia_semana", "mes", "anio", "fin_de_semana", "festivo", "franja"),
    "paciente": ("sexo", "edad_llegada", "pediatria", "grupo_edad"),
    "historia previa": ("hosp_previa_30d", "n_episodios_previos_30d", "n_episodios_previos_365d"),
    "cola en urgencias": ("urg_atencion_presentes_llegada", "urg_atencion_presentes_llegada_pct_trimestre"),
    "ocupación del piso": ("piso_censo_llegada", "piso_censo_llegada_pct_trimestre", "piso_grupo_censo_llegada",
                           "piso_grupo_censo_llegada_pct_trimestre"),
    "LOS reciente": ("los_reciente_promedio_h", "los_reciente_mediana_h", "n_salidas_recientes"),
}
# Variables de historia: solo se analizan en los episodios con la ventana completa.
MARCA_HISTORIA = {
    "hosp_previa_30d": "historia_completa_30d",
    "n_episodios_previos_30d": "historia_completa_30d",
    "n_episodios_previos_365d": "historia_completa_365d",
}
DISCRETAS = ("hora", "dia_semana", "mes", "anio", "franja")
CONTEOS_PREVIOS = ("n_episodios_previos_30d", "n_episodios_previos_365d")
# Variables cuyo gráfico ya está en el notebook 04 (heatmap hora × día, % > 12 h por grupo etario y sexo,
# % > 12 h según hospitalización previa): en el 08 solo se muestra su tabla.
SIN_FIGURA = ("hora", "dia_semana", "sexo", "edad_llegada", "pediatria", "grupo_edad", "hosp_previa_30d")
# Variables que no entran al gráfico de tamaño de efecto (sí a su tabla): versiones absolutas de la ocupación
# (queda su percentil del trimestre) y versiones redundantes de la edad (queda grupo_edad).
EXCLUIR_DE_EFECTO = ("piso_censo_llegada", "piso_grupo_censo_llegada", "urg_atencion_presentes_llegada",
                     "edad_llegada", "pediatria")


# --- Población --------------------------------------------------------------------------------------
def poblacion_bivariado(caracteristicas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica los filtros del análisis y devuelve (episodios, tabla de n por grupo después de cada filtro).

    Filtros: grupos de atención en urgencias y hospitalizado; válidos para tiempos; fuera del periodo de
    calentamiento del censo; con LOS. Las dos últimas filas de la tabla son los subconjuntos con la
    historia de 30 y 365 días completa (los que usan las variables de historia).
    """
    pasos = [("Episodios de la población de análisis", pd.Series(True, index=caracteristicas.index))]
    filtro = caracteristicas["grupo"].isin(GRUPOS_BIVARIADO)
    pasos.append(("Atención en urgencias y hospitalizados", filtro.copy()))
    filtro &= caracteristicas["valido_para_tiempos"].astype(bool)
    pasos.append(("Válidos para tiempos", filtro.copy()))
    filtro &= ~caracteristicas["censo_calentamiento"].astype(bool)
    pasos.append(("Fuera del periodo de calentamiento", filtro.copy()))
    filtro &= caracteristicas[DESENLACE_LOS].notna() & caracteristicas[DESENLACE_BINARIO].notna()
    pasos.append(("Con LOS", filtro.copy()))
    for marca in ("historia_completa_30d", "historia_completa_365d"):
        pasos.append((f"Con LOS e {marca.replace('_', ' ')}", filtro & caracteristicas[marca].astype(bool)))

    grupos = list(GRUPOS)
    tabla = pd.DataFrame(
        {paso: caracteristicas.loc[mascara, "grupo"].value_counts().reindex(grupos, fill_value=0)
         for paso, mascara in pasos}).T
    tabla.columns = [f"n_{grupo}" for grupo in tabla.columns]
    return caracteristicas[filtro].copy(), tabla.rename_axis("paso")


def episodios_de_variable(episodios: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Episodios con dato de la variable; las variables de historia, solo con su ventana completa."""
    datos = episodios[episodios[variable].notna()]
    if variable in MARCA_HISTORIA:
        datos = datos[datos[MARCA_HISTORIA[variable]].astype(bool)]
    return datos


# --- Categorización ---------------------------------------------------------------------------------
def es_continua(variable: str, serie: pd.Series) -> bool:
    """Se categoriza en deciles: numérica, no booleana, ni discreta ni conteo de episodios previos."""
    return (pd.api.types.is_numeric_dtype(serie) and not pd.api.types.is_bool_dtype(serie)
            and variable not in DISCRETAS and variable not in CONTEOS_PREVIOS)


def categorizar(serie: pd.Series, variable: str) -> tuple[pd.Series, pd.DataFrame | None]:
    """Categoría de cada episodio y, para las continuas, los cortes de cada decil (``desde``, ``hasta``).

    - Categóricas y booleanas: sus categorías (booleanas como «No» / «Sí»).
    - Discretas (hora, día de la semana, mes, año, franja): cada valor.
    - Conteos de episodios previos: 0, 1, 2, 3 o más.
    - Continuas: deciles de ``serie`` (se llama dentro de cada grupo); si hay valores repetidos, puede
      haber menos de 10.
    """
    if variable in CONTEOS_PREVIOS:
        valores = serie.astype(float).clip(upper=3)
        etiquetas = {0: "0", 1: "1", 2: "2", 3: "3 o más"}
        return pd.Categorical(valores.map(etiquetas), categories=list(etiquetas.values()), ordered=True), None
    if pd.api.types.is_bool_dtype(serie):
        return pd.Categorical(serie.map({True: "Sí", False: "No"}), categories=["No", "Sí"], ordered=True), None
    if es_continua(variable, serie):
        deciles, bordes = pd.qcut(serie.astype(float), 10, labels=False, retbins=True, duplicates="drop")
        etiquetas = [f"D{i + 1}" for i in range(len(bordes) - 1)]
        categoria = pd.Categorical.from_codes(deciles.fillna(-1).astype(int), categories=etiquetas, ordered=True)
        cortes = pd.DataFrame({"desde": bordes[:-1], "hasta": bordes[1:]}, index=pd.Index(etiquetas, name="categoria"))
        return categoria, cortes
    if variable == "dia_semana":
        return pd.Categorical(serie.map(dict(enumerate(estilo.DIAS_SEMANA))), categories=list(estilo.DIAS_SEMANA),
                              ordered=True), None
    if isinstance(serie.dtype, pd.CategoricalDtype):
        return serie.astype(str).astype(pd.CategoricalDtype([str(c) for c in serie.cat.categories], ordered=True)), None
    valores = sorted(serie.dropna().unique())
    return pd.Categorical(serie.astype(object).map(str), categories=[str(v) for v in valores], ordered=True), None


# --- Tablas -----------------------------------------------------------------------------------------
def resumen_por_categoria(categoria, binario: pd.Series, los: pd.Series) -> pd.DataFrame:
    """Por categoría: n, episodios y % con LOS > 12 h con IC de Wilson (en %), y mediana, p25 y p75 del LOS."""
    datos = pd.DataFrame({"categoria": categoria, "binario": binario.astype(bool).to_numpy(),
                          "los": los.astype(float).to_numpy()})
    grupos = datos.groupby("categoria", observed=False)
    tabla = pd.DataFrame({"n": grupos.size(), f"n_{SUFIJO}": grupos["binario"].sum().astype("int64")})
    tabla[f"pct_{SUFIJO}"] = 100 * tabla[f"n_{SUFIJO}"] / tabla["n"].where(tabla["n"] > 0)
    inferior, superior = ic_wilson(tabla[f"n_{SUFIJO}"].to_numpy(), tabla["n"].to_numpy())
    tabla[f"ic_inf_{SUFIJO}"] = 100 * inferior
    tabla[f"ic_sup_{SUFIJO}"] = 100 * superior
    tabla["mediana_h"] = grupos["los"].median()
    tabla["p25_h"] = grupos["los"].quantile(0.25)
    tabla["p75_h"] = grupos["los"].quantile(0.75)
    return tabla


def tabla_variable(episodios: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Tabla bivariada de una variable para cada grupo (deciles calculados dentro de cada grupo).
    Índice: grupo y categoría; columnas: cortes (``desde``, ``hasta``, solo continuas), n, % > 12 h con IC y
    mediana del LOS con p25 y p75."""
    partes = {}
    for grupo in GRUPOS_BIVARIADO:
        datos = episodios_de_variable(episodios[episodios["grupo"].eq(grupo)], variable)
        categoria, cortes = categorizar(datos[variable], variable)
        tabla = resumen_por_categoria(categoria, datos[DESENLACE_BINARIO], datos[DESENLACE_LOS])
        if cortes is not None:
            tabla = cortes.join(tabla, how="right")
        partes[grupo] = tabla
    tabla = pd.concat(partes, names=["grupo", "categoria"])
    if "desde" not in tabla.columns:
        tabla.insert(0, "desde", np.nan)
        tabla.insert(1, "hasta", np.nan)
    return tabla


def columnas_derivadas(tabla: pd.DataFrame) -> list[str]:
    """Columnas derivadas de los conteos (las que se ocultan si n < 10); los cortes no dependen de n."""
    return [c for c in tabla.columns if c not in ("n", f"n_{SUFIJO}", "desde", "hasta")
            and pd.api.types.is_numeric_dtype(tabla[c])]


def efecto_variable(episodios: pd.DataFrame, variable: str, tabla: pd.DataFrame) -> pd.DataFrame:
    """Tamaño de efecto por grupo: diferencia (puntos porcentuales) entre la categoría con mayor y menor
    % > 12 h (solo categorías con n ≥ 10), V de Cramér entre la categoría y LOS > 12 h (mismas categorías;
    ``comparar_categorica``) y, para las continuas, correlación de Spearman con el LOS en horas."""
    filas = []
    for grupo in GRUPOS_BIVARIADO:
        parte = tabla.loc[grupo]
        validas = parte[parte["n"] >= MIN_CELDA]
        datos = episodios_de_variable(episodios[episodios["grupo"].eq(grupo)], variable)
        categoria, _ = categorizar(datos[variable], variable)
        categoria = pd.Series(categoria, index=datos.index).astype(str)
        en_validas = categoria.isin(validas.index.astype(str))
        binario = datos[DESENLACE_BINARIO].astype(bool)
        v_cramer = np.nan
        if len(validas) > 1:
            v_cramer = float(comparar_categorica(categoria[en_validas & binario],
                                                 categoria[en_validas & ~binario])["v_cramer"].iloc[0])
        spearman = np.nan
        if es_continua(variable, datos[variable]):
            spearman = float(datos[variable].astype(float).corr(datos[DESENLACE_LOS].astype(float), method="spearman"))
        filas.append({
            "grupo": grupo, "variable": variable, "n": int(len(datos)),
            "diferencia_max_pp": (validas[f"pct_{SUFIJO}"].max() - validas[f"pct_{SUFIJO}"].min()
                                  if len(validas) > 1 else np.nan),
            "v_cramer": v_cramer, "spearman": spearman,
        })
    return pd.DataFrame(filas)


def tendencia_trimestral(episodios: pd.DataFrame) -> pd.DataFrame:
    """Por grupo y trimestre de llegada: llegadas (n), % > 12 h con IC y mediana del LOS con p25 y p75."""
    partes = {}
    for grupo in GRUPOS_BIVARIADO:
        datos = episodios[episodios["grupo"].eq(grupo)]
        trimestre = datos["llegada"].dt.to_period("Q").astype(str)
        orden = sorted(trimestre.unique())
        partes[grupo] = resumen_por_categoria(pd.Categorical(trimestre, categories=orden, ordered=True),
                                              datos[DESENLACE_BINARIO], datos[DESENLACE_LOS])
    return pd.concat(partes, names=["grupo", "trimestre"])


# --- Gráficos ---------------------------------------------------------------------------------------
def _visible(parte: pd.DataFrame, columna: str) -> np.ndarray:
    """Valores de ``columna`` ocultos (NaN) en las categorías que la tabla suprime: menos de 10 episodios,
    o entre 1 y 9 episodios con LOS > 12 h."""
    eventos = parte[f"n_{SUFIJO}"]
    oculta = parte["n"].lt(MIN_CELDA) | (eventos.gt(0) & eventos.lt(MIN_CELDA))
    return parte[columna].where(~oculta).to_numpy(dtype=float)


def grafico_pct(ax, tabla: pd.DataFrame, variable: str) -> None:
    """% > 12 h por categoría con IC de Wilson; atención en urgencias en azul y hospitalizados en ciruela,
    en el mismo panel. Las categorías con menos de 10 episodios no se dibujan."""
    categorias = list(dict.fromkeys(tabla.index.get_level_values("categoria")))
    x = np.arange(len(categorias))
    desplazamiento = {G2: -0.12, G3: 0.12}
    for grupo in GRUPOS_BIVARIADO:
        parte = tabla.loc[grupo].reindex(categorias)
        pct = _visible(parte, f"pct_{SUFIJO}")
        inferior = pct - _visible(parte, f"ic_inf_{SUFIJO}")
        superior = _visible(parte, f"ic_sup_{SUFIJO}") - pct
        ax.errorbar(x + desplazamiento[grupo], pct, yerr=[inferior, superior], fmt="o-", markersize=4, capsize=2,
                    color=estilo.COLOR_ROL[grupo], linewidth=estilo.GROSOR_ROL[grupo] * 0.6,
                    label=estilo.ETIQUETA_CORTA_ROL[grupo])
    rotar = len(categorias) > 8 or max(len(str(c)) for c in categorias) > 6
    ax.set_xticks(x, categorias, rotation=45 if rotar else 0, ha="right" if rotar else "center",
                  rotation_mode="anchor", fontsize=estilo.TAMANO_MINIMO)
    ax.set_title(variable, loc="left", fontsize=estilo.TAMANO_EJES)
    ax.set_ylabel(f"% LOS > {UMBRAL_OPERATIVO_H} h")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{fmt_numero(v)} %"))


def figura_familia(tablas: dict, variables) -> plt.Figure | None:
    """Un panel por variable (sin las de ``SIN_FIGURA``) con ``grafico_pct``; ``None`` si no queda ninguna."""
    variables = [v for v in variables if v not in SIN_FIGURA]
    if not variables:
        return None
    columnas = 2
    filas = int(np.ceil(len(variables) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(14, 4.2 * filas), squeeze=False)
    fig.get_layout_engine().set(hspace=0.12, wspace=0.08)
    for ax, variable in zip(ejes.flat, variables):
        grafico_pct(ax, tablas[variable], variable)
    for ax in list(ejes.flat)[len(variables):]:
        ax.set_visible(False)
    ejes.flat[0].legend(loc="upper left", fontsize=estilo.TAMANO_MINIMO)
    return fig


def grafico_efecto(efectos: pd.DataFrame) -> plt.Figure:
    """Gráfico de puntos de la V de Cramér, con las variables ordenadas por V de Cramér dentro de cada grupo;
    un panel por grupo. No incluye las variables de ``EXCLUIR_DE_EFECTO``."""
    efectos = efectos[~efectos["variable"].isin(EXCLUIR_DE_EFECTO)]
    fig, ejes = plt.subplots(1, len(GRUPOS_BIVARIADO), figsize=(14, 0.32 * efectos["variable"].nunique() + 2),
                             squeeze=False)
    for ax, grupo in zip(ejes[0], GRUPOS_BIVARIADO):
        datos = efectos[efectos["grupo"].eq(grupo)].dropna(subset=["v_cramer"])
        datos = datos.sort_values("v_cramer")
        y = np.arange(len(datos))
        ax.hlines(y, 0, datos["v_cramer"], color=estilo.BORDE, linewidth=1.5)
        ax.plot(datos["v_cramer"], y, "o", color=estilo.COLOR_ROL[grupo], markersize=6)
        ax.set_yticks(y, datos["variable"], fontsize=estilo.TAMANO_MINIMO)
        ax.set_xlabel("V de Cramér")
        ax.set_title(estilo.ETIQUETA_CORTA_ROL[grupo], loc="left", fontsize=estilo.TAMANO_EJES)
        ax.set_xlim(left=0)
        ax.grid(axis="y", visible=False)
    return fig


def grafico_tendencia(tendencia: pd.DataFrame) -> plt.Figure:
    """Por trimestre: % > 12 h con IC, mediana del LOS y llegadas, una línea por grupo."""
    fig, ejes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    for grupo in GRUPOS_BIVARIADO:
        parte = tendencia.loc[grupo]
        x = np.arange(len(parte))
        color = estilo.COLOR_ROL[grupo]
        etiqueta = estilo.ETIQUETA_CORTA_ROL[grupo]
        pct = _visible(parte, f"pct_{SUFIJO}")
        ejes[0].plot(x, pct, "o-", color=color, markersize=4, label=etiqueta)
        ejes[0].fill_between(x, _visible(parte, f"ic_inf_{SUFIJO}"), _visible(parte, f"ic_sup_{SUFIJO}"),
                             color=color, alpha=0.15, linewidth=0)
        ejes[1].plot(x, _visible(parte, "mediana_h"), "o-", color=color, markersize=4, label=etiqueta)
        ejes[2].plot(x, parte["n"].where(parte["n"] >= MIN_CELDA), "o-", color=color, markersize=4, label=etiqueta)
    trimestres = list(tendencia.loc[GRUPOS_BIVARIADO[0]].index)
    ejes[2].set_xticks(np.arange(len(trimestres)), trimestres, rotation=45, ha="right", rotation_mode="anchor",
                       fontsize=estilo.TAMANO_MINIMO)
    ejes[0].set_ylabel(f"% LOS > {UMBRAL_OPERATIVO_H} h")
    ejes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{fmt_numero(v)} %"))
    ejes[1].set_ylabel("Mediana del LOS (h)")
    ejes[2].set_ylabel("Llegadas")
    for ax in ejes:
        ax.set_ylim(bottom=0)
    ejes[0].legend(loc="upper left", fontsize=estilo.TAMANO_MINIMO)
    return fig


# --- Presentación por familia y exportación ---------------------------------------------------------
def predictores_de_familia(familia: str) -> list[str]:
    """Variables de la familia con rol «predictor» en ``ROLES_CARACTERISTICAS``."""
    return [v for v in FAMILIAS[familia] if ROLES_CARACTERISTICAS.get(v) == "predictor"]


def tabla_segura_bivariado(tabla: pd.DataFrame) -> pd.DataFrame:
    """Redondea y oculta las categorías con menos de 10 episodios (o de 1 a 9 con LOS > 12 h)."""
    return suprimir_pequenos(tabla.round(2), ["n", f"n_{SUFIJO}"], columnas_derivadas=columnas_derivadas(tabla))


def mostrar_familia(episodios: pd.DataFrame, familia: str, nombre_figura: str) -> dict:
    """Muestra la tabla bivariada de cada predictor de la familia y, si hay variables con gráfico, la figura
    de % > 12 h por categoría. Devuelve ``{variable: tabla}`` (sin suprimir) para el tamaño de efecto y la
    exportación."""
    tablas = {}
    for variable in predictores_de_familia(familia):
        tablas[variable] = tabla_variable(episodios, variable)
        mostrar_tabla(tabla_segura_bivariado(tablas[variable]),
                      f"{variable}: % con LOS > {UMBRAL_OPERATIVO_H} h y LOS por categoría y grupo")
    fig = figura_familia(tablas, list(tablas))
    if fig is not None:
        titulo_hallazgo(fig, f"% con LOS > {UMBRAL_OPERATIVO_H} h según {familia}",
                        "Por categoría o decil, con IC 95 % de Wilson; categorías con menos de 10 episodios sin punto")
        guardar_figura(fig, nombre_figura)
        plt.show()
    return tablas


def tabla_exportacion(tablas: dict) -> pd.DataFrame:
    """Todas las tablas bivariadas en formato largo: grupo, variable, categoría, cortes, n, % > 12 h con IC y
    mediana del LOS con p25 y p75, con los conteos pequeños suprimidos."""
    largo = pd.concat(tablas, names=["variable"]).reorder_levels(["grupo", "variable", "categoria"])
    largo = largo.reset_index()
    largo["categoria"] = largo["categoria"].astype(str)
    return suprimir_pequenos(largo.round(4), ["n", f"n_{SUFIJO}"], columnas_derivadas=columnas_derivadas(largo))
