"""Valores imposibles y extremos: detección, simulación de acciones y aplicación de reglas.

Los notebooks 03 (registros) y 05 (episodios) solo detectan y simulan. Las acciones se aplican con
``aplicar_reglas_registro`` y ``aplicar_reglas_episodio`` según ``REGLAS_REGISTRO`` y
``REGLAS_EPISODIO`` de ``src/config.py``; mientras una regla esté en ``"pendiente"`` no se aplica nada.

Las marcas son DataFrames booleanos con una columna por regla. Si una regla tiene varias formas de
detección (``criterios``), hay una columna por criterio con el nombre ``<regla>__<criterio>``.
"""

import numpy as np
import pandas as pd

from .config import (
    ACCIONES_EPISODIO,
    ACCIONES_REGISTRO,
    CONTACTO_BREVE,
    FACTOR_TUKEY_LOG,
    GRUPOS,
    PERCENTILES_EXTREMOS,
    UMBRAL_INGRESO_LARGO_MIN,
    REGLAS_EPISODIO,
    REGLAS_REGISTRO,
    UMBRAL_OPERATIVO_H,
)

G1, G2, G3 = GRUPOS
HORAS_CONTACTO_BREVE = CONTACTO_BREVE / pd.Timedelta(hours=1)


# --- Límites de detección -------------------------------------------------------------------------
def limite_percentil(serie: pd.Series, criterio: str) -> float:
    """Percentil de ``PERCENTILES_EXTREMOS`` (``p99`` o ``p99_9``) de los valores no nulos."""
    valores = pd.to_numeric(serie, errors="coerce").dropna()
    return float(valores.quantile(PERCENTILES_EXTREMOS[criterio])) if len(valores) else np.nan


def limite_tukey_log(serie: pd.Series, factor: float = FACTOR_TUKEY_LOG) -> float:
    """Límite superior de Tukey sobre el logaritmo natural de los valores positivos:
    ``exp(Q3 + factor × RIC)``, con los cuartiles del logaritmo."""
    valores = pd.to_numeric(serie, errors="coerce")
    positivos = valores[valores > 0].dropna()
    if positivos.empty:
        return np.nan
    logaritmo = np.log(positivos)
    q1, q3 = logaritmo.quantile([0.25, 0.75])
    return float(np.exp(q3 + factor * (q3 - q1)))


def limites(serie: pd.Series, criterios=("p99_9", "tukey_log")) -> dict:
    """Límite superior de ``serie`` para cada criterio (``p99``, ``p99_9`` o ``tukey_log``)."""
    return {c: limite_tukey_log(serie) if c == "tukey_log" else limite_percentil(serie, c) for c in criterios}


def conteo_por_paciente_anio(tabla: pd.DataFrame) -> pd.Series:
    """Número de filas del mismo paciente en el mismo año de llegada, alineado con ``tabla``.
    Usa ``person_id`` solo de forma interna."""
    anio = tabla["llegada"].dt.year
    return tabla.groupby([tabla["person_id"], anio])["llegada"].transform("size")


# --- Reglas de registro (nivel visita) ----------------------------------------------------------
def detectar_registros(visitas: pd.DataFrame, limites_etapa: dict) -> tuple[pd.DataFrame, dict]:
    """Marcas booleanas por regla de ``REGLAS_REGISTRO`` a nivel de visita.

    ``visitas`` viene de ``preparar_visitas``. ``limites_etapa`` tiene, por tipo de etapa, los límites
    de duración calculados en SQL (``{9203: {"p99_9": h, "tukey_log": h}, 3045729: {...}, 9201: {...}}``);
    una visita queda marcada si la duración máxima de alguno de sus tipos de etapa (``max_dur_<tipo>_h``)
    supera el límite de ese tipo. Devuelve (marcas, límites usados).
    """
    v = visitas
    marcas = pd.DataFrame(index=v.index)
    marcas["anio_nacimiento_imposible"] = v["estado_edad"].eq("anio_invalido")
    marcas["edad_negativa"] = v["estado_edad"].eq("negativa")
    marcas["edad_mayor_110"] = v["estado_edad"].eq("mayor_110")
    marcas["sexo_sin_dato"] = v["sexo"].eq("otro_o_sin_dato")
    marcas["etapas_duracion_0"] = v["n_etapas_dur_0"].gt(0)
    criterios_etapa = sorted({c for por_criterio in limites_etapa.values() for c in por_criterio})
    for criterio in criterios_etapa:
        supera = pd.Series(False, index=v.index)
        for concepto, por_criterio in limites_etapa.items():
            columna = f"max_dur_{int(concepto)}_h"
            if columna in v.columns and criterio in por_criterio:
                supera |= v[columna].gt(por_criterio[criterio])
        marcas[f"etapas_duracion_extrema__{criterio}"] = supera
    marcas["fin_fraccion_segundo"] = v["fin_fraccion_segundo"].eq(True)
    marcas["hosp_antes_de_llegada"] = v["inicio_piso"].lt(v["llegada"])
    marcas["visitas_sin_etapas"] = v["sin_etapas"].eq(True)
    marcas["ingresos_9203_largos"] = v["max_dur_9203_h"].gt(UMBRAL_INGRESO_LARGO_MIN / 60)

    usados = {"etapas_duracion_extrema": {int(c): dict(p) for c, p in limites_etapa.items()}}
    usados["etapas_por_visita_extremas"] = limites(v.loc[v["n_etapas"] > 0, "n_etapas"])
    for criterio, limite in usados["etapas_por_visita_extremas"].items():
        marcas[f"etapas_por_visita_extremas__{criterio}"] = v["n_etapas"].gt(limite)
    visitas_paciente_anio = conteo_por_paciente_anio(v)
    usados["paciente_muchas_visitas"] = limites(visitas_paciente_anio)
    for criterio, limite in usados["paciente_muchas_visitas"].items():
        marcas[f"paciente_muchas_visitas__{criterio}"] = visitas_paciente_anio.gt(limite)
    return marcas, usados


