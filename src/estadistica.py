"""Resúmenes estadísticos agregados: intervalos de Wilson y tablas de LOS y proporciones."""

from statistics import NormalDist

import numpy as np
import pandas as pd

from .config import UMBRALES_LOS_H


def ic_wilson(exitos, n, confianza: float = 0.95) -> tuple[np.ndarray, np.ndarray]:
    """Intervalo de confianza de Wilson para proporciones (en escala 0–1).

    Acepta escalares o arreglos. Donde ``n`` es 0 devuelve ``NaN``.
    """
    exitos = np.asarray(exitos, dtype=float)
    n = np.asarray(n, dtype=float)
    z = NormalDist().inv_cdf(0.5 + confianza / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = exitos / n
        denominador = 1 + z**2 / n
        centro = (p + z**2 / (2 * n)) / denominador
        margen = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominador
    inferior = np.where(n > 0, np.clip(centro - margen, 0, 1), np.nan)
    superior = np.where(n > 0, np.clip(centro + margen, 0, 1), np.nan)
    return inferior, superior


def _como_lista(por) -> list:
    lista = [por] if isinstance(por, str) else list(por)
    if not lista:
        raise ValueError("Indica al menos una columna en 'por' (usa una columna constante para el total).")
    return lista


def tabla_proporciones(
    df: pd.DataFrame, por, columna: str, confianza: float = 0.95
) -> pd.DataFrame:
    """Proporción de ``columna`` (booleana, nulos excluidos) por grupo, con IC de Wilson en %.

    Columnas: ``n``, ``n_eventos``, ``pct_eventos``, ``ic_inf_eventos``, ``ic_sup_eventos``.
    """
    por = _como_lista(por)
    datos = df.loc[df[columna].notna(), por + [columna]]
    claves = [datos[c] for c in por]
    eventos = datos[columna].astype(bool).groupby(claves, observed=True, dropna=False)
    tabla = pd.DataFrame({"n": eventos.size(), "n_eventos": eventos.sum().astype("int64")})
    tabla["pct_eventos"] = 100 * tabla["n_eventos"] / tabla["n"]
    inferior, superior = ic_wilson(tabla["n_eventos"].to_numpy(), tabla["n"].to_numpy(), confianza)
    tabla["ic_inf_eventos"] = 100 * inferior
    tabla["ic_sup_eventos"] = 100 * superior
    return tabla


def tabla_los(
    df: pd.DataFrame,
    por,
    columna: str = "los_h",
    umbrales: list = UMBRALES_LOS_H,
    confianza: float = 0.95,
) -> pd.DataFrame:
    """Resumen del LOS por grupo: n, mediana, p25, p75, p90 y % por encima de cada umbral.

    Los porcentajes llevan IC de Wilson (en %). Las filas con LOS nulo se excluyen.
    """
    por = _como_lista(por)
    datos = df.loc[df[columna].notna(), por + [columna]]
    claves = [datos[c] for c in por]
    valores = datos[columna].astype(float)
    grupos = valores.groupby(claves, observed=True, dropna=False)

    tabla = pd.DataFrame(
        {
            "n": grupos.size(),
            "mediana_h": grupos.median(),
            "p25_h": grupos.quantile(0.25),
            "p75_h": grupos.quantile(0.75),
            "p90_h": grupos.quantile(0.90),
        }
    )
    for umbral in umbrales:
        sufijo = f"mas_{umbral}h"
        eventos = (
            (valores > umbral)
            .groupby(claves, observed=True, dropna=False)
            .sum()
            .reindex(tabla.index)
            .astype("int64")
        )
        tabla[f"n_{sufijo}"] = eventos
        tabla[f"pct_{sufijo}"] = 100 * eventos / tabla["n"]
        inferior, superior = ic_wilson(eventos.to_numpy(), tabla["n"].to_numpy(), confianza)
        tabla[f"ic_inf_{sufijo}"] = 100 * inferior
        tabla[f"ic_sup_{sufijo}"] = 100 * superior
    return tabla


def ecdf_en_malla(valores: pd.Series, malla: np.ndarray) -> np.ndarray:
    """ECDF evaluada en una malla fija (no expone observaciones individuales)."""
    ordenados = np.sort(np.asarray(valores.dropna(), dtype=float))
    if ordenados.size == 0:
        return np.full(len(malla), np.nan)
    return np.searchsorted(ordenados, malla, side="right") / ordenados.size
