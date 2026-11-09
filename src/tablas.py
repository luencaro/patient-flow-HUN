"""Presentación de tablas en los notebooks, en lugar de ``print``.

Las tablas se muestran con el ``display`` por defecto de pandas, sin estilos, con un título
opcional arriba. Los números se muestran en formato colombiano (miles con punto, decimales con
coma, sin notación científica) con ``graficos.formatear_tabla``; los datos no se modifican.
"""

import pandas as pd
from IPython.display import Markdown, display

from .graficos import formatear_tabla


def mostrar_tabla(df: pd.DataFrame, titulo: str | None = None) -> None:
    """Muestra ``df`` con el ``display`` por defecto de pandas y, si se da, un título arriba."""
    if titulo:
        display(Markdown(f"**{titulo}**"))
    display(formatear_tabla(df.to_frame() if isinstance(df, pd.Series) else df))


def tabla_medidas(medidas: dict, titulo: str | None = None) -> None:
    """Muestra un dato suelto (totales, rangos, conteos) como tabla de dos columnas
    (medida, valor), en lugar de ``print``."""
    mostrar_tabla(pd.DataFrame({"medida": list(medidas.keys()), "valor": list(medidas.values())}), titulo)