def _columna_marca(marcas: pd.DataFrame, clave: str, regla: dict) -> pd.Series:
    """Marca de una regla; si tiene varios criterios, la del criterio elegido en la regla."""
    if "criterios" not in regla:
        return marcas[clave]
    criterio = regla.get("criterio", "pendiente")
    if criterio not in regla["criterios"]:
        raise ValueError(f"La regla '{clave}' tiene acción '{regla['accion']}' pero su criterio es '{criterio}'. "
                         f"Elige uno de {regla['criterios']} en src/config.py.")
    return marcas[f"{clave}__{criterio}"]


def aplicar_reglas_registro(visitas: pd.DataFrame, marcas: pd.DataFrame, reglas: dict = REGLAS_REGISTRO,
                            episodio: pd.Series | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica las acciones de ``reglas`` a las visitas y devuelve (visitas, reporte agregado).

    - ``pendiente`` y ``conservar``: no cambian nada.
    - ``marcar``: agrega la columna booleana ``marca_<regla>``.
    - ``nan``: pone en NaN las ``columnas_nan`` de la regla en las visitas marcadas.
    - ``excluir``: quita las visitas marcadas. Se aplica a nivel de visita, antes de la fusión.

    El reporte tiene, por regla, la acción, las visitas marcadas y, para las que excluyen, las visitas
    quitadas y los episodios que desaparecen o cambian. Las exclusiones se cuentan en el orden de
    ``reglas``: una visita ya quitada por una regla anterior no se vuelve a contar. Los episodios se
    cuentan con ``episodio`` (``episodios.episodio_de_visitas``, calculado antes de excluir); si no se
    da, esas columnas quedan vacías.
    """
    v = visitas.copy()
    restantes = pd.Series(True, index=visitas.index)
    filas = []
    for clave, regla in reglas.items():
        accion = regla["accion"]
        if accion not in ACCIONES_REGISTRO:
            raise ValueError(f"Acción desconocida '{accion}' en la regla '{clave}'. Opciones: {ACCIONES_REGISTRO}.")
        fila = {"regla": clave, "accion": accion, "n_marcadas": np.nan, "n_visitas_quitadas": 0,
                "n_episodios_quitados": 0, "n_episodios_modificados": 0}
        if accion == "pendiente" and "criterios" in regla:
            filas.append(fila)  # sin criterio elegido no hay una marca única que contar
            continue
        marca = _columna_marca(marcas, clave, regla).reindex(visitas.index, fill_value=False)
        fila["n_marcadas"] = int(marca.sum())
        if accion == "marcar":
            v[f"marca_{clave}"] = marca.reindex(v.index)
        elif accion == "nan":
            if not regla.get("columnas_nan"):
                raise ValueError(f"La regla '{clave}' no admite la acción 'nan' (no tiene columnas_nan).")
            v.loc[marca.reindex(v.index), regla["columnas_nan"]] = np.nan
        elif accion == "excluir":
            quitar = marca & restantes
            fila["n_visitas_quitadas"] = int(quitar.sum())
            if episodio is not None:
                antes = set(episodio[restantes].unique())
                despues = set(episodio[restantes & ~quitar].unique())
                tocados = set(episodio[quitar].unique())
                fila["n_episodios_quitados"] = len(antes - despues)
                fila["n_episodios_modificados"] = len(tocados & despues)
            else:
                fila["n_episodios_quitados"] = fila["n_episodios_modificados"] = np.nan
            restantes &= ~quitar
            v = v[restantes.reindex(v.index, fill_value=False)]
        filas.append(fila)
    return v, pd.DataFrame(filas).set_index("regla")


def simular_opciones_registro(marca: pd.Series, episodio: pd.Series, columnas_nan) -> pd.DataFrame:
    """Qué pasaría con cada acción posible para una marca de visitas (sin aplicar nada).

    ``episodio`` es el episodio de cada visita (``episodios.episodio_de_visitas``). Para
    ``excluir`` se cuentan los episodios que cambiarían (tienen alguna visita marcada) y los que
    desaparecerían (todas sus visitas están marcadas).
    """
    marca = marca.fillna(False).astype(bool)
    por_episodio = marca.groupby(episodio)
    n_visitas = int(marca.sum())
    n_cambian = int(por_episodio.any().sum())
    n_desaparecen = int(por_episodio.all().sum())
    filas = [
        {"accion": "conservar", "efecto": "ningún cambio", "n_visitas": 0, "n_episodios_cambian": 0,
         "n_episodios_desaparecen": 0},
        {"accion": "marcar", "efecto": "columna booleana marca_<regla>", "n_visitas": n_visitas,
         "n_episodios_cambian": 0, "n_episodios_desaparecen": 0},
        {"accion": "nan", "efecto": ("pone en NaN: " + ", ".join(columnas_nan)) if columnas_nan else "no aplica",
         "n_visitas": n_visitas if columnas_nan else 0, "n_episodios_cambian": n_cambian if columnas_nan else 0,
         "n_episodios_desaparecen": 0},
        {"accion": "excluir", "efecto": "quita las visitas", "n_visitas": n_visitas,
         "n_episodios_cambian": n_cambian, "n_episodios_desaparecen": n_desaparecen},
    ]
    return pd.DataFrame(filas).set_index("accion")


# --- Reglas de episodio ----------------------------------------------------------------------------
def detectar_episodios(episodios: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Marcas booleanas por regla de ``REGLAS_EPISODIO`` sobre los episodios recibidos (normalmente,
    la población de análisis). Devuelve (marcas, límites usados).

    Hay una columna por regla; ``los_extremo`` tiene una por criterio (``los_extremo__p99`` y
    ``los_extremo__p99_9``), con los percentiles de cada grupo con tiempos.
    """
    e = episodios
    marcas = pd.DataFrame(index=e.index)
    usados = {"los_extremo": {}}
    for criterio in REGLAS_EPISODIO["los_extremo"]["criterios"]:
        marcas[f"los_extremo__{criterio}"] = False
    for grupo in (G2, G3):
        del_grupo = e["grupo"].eq(grupo)
        limites_grupo = limites(e.loc[del_grupo, "los_h"], REGLAS_EPISODIO["los_extremo"]["criterios"])
        usados["los_extremo"][grupo] = limites_grupo
        for criterio, limite in limites_grupo.items():
            columna = f"los_extremo__{criterio}"
            marcas[columna] = marcas[columna] | (del_grupo & e["los_h"].gt(limite))

    marcas["fin_fraccion_segundo"] = e["fin_fraccion_segundo"].eq(True)
    usados["muchas_visitas_en_episodio"] = limite_percentil(e["n_visitas"], "p99_9")
    marcas["muchas_visitas_en_episodio"] = e["n_visitas"].gt(usados["muchas_visitas_en_episodio"])
    marcas["los_recortado"] = e["los_recortado"].eq(True)
    hosp = e["grupo"].eq(G3)
    marcas["hosp_etapas_urg_despues_de_piso"] = hosp & e["fin_urg"].gt(e["inicio_piso"])

    # Contacto breve con LOS ≥ 5 min: solo ocurre al unir visitas sin etapas en un mismo episodio.
    marcas["contacto_breve_por_visitas_unidas"] = e["grupo"].eq(G1) & e["los_h"].ge(HORAS_CONTACTO_BREVE)
    marcas["hosp_sin_inicio_piso"] = hosp & e["inicio_piso"].isna()
    marcas["atencion_menos_5min"] = e["grupo"].eq(G2) & e["los_h"].lt(HORAS_CONTACTO_BREVE)
    marcas["fin_urg_antes_llegada"] = e["fin_urg"].lt(e["llegada"])

    episodios_paciente_anio = conteo_por_paciente_anio(e)
    usados["paciente_muchos_episodios"] = limite_percentil(episodios_paciente_anio, "p99_9")
    marcas["paciente_muchos_episodios"] = episodios_paciente_anio.gt(usados["paciente_muchos_episodios"])
    marcas["edad_nan"] = e["edad"].isna()
    return marcas, usados


def cifras_clave(episodios: pd.DataFrame, para_tiempos: pd.Series | None = None) -> dict:
    """Cifras clave de un conjunto de episodios: mediana del LOS de atención en urgencias y de
    hospitalizados, % de hospitalizados > 12 h, tamaño de cada grupo y reconsulta a 72 h (con
    censura). ``para_tiempos`` (booleano) limita los episodios que entran a los cálculos de LOS."""
    e = episodios
    tiempos = e if para_tiempos is None else e[para_tiempos.reindex(e.index, fill_value=True)]
    los_g2 = tiempos.loc[tiempos["grupo"].eq(G2), "los_h"].dropna()
    los_g3 = tiempos.loc[tiempos["grupo"].eq(G3), "los_h"].dropna()
    cifras = {
        "mediana_los_atencion_h": los_g2.median(),
        "mediana_los_hosp_h": los_g3.median(),
        f"pct_mas_{UMBRAL_OPERATIVO_H}h_hosp": 100 * los_g3.gt(UMBRAL_OPERATIVO_H).mean() if len(los_g3) else np.nan,
    }
    tamanos = e["grupo"].value_counts()
    for grupo in GRUPOS:
        cifras[f"n_{grupo}"] = int(tamanos.get(grupo, 0))
    cifras["pct_reconsulta_72h"] = 100 * e["reconsulta_72h"].dropna().astype(bool).mean()
    return cifras


def simular_opciones_episodio(episodios: pd.DataFrame, marca: pd.Series) -> pd.DataFrame:
    """Cifras clave con todos los episodios y simulando cada opción para una marca (sin aplicar nada):
    ``excluir`` (se quitan del dataset) y ``excluir_de_tiempos`` (siguen en el dataset, pero no
    entran a los cálculos de LOS). La reconsulta no se recalcula: se usa la ya calculada."""
    marca = marca.reindex(episodios.index, fill_value=False).astype(bool)
    filas = {
        "todos los episodios": cifras_clave(episodios),
        "excluir": cifras_clave(episodios[~marca]),
        "excluir_de_tiempos": cifras_clave(episodios, para_tiempos=~marca),
    }
    tabla = pd.DataFrame(filas).T.rename_axis("opcion")
    tabla.insert(0, "n_episodios_afectados", int(marca.sum()))
    return tabla


def aplicar_reglas_episodio(episodios: pd.DataFrame, marcas: pd.DataFrame,
                            reglas: dict = REGLAS_EPISODIO) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica las acciones de ``reglas`` a los episodios y devuelve (episodios, reporte agregado).

    - ``pendiente`` y ``conservar``: no cambian nada.
    - ``excluir_de_tiempos``: deja ``valido_para_tiempos = False`` en los episodios marcados.
    - ``excluir``: quita los episodios marcados.

    La columna booleana ``valido_para_tiempos`` siempre se crea (True si ninguna regla la cambia).
    """
    e = episodios.copy()
    if "valido_para_tiempos" not in e.columns:
        e["valido_para_tiempos"] = True
    filas = []
    for clave, regla in reglas.items():
        accion = regla["accion"]
        if accion not in ACCIONES_EPISODIO:
            raise ValueError(f"Acción desconocida '{accion}' en la regla '{clave}'. Opciones: {ACCIONES_EPISODIO}.")
        if accion in ("pendiente", "conservar"):
            filas.append({"regla": clave, "accion": accion, "n_afectados": 0})
            continue
        marca = _columna_marca(marcas, clave, regla).reindex(e.index, fill_value=False)
        if accion == "excluir_de_tiempos":
            e["valido_para_tiempos"] = e["valido_para_tiempos"] & ~marca
        elif accion == "excluir":
            e = e[~marca]
        filas.append({"regla": clave, "accion": accion, "n_afectados": int(marca.sum())})
    return e, pd.DataFrame(filas).set_index("regla")


def resumen_marcas(marcas: pd.DataFrame) -> pd.DataFrame:
    """Tabla agregada: total de filas y cuántas marca cada columna, con su porcentaje."""
    n = len(marcas)
    tabla = pd.DataFrame({"n": n, "n_afectados": marcas.sum().astype("int64")}, index=marcas.columns)
    tabla["pct_afectados"] = 100 * tabla["n_afectados"] / n if n else np.nan
    return tabla.rename_axis("marca")
