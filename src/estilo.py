"""Sistema visual del proyecto: fuente única de colores, tipografía y formato de números.

Lo usan el EDA (matplotlib, a través de ``src/graficos.py``) y, más adelante, el
dashboard en Dash. Por eso este módulo solo tiene constantes y funciones puras:
se puede importar sin matplotlib. Las funciones que devuelven colormaps importan
matplotlib dentro de la función.

Principio central: cada color tiene un solo significado en todo el proyecto. Los
subgrupos (sexo, edad, diagnóstico) no reciben colores nuevos: heredan la familia
del grupo al que pertenecen.
"""

import math
from datetime import date, datetime

# --- Roles de paciente (grupos de análisis) -------------------------------------------
ROL_CONTACTO = "1_contacto_breve"
ROL_ATENCION = "2_atencion_urgencias"
ROL_HOSPITALIZADO = "3_hospitalizado"
ROLES = (ROL_CONTACTO, ROL_ATENCION, ROL_HOSPITALIZADO)

# --- Cuatro familias de color, cada una con un significado fijo ---------------------------------
# Validadas juntas para daltonismo y con contraste >= 3:1 sobre blanco.
AZUL = "#2a78d6"  # urgencias: visitas 9203, etapa 3045729, atención en urgencias
CIRUELA = "#9b2f6e"  # hospitalización: etapa y visitas 9201, hospitalizados
OCRE = "#c98500"  # ambulatorio: visitas y etapas 581479
VERDE = "#159a8c"  # general (verde azulado): base completa o variables sin rol
GRIS_CONTEXTO = "#898781"  # contacto breve (contexto)

# Rampas completas de claro a oscuro (para heatmaps y rellenos de cajas).
RAMPA_AZUL = ("#e3eefc", "#cde2fb", "#9ec5f4", "#6da7ec", "#2a78d6", "#184f95", "#0d366b")
RAMPA_CIRUELA = ("#f6e6ef", "#ecc9dc", "#dc9fc1", "#c672a2", "#9b2f6e", "#7a2457", "#561a3d")
RAMPA_OCRE = ("#f8eddf", "#edd3b3", "#dcae71", "#c98500", "#a36500", "#874a00", "#6b3100")
RAMPA_VERDE = ("#e5f2ef", "#c0dfda", "#8bc5bb", "#50aa9e", "#159a8c", "#006c60", "#005248")
# Gris solo para contexto o ausencia de dato: "Otros", "Sin dato", concepto 0, columnas constantes,
# eventos previos, contacto breve, etiquetas y ejes. De oscuro a claro.
GRISES = ("#52514e", "#898781", "#c3c2b7")
RAMPA_GRIS = ("#ffffff", "#ecebe5", "#c3c2b7", "#a5a39b", "#898781", "#6d6c68", "#52514e")

# --- Semáforo: reservado para la página de alerta del dashboard. NO se usa en el EDA. ---
SEMAFORO = {"normal": "#2f9e44", "atencion": "#fab219", "alto": "#ec835a", "critico": "#d03b3b"}

# --- Neutros --------------------------------------------------------------------------
FONDO_FIGURA = "#ffffff"
FONDO_PAGINA = "#f6f5f1"
BORDE = "#ecebe5"  # bordes y cuadrícula
EJES = "#898781"  # ejes y marcas
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"

# --- Tipografía -------------------------------------------------------------------------
FUENTES = ["Inter", "Segoe UI", "DejaVu Sans", "sans-serif"]
TAMANO_TITULO = 15
TAMANO_SUBTITULO = 11
TAMANO_EJES = 10
TAMANO_NOTA = 9
TAMANO_MINIMO = 9

