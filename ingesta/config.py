"""Configuración central de la ingesta: datasets, mapeos de campos y años."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Carga el .env de la raíz del proyecto sin importar desde dónde se ejecute
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://politracker:politracker_dev@localhost:5433/politracker",
)
SODA_APP_TOKEN = os.getenv("SODA_APP_TOKEN", "").strip()
ANIOS_INGESTA = [
    int(a) for a in os.getenv("ANIOS_INGESTA", "2023,2024,2025").split(",") if a.strip()
]

SODA_BASE_URL = "https://www.datos.gov.co/resource"

# Dataset de GASTOS del PGN (Minhacienda, sistema SIIF)
DATASET_GASTOS = "5phs-yqfw"
FUENTE_GASTOS = "datos.gov.co/5phs-yqfw"

# Dataset de INGRESOS del PGN: "Ingresos por Vigencia" (Minhacienda, SIIF).
# Elegido tras buscar en el catálogo Socrata: es el único publicado por
# Minhacienda con aforo y recaudo mensual a nivel nacional.
DATASET_INGRESOS = "22f3-gynv"
FUENTE_INGRESOS = "datos.gov.co/22f3-gynv"

# Mapeo campo_soda -> columna_bd, verificado con $limit=1 contra la API real
# (los nombres SODA difieren del CSV: minúsculas, sin tildes ni espacios).
CAMPOS_GASTO = {
    "anio": "anio",
    "nombremes": "mes",            # viene como nombre ("Enero") -> convertir a número
    "sector": "sector",
    "codigoentidad": "cod_entidad",
    "nombreentidad": "entidad",
    "nombretipogasto": "tipo_gasto",
    "nombredetallegasto": "detalle_gasto",
    "apropiacioninicial": "apropiacion_inicial",
    "apropiacionvigente": "apropiacion_vigente",
    "compromisos": "compromisos",
    "obligaciones": "obligaciones",
    "pagos": "pagos",
}

CAMPOS_INGRESO = {
    "anio": "anio",
    "numeromes": "mes",            # viene como número en string ("1")
    "nombrerubro": "concepto",
    "aforovigente": "aforo",
    "recaudoefectivoacumulado": "recaudo",
}

# Meses en español -> número, tolerante a mayúsculas y tildes
MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
