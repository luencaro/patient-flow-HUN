"""Controles de privacidad para tablas que se muestran o exportan.

Convención de nombres que usa ``suprimir_pequenos`` para saber qué columnas
dependen de qué conteos:

- Columnas de conteo: ``n`` (denominador) o ``n_<sufijo>`` (numeradores).
- Una columna derivada que termina en ``_<sufijo>`` (por ejemplo ``pct_mas_12h``)
  depende de ``n`` y de ``n_<sufijo>`` (``n_mas_12h``).
- Una columna derivada sin sufijo reconocible (por ejemplo ``mediana_h``) depende
  solo de ``n``; si la tabla no tiene ``n``, depende de todos los conteos.

Las etiquetas (hora, mes, grupo, etc.) deben ir en el índice o ser texto, para
que no se confundan con columnas derivadas.
"""

import pandas as pd

from .config import MIN_CELDA

COLUMNAS_PROHIBIDAS = ("person_id", "visit_occurrence_id", "visit_detail_id", "episodio_id")
TEXTO_SUPRIMIDO = "suprimido"


def verificar_agregada(tabla: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Lanza un error si la tabla tiene columnas o índices con identificadores.

    Devuelve la misma tabla para poder encadenar la llamada.
    """
    if isinstance(tabla, pd.Series):
        nombres = [tabla.name, *tabla.index.names]
    else:
        nombres = [*tabla.columns, *tabla.index.names, *tabla.columns.names]
    prohibidas = sorted(
        {str(n) for n in nombres if n is not None and any(p in str(n).lower() for p in COLUMNAS_PROHIBIDAS)}
    )
    if prohibidas:
        raise ValueError(
            "La tabla no es agregada: contiene identificadores en " + ", ".join(prohibidas) + "."
        )
    return tabla


def columnas_de_conteo(tabla: pd.DataFrame) -> list[str]:
    """Columnas que siguen la convención de conteo (``n`` o ``n_*``)."""
    return [c for c in tabla.columns if isinstance(c, str) and (c == "n" or c.startswith("n_"))]


def _inferir_dependencias(derivadas: list, conteos: list) -> dict:
    """Asigna a cada columna derivada los conteos de los que depende (ver docstring del módulo)."""
    sufijos = {c[2:]: c for c in conteos if isinstance(c, str) and c.startswith("n_")}
    base = ["n"] if "n" in conteos else []
    dependencias = {}
    for columna in derivadas:
        ligadas = [c for sufijo, c in sufijos.items() if str(columna).endswith("_" + sufijo)]
        dependencias[columna] = (base + ligadas) if (base or ligadas) else list(conteos)
    return dependencias


def suprimir_pequenos(
    tabla: pd.DataFrame,
    columnas_conteo: list | str,
    minimo: int = MIN_CELDA,
    columnas_derivadas: list | None = None,
    dependencias: dict | None = None,
    conservar_ceros: bool = False,
) -> pd.DataFrame:
    """Devuelve una copia con los conteos menores a ``minimo`` reemplazados por ``"<minimo>"``.

    Las columnas derivadas (porcentajes, medianas, intervalos) que dependen de un
    conteo suprimido en la misma fila se reemplazan por ``"suprimido"``.

    Parámetros
    ----------
    tabla:
        Tabla agregada. Se verifica con ``verificar_agregada``.
    columnas_conteo:
        Columnas que contienen conteos de personas, visitas o episodios.
    minimo:
        Conteo mínimo publicable (por defecto ``MIN_CELDA``).
    columnas_derivadas:
        Columnas calculadas sobre los conteos. Por defecto, todas las columnas
        numéricas que no son conteos.
    dependencias:
        Diccionario ``{columna_derivada: [conteos]}`` que reemplaza la inferencia
        por nombres.
    conservar_ceros:
        Si es ``True``, los conteos iguales a 0 se muestran tal cual (un cero no
        identifica a nadie). Útil en tablas de calidad (p. ej., número de nulos).
    """
    verificar_agregada(tabla)
    if isinstance(columnas_conteo, str):
        columnas_conteo = [columnas_conteo]
    columnas_conteo = list(columnas_conteo)
    faltantes = [c for c in columnas_conteo if c not in tabla.columns]
    if faltantes:
        raise KeyError(f"Columnas de conteo inexistentes: {faltantes}")

    if columnas_derivadas is None:
        columnas_derivadas = [
            c
            for c in tabla.columns
            if c not in columnas_conteo and pd.api.types.is_numeric_dtype(tabla[c])
        ]
    if dependencias is None:
        dependencias = _inferir_dependencias(list(columnas_derivadas), columnas_conteo)

    salida = tabla.copy()
    conteos = tabla[columnas_conteo].apply(pd.to_numeric, errors="coerce")
    pequenos = conteos.lt(minimo)  # los nulos no se marcan
    if conservar_ceros:
        pequenos &= conteos.ne(0)
    etiqueta = f"<{minimo}"

    for columna in columnas_derivadas:
        ligadas = [c for c in dependencias.get(columna, columnas_conteo) if c in pequenos.columns]
        if not ligadas:
            continue
        mascara = pequenos[ligadas].any(axis=1)
        if mascara.any():
            salida[columna] = salida[columna].astype(object)
            salida.loc[mascara, columna] = TEXTO_SUPRIMIDO

    for columna in columnas_conteo:
        mascara = pequenos[columna]
        if mascara.any():
            salida[columna] = salida[columna].astype(object)
            salida.loc[mascara, columna] = etiqueta

    return salida


def tabla_segura(tabla: pd.DataFrame, decimales: int = 2, **kwargs) -> pd.DataFrame:
    """Redondea y suprime usando la convención de nombres (``n`` / ``n_*``) para los conteos."""
    return suprimir_pequenos(tabla.round(decimales), columnas_de_conteo(tabla), **kwargs)


def enmascarar_pequenos(valores: pd.DataFrame | pd.Series, conteos, minimo: int = MIN_CELDA):
    """Para gráficos: deja en ``NaN`` los valores cuyo conteo asociado es menor a ``minimo``."""
    return valores.where(conteos >= minimo)