# --- Mapeos por rol -------------------------------------------------------------------
COLOR_ROL = {ROL_CONTACTO: GRIS_CONTEXTO, ROL_ATENCION: AZUL, ROL_HOSPITALIZADO: CIRUELA}
ETIQUETA_ROL = {
    ROL_CONTACTO: "1. Contacto breve (< 5 min o sin etapas)",
    ROL_ATENCION: "2. Atención en urgencias (no hospitalizado)",
    ROL_HOSPITALIZADO: "3. Hospitalizado",
}
ETIQUETA_CORTA_ROL = {
    ROL_CONTACTO: "Contacto breve",
    ROL_ATENCION: "Atención en urgencias",
    ROL_HOSPITALIZADO: "Hospitalizado",
}
GROSOR_ROL = {ROL_CONTACTO: 2.0, ROL_ATENCION: 2.0, ROL_HOSPITALIZADO: 3.0}  # foco más grueso
NEGRITA_ROL = {ROL_CONTACTO: False, ROL_ATENCION: False, ROL_HOSPITALIZADO: True}
FAMILIA_ROL = {ROL_CONTACTO: "gris", ROL_ATENCION: "urgencias", ROL_HOSPITALIZADO: "hospitalizacion"}

# Sexo: Femenino oscuro y relleno, Masculino claro en anillo (o con borde), dentro de la familia.
SEXO_POR_FAMILIA = {
    "urgencias": {"femenino": "#184f95", "masculino": "#6da7ec"},
    "hospitalizacion": {"femenino": "#7a2457", "masculino": "#c672a2"},
    "general": {"femenino": "#006c60", "masculino": "#50aa9e"},
    "gris": {"femenino": GRISES[0], "masculino": GRISES[1]},
}
RELLENO_SEXO = {"femenino": True, "masculino": False}

# --- Colores por variable del EDA -----------------------------------------------------
COLOR_TOP_TABLA = VERDE  # top-N de la tabla completa (notebook 01)
COLOR_OTROS = GRISES[2]  # categoría "Otros (n)"
COLOR_DATO_VALIDO = VERDE
COLOR_SIN_DATO = GRISES[2]  # siempre con relleno rayado; nunca rojo
COLOR_ETAPA = {9203: "#184f95", 3045729: AZUL, 9201: CIRUELA, 581479: OCRE}
COLOR_EVENTO_PREVIO = GRISES[1]
# Tipo de visita: cada tipo con su familia; 3045729 en azul claro con línea discontinua.
COLOR_TIPO_VISITA = {9203: AZUL, 581479: OCRE, 9201: CIRUELA, 3045729: "#6da7ec", 0: GRISES[2]}
LINEA_TIPO_VISITA = {3045729: "--"}
COLOR_VOCABULARIO = {"SNOMED": "#159a8c", "LOINC": "#50aa9e", "ICD10CM": "#006c60"}

# --- Textos en español de conjuntos pequeños y fijos ---------------------------------------
NOMBRE_SEXO = {
    "FEMALE": "Femenino",
    "MALE": "Masculino",
    "No matching concept": "Sin dato",
    "(sin concepto)": "Sin dato",
    "femenino": "Femenino",
    "masculino": "Masculino",
    "otro_o_sin_dato": "Otro o sin dato",
}
NOMBRE_RAZA_ETNIA = {
    "No matching concept": "Sin dato",
    "(sin concepto)": "Sin dato",
    "White": "Blanca",
    "Black or African American": "Negra o afrodescendiente",
    "Black": "Negra",
    "Asian": "Asiática",
    "American Indian or Alaska Native": "Indígena americana",
    "Native Hawaiian or Other Pacific Islander": "Isleña del Pacífico",
    "Other Race": "Otra",
    "Unknown": "Desconocida",
    "Hispanic or Latino": "Hispana o latina",
    "Not Hispanic or Latino": "No hispana ni latina",
}
NOMBRE_TIPO_VISITA = {
    9203: "Urgencias",
    581479: "Consulta externa",
    9201: "Hospitalización",
    3045729: "Tratamiento urgente",
}
NOMBRE_ETAPA = {
    9203: "Ingreso por urgencias",
    3045729: "Movimiento o etapa",
    9201: "Hospitalización en piso",
    581479: "Ingreso ambulatorio",
}
# Mismos conceptos por su nombre en concept (para consultas que solo devuelven el nombre).
CONCEPTO_POR_NOMBRE = {
    "Emergency Room Visit": 9203,
    "Ambulatory Rehabilitation Visit": 581479,
    "Inpatient Visit": 9201,
    "Treatment urgency {Diagnosis}": 3045729,
}
NOMBRE_GRUPO_ETARIO = {
    "pediatria": "Pediatría (< 18)",
    "adulto": "Adulto (18–64)",
    "adulto_mayor": "Adulto mayor (≥ 65)",
    "sin_dato": "Sin dato",
}
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
DIAS_SEMANA_COMPLETOS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


