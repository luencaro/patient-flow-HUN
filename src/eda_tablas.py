"""Funciones de apoyo para el EDA por tablas (notebook 01).

Las consultas ``sql/01t_*_calidad.sql`` devuelven una sola fila con esta
convención de nombres, que ``perfil_calidad`` convierte en tablas largas:

- ``n_filas``: filas de la tabla.
- ``nulos__<columna>``: valores nulos de la columna.
- ``distintos__<columna>``: valores distintos de la columna.
- ``chequeo__<nombre>``: filas que cumplen una condición de calidad.
- ``rango__<nombre>``: un valor de referencia (mes o año), sin conteos.

La fila ancha tiene identificadores en el nombre de sus columnas (p. ej.,
``nulos__person_id``), así que nunca se muestra: solo se muestran las tablas largas.
"""

import re

import pandas as pd

from . import estilo
from .config import MIN_CELDA
from .privacidad import suprimir_pequenos, tabla_segura

# Orden de las categorías de conteo que devuelven las consultas 01t_*_por_visita y por paciente.
ORDEN_CONTEO = ["0", "1", "2", "3", "4-5", "6-9", "10+"]

# Columnas del diccionario oficial entregado por el hospital (revisar contra el documento).
# Las que no existen en la base se marcan como «falta en la base».
DICCIONARIO_COLUMNAS = {
    "person": [
        "person_id", "gender_concept_id", "year_of_birth", "race_concept_id", "ethnicity_concept_id",
    ],
    "visit_occurrence": [
        "visit_occurrence_id", "person_id", "visit_concept_id", "visit_start_datetime",
        "visit_end_datetime", "visit_type_concept_id", "provider_id", "preceding_visit_occurrence_id",
    ],
    "visit_detail": [
        "visit_detail_id", "visit_occurrence_id", "visit_detail_concept_id",
        "visit_detail_start_datetime", "visit_detail_end_datetime", "provider_id",
    ],
    "condition_occurrence": [
        "condition_occurrence_id", "person_id", "visit_occurrence_id", "condition_concept_id",
        "condition_start_datetime",
    ],
    "procedure_occurrence": [
        "procedure_occurrence_id", "person_id", "visit_occurrence_id", "procedure_concept_id",
        "procedure_datetime", "procedure_type_concept_id",
    ],
    "measurement": [
        "measurement_id", "person_id", "visit_occurrence_id", "measurement_concept_id",
        "measurement_datetime", "value_as_number", "unit_concept_id", "measurement_type_concept_id",
    ],
}


def comparar_columnas(columnas_reales: pd.DataFrame, tabla: str) -> pd.DataFrame:
    """Compara el diccionario con las columnas reales de ``tabla`` (de ``01t_columnas_reales``).

    Devuelve una fila por columna con ``tipo_dato`` y ``estado``: ``existe``,
    ``falta en la base`` o ``no está en el diccionario``.
    """
    reales = columnas_reales[columnas_reales["tabla"] == tabla].set_index("columna")["tipo_dato"]
    diccionario = DICCIONARIO_COLUMNAS.get(tabla, [])
    orden = list(reales.index) + [c for c in diccionario if c not in reales.index]
    filas = []
    for columna in orden:
        en_base = columna in reales.index
        en_diccionario = columna in diccionario
        if en_base and en_diccionario:
            estado = "existe"
        elif en_diccionario:
            estado = "falta en la base"
        else:
            estado = "no está en el diccionario"
        filas.append(
            {"columna": columna, "tipo_dato": reales.get(columna, "—"), "estado": estado}
        )
    return pd.DataFrame(filas).set_index("columna")


