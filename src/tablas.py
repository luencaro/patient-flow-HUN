"""Presentación de tablas en los notebooks, en lugar de ``print``.

Las tablas se muestran con el ``display`` por defecto de pandas, con un título opcional
arriba. No se aplica ningún estilo ni formato: los datos se ven tal como son.
"""

import pandas as pd
from IPython.display import Markdown, display


def mostrar_tabla(df: pd.DataFrame, titulo: str | None = None) -> None:
    """Muestra ``df`` con el ``display`` por defecto de pandas y, si se da, un título arriba."""
    if titulo:
        display(Markdown(f"**{titulo}**"))
    display(df)


def tabla_medidas(medidas: dict, titulo: str | None = None) -> None:
    """Muestra un dato suelto (totales, rangos, conteos) como tabla de dos columnas
    (medida, valor), en lugar de ``print``."""
    mostrar_tabla(pd.DataFrame({"medida": list(medidas.keys()), "valor": list(medidas.values())}), titulo)