# --- Formato de números (colombiano: miles con punto, decimales con coma) -------------------
def _es_vacio(x) -> bool:
    try:
        return x is None or (isinstance(x, float) and math.isnan(x))
    except TypeError:
        return False


def _colombiano(texto: str) -> str:
    """Convierte ``1,234.5`` (formato de Python) en ``1.234,5``."""
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def fmt_decimal(x, decimales: int = 1) -> str:
    """Número con ``decimales`` decimales y separador de miles: ``1.234,5``."""
    if _es_vacio(x):
        return "—"
    return _colombiano(f"{float(x):,.{decimales}f}")


def fmt_entero(n) -> str:
    """Entero con separador de miles: ``1.706.001``."""
    if _es_vacio(n):
        return "—"
    return _colombiano(f"{round(float(n)):,.0f}")


def fmt_pct(x, decimales: int = 1) -> str:
    """Porcentaje (``x`` en escala 0–100): ``68,2 %``."""
    return "—" if _es_vacio(x) else f"{fmt_decimal(x, decimales)} %"


def fmt_horas(h, decimales: int = 1) -> str:
    """Horas: ``24,1 h``."""
    return "—" if _es_vacio(h) else f"{fmt_decimal(h, decimales)} h"


def fmt_numero(x) -> str:
    """Formato adaptable: enteros sin decimales; < 1 con dos; el resto con uno."""
    if _es_vacio(x):
        return "—"
    x = float(x)
    if x.is_integer():
        return fmt_entero(x)
    return fmt_decimal(x, 2 if abs(x) < 1 else 1)


def fmt_mes(fecha) -> str:
    """``ene 2024`` a partir de una fecha (``date``, ``datetime`` o ``Timestamp``)."""
    if _es_vacio(fecha):
        return "—"
    return f"{MESES[fecha.month - 1]} {fecha.year}"


def fmt_fecha(fecha) -> str:
    """``31 mar 2026``."""
    if _es_vacio(fecha):
        return "—"
    return f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}"


# Equivalentes con firma (valor, posición) para matplotlib.ticker.FuncFormatter.
def tick_entero(x, _pos=None) -> str:
    return fmt_entero(x)


def tick_numero(x, _pos=None) -> str:
    return fmt_numero(x)


def tick_pct(x, _pos=None) -> str:
    return fmt_pct(x, 0 if float(x).is_integer() else 1)


def tick_horas(x, _pos=None) -> str:
    return fmt_horas(x, 0 if float(x).is_integer() else 1)


