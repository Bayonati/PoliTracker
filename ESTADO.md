# Estado de PoliTracker
Última actualización: 2026-06-12

## Qué existe y funciona
- `CLAUDE.md` — instrucciones completas del proyecto
- `docker-compose.yml` — PostgreSQL 15 en Docker, puerto host **5433** (el 5432 lo ocupa un PostgreSQL nativo de Windows)
- `.env` / `.env.example` — variables documentadas
- `ingesta/config.py` — datasets, mapeo real campo_soda→columna_bd (verificado con `$limit=1`), años
- `ingesta/soda_client.py` — cliente SODA con paginación ($limit=50000, $order=:id), backoff 2s/4s/8s, timeout 60s
- `ingesta/db.py` — engine + tablas SQLAlchemy Core + `ensure_schema()`
- `ingesta/schema.sql` — SQL de referencia
- `ingesta/ingestar_gastos.py` — dataset 5phs-yqfw → tabla `gasto` (agrega por llave única antes del upsert)
- `ingesta/ingestar_ingresos.py` — dataset 22f3-gynv → tabla `ingreso`
- `backend/app/` — FastAPI: main (CORS, manejo global de errores), database, models, schemas, routers gasto/ingreso
- `frontend/` — Vue 3 + Vite + Tailwind: TreemapExplorer (D3 calcula, Vue renderiza), Breadcrumb, BarraComparativa, IngresosVsGastos (Chart.js), SelectorAnio, TarjetaCifra, TablaDetalle, store composable, formato es-CO

## Última fase completada
- **Fase 4 (Frontend)**. Verificado: `npm run build` compila sin errores; dev server en :5173 sirve la SPA; CORS contra :8000 OK; drill-down de 3 niveles validado contra la API con datos reales (sectores → entidades de Salud → tipos de Minsalud).
- Fase 3: los 6 endpoints probados con datos reales; totales coinciden con la cordura de Fase 2; 404 con mensaje claro.
- Fase 2: ingesta corrida DOS veces sin duplicar (15.729 / 14.569 / 14.494 filas por año, idénticas en ambas corridas). Cordura: apropiación vigente 2025 (mes 12) = **$510,5 billones COP** ✓ (PGN 2025 ~$523B inicial). Ingresos: aforo 2025 = $510,5 billones ✓.
- Fase 1: BD conecta desde host (psycopg2 → PostgreSQL 15.18 del contenedor).

## Próximo paso
- Fase 5: Deploy (backend + BD a Railway, frontend a Vercel). Requiere cuentas/credenciales del founder.
- Probar la UI en navegador real (drill-down, móvil, teclado) — verificación técnica hecha, falta la visual.

## Decisiones tomadas
| Fecha | Decisión | Por qué |
|---|---|---|
| 2026-06-12 | Puerto host 5433 para Postgres | Un PostgreSQL nativo de Windows ya escucha en 0.0.0.0:5432 y capturaba las conexiones (error psycopg2 UnicodeDecodeError con mensaje en español) |
| 2026-06-12 | Dataset de ingresos: `22f3-gynv` "Ingresos por Vigencia" (Minhacienda) | Único del catálogo Socrata publicado por Minhacienda con aforo y recaudo mensual del PGN; solo tiene filas nivel=2, sin doble conteo |
| 2026-06-12 | La ingesta AGREGA antes del upsert | El dataset crudo tiene más granularidad (rubros 4°/5° nivel, fuente, situación) que la llave única; sin agregar, el upsert sobrescribiría y perdería plata |
| 2026-06-12 | **Montos mensuales = ACUMULADOS del año** | Verificado con entidad 13-01-01 en 2024: pagos crecen monótonamente enero→diciembre. Valor anual = último mes, NUNCA la suma. Los endpoints filtran por `mes = MAX(mes)` |
| 2026-06-12 | `concepto` de ingreso = `nombrerubro` | Granularidad ciudadana razonable (~110 conceptos), agregando sobre fuente/situación |
| 2026-06-12 | Navegación de vistas sin vue-router | 3 vistas estáticas; un `ref` basta y es una dependencia menos |

## Lo que falló y cómo se resolvió
| Fecha | Problema | Solución |
|---|---|---|
| 2026-06-12 | psycopg2 `UnicodeDecodeError: 0xf3` al conectar | No era encoding: la conexión iba a un PostgreSQL nativo de Windows en el 5432 que respondía error en español (cp1252). Se movió el contenedor al 5433 |
| 2026-06-12 | Node.js no estaba instalado | `winget install OpenJS.NodeJS.LTS`; queda en `C:\Program Files\nodejs` (abrir terminal nueva para que el PATH lo tome) |

## Cómo correr todo (dev)
```powershell
docker compose up -d
.venv\Scripts\python ingesta\ingestar_gastos.py      # solo si hay que refrescar datos
.venv\Scripts\python ingesta\ingestar_ingresos.py
.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000
cd frontend; npm run dev                              # http://localhost:5173
```
