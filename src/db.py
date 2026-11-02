"""Conexión a PostgreSQL y lectura de consultas con caché en parquet."""

import hashlib
import os
import warnings
from functools import lru_cache

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

from .config import DATA_RAW, RAIZ, SCHEMA, SQL_DIR

VARIABLES_CONEXION = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
MODOS_VALIDOS = ("remote", "local")


def _cargar_entorno() -> None:
    """Carga ``.env`` desde la raíz del proyecto sin sobrescribir variables ya definidas."""
    load_dotenv(RAIZ / ".env")


def _valor_entorno(nombre: str, quitar_comentario: bool = False) -> str | None:
    """Devuelve la variable sin espacios, o ``None`` si está vacía.

    ``quitar_comentario`` elimina un comentario en línea (`` # ...``); no se usa
    con credenciales para no alterar contraseñas que contengan ``#``.
    """
    valor = os.getenv(nombre)
    if valor is None:
        return None
    if quitar_comentario:
        valor = valor.split(" #")[0]
    valor = valor.strip()
    return valor or None


def modo_datos() -> str:
    """Lee ``DATA_MODE`` (``remote`` o ``local``). Si no está definida, usa ``local``."""
    _cargar_entorno()
    modo = (_valor_entorno("DATA_MODE", quitar_comentario=True) or "local").lower()
    if modo not in MODOS_VALIDOS:
        raise ValueError("DATA_MODE debe ser 'remote' o 'local'.")
    return modo


@lru_cache(maxsize=1)
def obtener_engine() -> Engine:
    """Crea el engine de SQLAlchemy (driver ``postgresql+psycopg``) desde el entorno.

    Lanza un error que nombra las variables faltantes, sin mostrar ningún valor.
    """
    _cargar_entorno()
    valores = {nombre: _valor_entorno(nombre) for nombre in VARIABLES_CONEXION}
    faltantes = [nombre for nombre, valor in valores.items() if valor is None]
    if faltantes:
        raise OSError(
            "Faltan variables de entorno para conectarse: "
            + ", ".join(faltantes)
            + ". Complétalas en el archivo .env (ver .env.example)."
        )
    try:
        puerto = int(valores["DB_PORT"])
    except ValueError:
        raise ValueError("DB_PORT debe ser un número entero.") from None

    url = URL.create(
        drivername="postgresql+psycopg",
        username=valores["DB_USER"],
        password=valores["DB_PASSWORD"],
        host=valores["DB_HOST"],
        port=puerto,
        database=valores["DB_NAME"],
    )
    # hide_parameters evita que los parámetros aparezcan en mensajes de error o logs.
    return create_engine(url, pool_pre_ping=True, hide_parameters=True)


def ruta_sql(nombre: str):
    """Ruta del archivo ``sql/{nombre}.sql``."""
    ruta = SQL_DIR / f"{nombre}.sql"
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo sql/{nombre}.sql.")
    return ruta


def cargar_sql(nombre: str) -> str:
    """Lee ``sql/{nombre}.sql`` y reemplaza el marcador ``{schema}`` por ``SCHEMA``."""
    return ruta_sql(nombre).read_text(encoding="utf-8").replace("{schema}", SCHEMA)


def hash_sql(nombre: str) -> str:
    """Hash SHA-256 del archivo SQL (sin reemplazar el esquema), para versionar extracciones."""
    return hashlib.sha256(ruta_sql(nombre).read_bytes()).hexdigest()


def consultar(nombre: str, refrescar: bool = False) -> pd.DataFrame:
    """Devuelve el resultado de ``sql/{nombre}.sql`` usando caché en ``data/raw/{nombre}.parquet``.

    - Si el parquet existe y ``refrescar=False``, se lee sin consultar la base.
    - ``DATA_MODE=remote``: ejecuta la consulta, guarda el parquet y lo devuelve.
    - ``DATA_MODE=local``: solo lee el parquet; si no existe, lanza un error.
    """
    ruta_cache = DATA_RAW / f"{nombre}.parquet"
    if ruta_cache.exists() and not refrescar:
        return pd.read_parquet(ruta_cache)

    if modo_datos() == "local":
        if ruta_cache.exists():
            warnings.warn("refrescar=True se ignora en modo local; se usa el parquet existente.")
            return pd.read_parquet(ruta_cache)
        raise FileNotFoundError(
            f"No existe data/raw/{nombre}.parquet. Ejecuta primero con DATA_MODE=remote "
            "(conectado a la VPN del hospital) para generarlo."
        )

    consulta = text(cargar_sql(nombre))
    with obtener_engine().connect() as conexion:
        # coerce_float convierte los NUMERIC de Postgres (Decimal) a float.
        resultado = pd.read_sql_query(consulta, conexion, coerce_float=True)

    ruta_cache.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_parquet(ruta_cache, index=False)
    return resultado
