# Backend — PoliTracker API

FastAPI + SQLAlchemy 2.x sobre PostgreSQL.

## Cómo correr

```powershell
# Desde la raíz del proyecto, con la BD arriba y datos ingestados:
.venv\Scripts\pip install -r backend\requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Docs interactivas: http://localhost:8000/docs

## Endpoints

| Ruta | Qué responde |
|---|---|
| `GET /api/gasto/sectores?anio=2025` | Nivel 1 del treemap (sectores) |
| `GET /api/gasto/entidades?anio=&sector=` | Nivel 2 (entidades del sector) |
| `GET /api/gasto/tipos?anio=&sector=&entidad=` | Nivel 3 (tipos de gasto) |
| `GET /api/gasto/serie?anio=[&sector=&entidad=]` | Serie mensual acumulada |
| `GET /api/ingresos/resumen?anio=` | Aforo vs recaudo + total de gasto |
| `GET /api/meta` | Años disponibles, última ingesta, fuentes |

Los montos se devuelven como **string** para no perder precisión (NUMERIC → float JSON pierde centavos en cifras de billones).

Regla clave: los datos SIIF son acumulados por mes → el valor anual es el del último mes disponible, no la suma de meses.