def perfil_calidad(fila: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convierte la fila ancha de ``01t_*_calidad`` en tres tablas largas agregadas.

    - ``columnas``: por columna, ``n`` (filas), ``n_nulos``, ``pct_nulos``,
      ``valores_distintos`` (si se calculó) y ``constante`` (``sí`` si tiene un solo valor).
    - ``chequeos``: por chequeo, ``n`` (filas), ``n_casos`` y ``pct_casos``.
    - ``rango``: valores de referencia como texto.
    """
    if len(fila) != 1:
        raise ValueError("La consulta de calidad debe devolver exactamente una fila.")
    registro = fila.iloc[0]
    n_filas = int(registro["n_filas"])

    def _con_prefijo(prefijo: str) -> pd.Series:
        columnas = [c for c in registro.index if str(c).startswith(prefijo)]
        return pd.Series(
            [registro[c] for c in columnas], index=[str(c)[len(prefijo):] for c in columnas], dtype=object
        )

    nulos = pd.to_numeric(_con_prefijo("nulos__"))
    distintos = pd.to_numeric(_con_prefijo("distintos__")).reindex(nulos.index)
    columnas = pd.DataFrame({"n": n_filas, "n_nulos": nulos.astype("int64")})
    columnas["pct_nulos"] = 100 * columnas["n_nulos"] / n_filas if n_filas else float("nan")
    columnas["valores_distintos"] = distintos
    constante = distintos.eq(1) | nulos.eq(n_filas)
    columnas["constante"] = constante.map({True: "sí", False: "no"})
    columnas.index.name = "columna"

    casos = pd.to_numeric(_con_prefijo("chequeo__"))
    chequeos = pd.DataFrame({"n": n_filas, "n_casos": casos.astype("int64")})
    chequeos["pct_casos"] = 100 * chequeos["n_casos"] / n_filas if n_filas else float("nan")
    chequeos.index.name = "chequeo"

    rango = _con_prefijo("rango__").astype(str).rename("valor").rename_axis("medida").to_frame()
    return {"columnas": columnas, "chequeos": chequeos, "rango": rango}


def agregar_porcentaje(tabla: pd.DataFrame, columna: str, por: list | str | None = None) -> pd.DataFrame:
    """Agrega ``pct_<sufijo>`` = 100 · ``columna`` / total (o total dentro de cada grupo de ``por``).

    ``columna`` debe seguir la convención ``n_<sufijo>`` para que ``suprimir_pequenos``
    asocie el porcentaje a su conteo.
    """
    if not columna.startswith("n_"):
        raise ValueError("La columna de conteo debe empezar por 'n_'.")
    t = tabla.copy()
    if por is None:
        total = t[columna].sum()
    else:
        por = [por] if isinstance(por, str) else list(por)
        total = t.groupby(por)[columna].transform("sum")
    t[f"pct_{columna[2:]}"] = 100 * t[columna] / total
    return t


def calidad_segura(fila: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """``perfil_calidad`` con redondeo y supresión, listo para mostrar.

    Los ceros se conservan (``0`` nulos no identifica a nadie); los demás conteos
    menores a ``MIN_CELDA`` se muestran como ``"<10"``.
    """
    perfil = perfil_calidad(fila)
    return {
        "columnas": tabla_segura(perfil["columnas"], conservar_ceros=True),
        "chequeos": tabla_segura(perfil["chequeos"], conservar_ceros=True),
        "rango": suprimir_pequenos(perfil["rango"], []),
    }


# --- Traducciones para mostrar ---------------------------------------------------------------
def nombre_sexo(valor) -> str:
    """``FEMALE`` → Femenino, ``MALE`` → Masculino, ``No matching concept`` → Sin dato."""
    return estilo.NOMBRE_SEXO.get(str(valor), str(valor))


def nombre_raza_etnia(valor) -> str:
    return estilo.NOMBRE_RAZA_ETNIA.get(str(valor), str(valor))


def _concepto(concepto=None, nombre=None):
    if concepto is not None and not pd.isna(concepto):
        return int(concepto)
    return estilo.CONCEPTO_POR_NOMBRE.get(str(nombre))


def nombre_tipo_visita(concepto=None, nombre=None) -> str:
    """Tipo de visita en español con su código, p. ej. «Urgencias (9203)». Si no está en el
    diccionario de ``estilo``, devuelve el nombre de ``concept`` con el código."""
    c = _concepto(concepto, nombre)
    if c in estilo.NOMBRE_TIPO_VISITA:
        return f"{estilo.NOMBRE_TIPO_VISITA[c]} ({c})"
    return f"{nombre} ({c})" if c is not None else str(nombre)


def nombre_etapa(concepto=None, nombre=None) -> str:
    """Tipo de etapa en español con su código, p. ej. «Ingreso por urgencias (9203)»."""
    c = _concepto(concepto, nombre)
    if c in estilo.NOMBRE_ETAPA:
        return f"{estilo.NOMBRE_ETAPA[c]} ({c})"
    return f"{nombre} ({c})" if c is not None else str(nombre)


def es_urgencias(etiqueta) -> bool:
    return "(9203)" in str(etiqueta)


def concepto_de_etiqueta(etiqueta):
    """Código de concepto al final de una etiqueta como «Urgencias (9203)», o ``None``."""
    coincidencia = re.search(r"\((\d+)\)\s*$", str(etiqueta))
    return int(coincidencia.group(1)) if coincidencia else None


def colores_tipo_visita(etiquetas) -> list:
    """Color de cada tipo de visita según su familia (urgencias azul, ambulatorio ocre,
    hospitalización ciruela, 3045729 azul claro); los demás tipos en gris."""
    return [estilo.color_tipo_visita(concepto_de_etiqueta(e)) for e in etiquetas]


def linea_tipo_visita(etiqueta) -> str:
    """Estilo de línea del tipo de visita: discontinua para 3045729, continua para el resto."""
    return estilo.LINEA_TIPO_VISITA.get(concepto_de_etiqueta(etiqueta), "-")


def familias_tipo_visita(etiquetas) -> list:
    return [estilo.familia_de_tipo_visita(concepto_de_etiqueta(e)) for e in etiquetas]


# --- Magnitudes de los hallazgos (texto construido desde los datos) ---------------------------
def magnitud(casos, total) -> str:
    """«53,1 % (1.234 de 2.325)»; si los casos son 1–9, «<10 casos»; si son 0, «0 casos»."""
    casos, total = float(casos), float(total)
    if casos == 0:
        return "0 casos"
    if casos < MIN_CELDA:
        return f"<{MIN_CELDA} casos"
    return f"{estilo.fmt_pct(100 * casos / total)} ({estilo.fmt_entero(casos)} de {estilo.fmt_entero(total)})"


# --- Tablas del EDA ---------------------------------------------------------------------------
TABLAS_EDA = ("person", "visit_occurrence", "visit_detail", "condition_occurrence", "procedure_occurrence",
              "measurement")


def categorizar_conteos(frecuencias: pd.DataFrame, columna_k: str = "k", columna_n: str = "n_visitas") -> pd.Series:
    """Agrupa una tabla de frecuencias exactas (k, n) en las categorías de ``ORDEN_CONTEO``."""
    etiquetas = ORDEN_CONTEO
    bordes = [-0.5, 0.5, 1.5, 2.5, 3.5, 5.5, 9.5, float("inf")]
    categoria = pd.cut(frecuencias[columna_k], bins=bordes, labels=etiquetas)
    return frecuencias.groupby(categoria, observed=False)[columna_n].sum()


# --- Ficha del dataset: info() y describe() desde SQL -----------------------------------------
# Columna que ordena el head() de cada tabla.
ID_TABLA = {
    "person": "person_id",
    "visit_occurrence": "visit_occurrence_id",
    "visit_detail": "visit_detail_id",
    "condition_occurrence": "condition_occurrence_id",
    "procedure_occurrence": "procedure_occurrence_id",
    "measurement": "measurement_id",
}
ESTADISTICOS_DESCRIBE = {"count": "count", "mean": "mean", "std": "std", "min": "min", "p25": "25%",
                         "p50": "50%", "p75": "75%", "max": "max"}


def info_tabla(faltantes: pd.DataFrame, columnas_reales: pd.DataFrame, tabla: str) -> tuple[pd.DataFrame, int]:
    """Equivalente a ``df.info()`` calculado en SQL sobre la tabla completa.

    Devuelve (tabla, número de filas). Columnas: columna, tipo de dato, no nulos, nulos,
    % nulos y valores distintos. Los conteos de 1 a 9 se muestran como «<10».
    """
    f = faltantes[faltantes["tabla"] == tabla].sort_values("posicion")
    tipos = columnas_reales[columnas_reales["tabla"] == tabla].set_index("columna")["tipo_dato"]
    n_filas = int(f["n"].iloc[0]) if len(f) else 0
    info = pd.DataFrame({
        "columna": f["columna"].to_numpy(),
        "tipo_dato": [tipos.get(c, "—") for c in f["columna"]],
        "n_no_nulos": (f["n"] - f["n_nulos"]).to_numpy(),
        "n_nulos": f["n_nulos"].to_numpy(),
        "pct_nulos": (100 * f["n_nulos"] / f["n"]).to_numpy(),
        "valores_distintos": f["valores_distintos"].to_numpy(),
    })
    info = suprimir_pequenos(info, ["n_no_nulos", "n_nulos"], columnas_derivadas=["pct_nulos"],
                             dependencias={"pct_nulos": ["n_nulos"]}, conservar_ceros=True)
    info = info.rename(columns={"tipo_dato": "tipo de dato", "n_no_nulos": "no nulos", "n_nulos": "nulos",
                                "pct_nulos": "% nulos", "valores_distintos": "valores distintos"})
    return info, n_filas


def pct_faltantes(faltantes: pd.DataFrame, tabla: str) -> pd.DataFrame:
    """% nulo y % sin información (concepto 0, o el resto de la columna si es constante) por
    columna, para ``graficos.barras_faltantes``."""
    f = faltantes[faltantes["tabla"] == tabla].set_index("columna")
    pct_nulos = 100 * f["n_nulos"] / f["n"]
    pct_cero = 100 * pd.to_numeric(f["n_concepto_0"]).fillna(0) / f["n"]
    constante = f["es_constante"].eq(True)
    pct_sin_info = pct_cero.where(~constante, 100 - pct_nulos)
    return pd.DataFrame({"pct_nulos": pct_nulos, "pct_sin_informacion": pct_sin_info})


def _conteo_texto(v) -> str:
    """Conteo como texto con separador de miles (las filas de conteo comparten columna con
    valores de otro tipo); de 1 a 9, «<10»."""
    if v is None or pd.isna(v):
        return ""
    v = float(v)
    return f"<{MIN_CELDA}" if 0 < v < MIN_CELDA else estilo.fmt_entero(v)


def describe_desde_fila(fila: pd.DataFrame) -> pd.DataFrame:
    """Tabla con el formato de ``df.describe()`` (estadísticos en filas, columnas en columnas) a
    partir de la fila ancha de ``01t_<tabla>_describe`` (alias ``<estadístico>__<columna>``).
    Los conteos de 1 a 9 se muestran como «<10»."""
    registro = fila.iloc[0]
    columnas = list(dict.fromkeys(str(c).split("__", 1)[1] for c in registro.index if "__" in str(c)))
    tabla = pd.DataFrame(index=list(ESTADISTICOS_DESCRIBE.values()), columns=columnas, dtype=object)
    for alias, valor in registro.items():
        estadistico, columna = str(alias).split("__", 1)
        tabla.loc[ESTADISTICOS_DESCRIBE[estadistico], columna] = valor
    tabla = tabla.dropna(how="all")
    if "count" in tabla.index:
        tabla.loc["count"] = [_conteo_texto(v) for v in tabla.loc["count"]]
    return tabla.rename_axis("estadístico")


def describe_categorico(resumen: pd.DataFrame) -> pd.DataFrame:
    """Formato de ``df.describe()`` para categóricas (count, unique, top, freq) a partir de
    ``01t_<tabla>_describe_cat`` (una fila por columna)."""
    tabla = resumen.set_index("columna")[["count", "unique", "top", "freq"]].T.astype(object)
    for estadistico in ("count", "unique", "freq"):
        tabla.loc[estadistico] = [_conteo_texto(v) for v in tabla.loc[estadistico]]
    return tabla.rename_axis("estadístico")