# --- Familias de color ------------------------------------------------------------------------
# rampa: completa (heatmaps y rellenos de cajas). barras: del paso anterior al base hacia lo oscuro
# (barras y marcadores; los tonos más claros no contrastan con el fondo blanco).
FAMILIAS = {
    "urgencias": {"base": AZUL, "rampa": RAMPA_AZUL, "barras": RAMPA_AZUL[3:], "oscuro": RAMPA_AZUL[5],
                  "claro": RAMPA_AZUL[3]},
    "hospitalizacion": {"base": CIRUELA, "rampa": RAMPA_CIRUELA, "barras": RAMPA_CIRUELA[3:],
                        "oscuro": RAMPA_CIRUELA[5], "claro": RAMPA_CIRUELA[3]},
    "ambulatorio": {"base": OCRE, "rampa": RAMPA_OCRE, "barras": RAMPA_OCRE[3:], "oscuro": RAMPA_OCRE[5],
                    "claro": RAMPA_OCRE[3]},
    "general": {"base": VERDE, "rampa": RAMPA_VERDE, "barras": RAMPA_VERDE[3:], "oscuro": RAMPA_VERDE[5],
                "claro": RAMPA_VERDE[3]},
    "gris": {"base": GRISES[1], "rampa": RAMPA_GRIS, "barras": (GRISES[2], GRISES[1], GRISES[0]),
             "oscuro": GRISES[0], "claro": GRISES[2]},
}
# Nombres anteriores de las familias, para no romper código existente.
_ALIAS_FAMILIA = {"azul": "urgencias", "ciruela": "hospitalizacion", "ocre": "ambulatorio", "verde": "general"}


def familia(nombre: str) -> dict:
    """Familia por nombre (``urgencias``, ``hospitalizacion``, ``ambulatorio``, ``general`` o ``gris``)."""
    return FAMILIAS[_ALIAS_FAMILIA.get(nombre, nombre)]


def _familia_de_concepto(concept_id) -> str:
    try:
        c = int(concept_id)
    except (TypeError, ValueError):
        return "general"
    return {9203: "urgencias", 3045729: "urgencias", 9201: "hospitalizacion", 581479: "ambulatorio"}.get(c, "general")


def familia_de_tipo_visita(concept_id) -> str:
    """9203 y 3045729 → urgencias; 9201 → hospitalizacion; 581479 → ambulatorio; otros → general."""
    return _familia_de_concepto(concept_id)


def familia_de_etapa(concept_id) -> str:
    """Igual que ``familia_de_tipo_visita``, para los tipos de etapa de ``visit_detail``."""
    return _familia_de_concepto(concept_id)


def color_tipo_visita(concept_id) -> str:
    """Color de un tipo de visita. Los tipos sin familia propia van en gris (una figura no
    debe pasar de 3 familias)."""
    try:
        return COLOR_TIPO_VISITA.get(int(concept_id), GRISES[1])
    except (TypeError, ValueError):
        return GRISES[1]


def colores_por_rango(n: int, nombre_familia: str) -> list[str]:
    """Colores de un top-N por puesto: 1–5 en ``oscuro``, 6–15 en ``base`` y 16 en adelante en
    el paso de barras más claro. La categoría «Otros» va aparte, en ``COLOR_OTROS``."""
    f = familia(nombre_familia)
    return [f["oscuro"] if i < 5 else f["base"] if i < 15 else f["barras"][0] for i in range(n)]


def tonos(nombre_familia: str, n: int) -> list[str]:
    """``n`` tonos de la rampa de una familia, de claro a oscuro (sin el tono más claro)."""
    rampa = familia(nombre_familia)["rampa"][1:]
    if n <= 1:
        return [rampa[len(rampa) // 2 + 1]]
    indices = [round(i * (len(rampa) - 1) / (n - 1)) for i in range(n)]
    return [rampa[i] for i in indices]


def colormap(nombre_familia: str):
    """Colormap continuo de matplotlib con la rampa completa de la familia, desde blanco.

    Las celdas ``NaN`` (suprimidas o que no aplican) quedan en blanco.
    """
    from matplotlib.colors import LinearSegmentedColormap  # import local: el módulo no exige matplotlib

    rampa = familia(nombre_familia)["rampa"]
    colores = list(rampa) if rampa[0] == FONDO_FIGURA else [FONDO_FIGURA, *rampa]
    mapa = LinearSegmentedColormap.from_list(f"rampa_{nombre_familia}", colores)
    mapa.set_bad(FONDO_FIGURA)
    return mapa


def rampa(nombre_familia: str):
    """Nombre anterior de ``colormap``."""
    return colormap(nombre_familia)


def es_fecha(x) -> bool:
    return isinstance(x, (date, datetime))
