# Ingesta de datos — PoliTracker

Scripts que descargan los datos oficiales del Presupuesto General de la Nación
(API SODA de datos.gov.co) y los cargan a PostgreSQL con upsert (re-correr no duplica).

## Fuentes

| Tabla | Dataset | Publicador |
|---|---|---|
| `gasto` | [5phs-yqfw](https://www.datos.gov.co/resource/5phs-yqfw.json) — Información de Gastos del PGN | Minhacienda (SIIF) |
| `ingreso` | [22f3-gynv](https://www.datos.gov.co/resource/22f3-gynv.json) — Ingresos por Vigencia | Minhacienda (SIIF) |

## Cómo correr

```powershell
# 1. Levantar la BD (desde la raíz del proyecto)
docker compose up -d

# 2. Crear entorno e instalar dependencias
python -m venv .venv
.venv\Scripts\pip install -r ingesta\requirements.txt

# 3. Correr las ingestas (años configurados en .env -> ANIOS_INGESTA)
.venv\Scripts\python ingesta\ingestar_gastos.py
.venv\Scripts\python ingesta\ingestar_ingresos.py
```

## Notas importantes

- **Los montos mensuales son ACUMULADOS del año** (verificado con datos reales:
  los pagos de una entidad crecen monótonamente enero→diciembre). El valor anual
  es el del último mes disponible, nunca la suma de meses.
- El dataset de gastos tiene más granularidad que nuestra tabla (rubros 4°/5°
  nivel, fuente, situación de fondos): la ingesta agrega por la llave única
  antes del upsert.
- Si la API devuelve 429, registra un App Token gratis en datos.gov.co y ponlo
  en `.env` como `SODA_APP_TOKEN`.
