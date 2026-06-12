# PoliTracker — Instrucciones completas para Claude Code

> **Cómo usar este archivo:** pégalo completo como primer mensaje en Claude Code, o guárdalo como `CLAUDE.md` en la raíz del repo para que Claude Code lo lea automáticamente en cada sesión.

---

## 1. Contexto del proyecto

**PoliTracker** es una plataforma ciudadana de vigilancia del gasto público colombiano. Su misión: que cualquier colombiano, sin conocimientos técnicos, entienda en qué se gastan sus impuestos mediante gráficas claras e interactivas.

**Inspiración directa:** el Spending Explorer de USAspending.gov (https://www.usaspending.gov/explorer/budget_function) — navegación jerárquica top-down donde el usuario parte de una visión macro (sectores) y hace drill-down hasta el detalle.

**Usuario objetivo:** ciudadano colombiano promedio. NO es una herramienta para economistas. Cada texto, label y visualización debe ser comprensible para alguien sin formación en finanzas públicas.

**Alcance del MVP:**
- Treemap interactivo con drill-down de 3 niveles: **Sector → Entidad → Tipo de Gasto**
- Comparación visual de **apropiado vs pagado** (cuánto le asignaron vs cuánto gastó realmente)
- Vista de **ingresos vs gastos** del Estado
- Filtro por **departamento** (fase posterior del MVP, ver sección 13)
- Datos de **2023, 2024 y 2025**
- Plataforma **100% pública, sin login, sin registro**
- Actualización de datos **manual** (se corre el script de ingesta a mano)

---

## 2. Tu rol y reglas de comportamiento

Eres un ingeniero senior full-stack. Trabajas con un founder técnico no-experto. Reglas:

1. **Antes de escribir código**, describe en una línea qué vas a hacer.
2. **Explica siempre por qué** tomaste una decisión técnica, en máximo 2 líneas.
3. Si hay más de una forma de hacer algo, menciona cuál elegiste y por qué.
4. **Usa español** en toda la comunicación. El código (variables, funciones) va en inglés; los comentarios y docstrings en español.
5. Sé directo. No repitas lo que ya se dijo.
6. **No asumas que algo funciona.** Después de cada fase, corre el código y verifica con datos reales antes de continuar.
7. Si una tarea se complica más de lo esperado: **para, resume dónde estás, y propón dividirla.**
8. Al terminar cada fase, actualiza la sección `ESTADO.md` del repo (ver sección 14).

---

## 3. Stack tecnológico (FIJO — no se cambia sin discutirlo)

| Capa | Tecnología | Notas |
|---|---|---|
| Frontend | Vue 3 + Vite + TailwindCSS | Composition API con `<script setup>` |
| Gráficas | D3.js para el treemap, Chart.js para barras/líneas | D3 solo para el treemap (Chart.js no hace treemaps con drill-down decente) |
| Backend | Python 3.11 + FastAPI + SQLAlchemy 2.x | Estilo declarativo moderno (Mapped, mapped_column) |
| Base de datos | PostgreSQL 15 | Local vía Docker; producción en Supabase o Railway |
| Ingesta | Python — requests + SODA API | NUNCA web scraping si existe API |
| Infra local | Docker + Docker Compose | Solo PostgreSQL en contenedor; backend y frontend corren en host para desarrollo rápido |
| Deploy | Frontend en Vercel; backend + BD en Railway | Ver sección 12 |

**Decisión ya tomada sobre deploy:** FastAPI NO corre nativamente en Vercel. El frontend (Vue, estático) va a Vercel; el backend FastAPI y PostgreSQL van a Railway. No intentes meter FastAPI en funciones serverless de Vercel.

---

## 4. Estructura de carpetas objetivo

```
politracker/
├── CLAUDE.md                  # Este archivo
├── ESTADO.md                  # Bitácora: qué existe, qué falta, qué falló
├── docker-compose.yml         # Solo PostgreSQL
├── .env.example               # Variables de entorno documentadas
├── .gitignore
│
├── ingesta/                   # Scripts de ingesta de datos
│   ├── requirements.txt
│   ├── config.py              # Lee .env, define constantes (dataset IDs, años)
│   ├── soda_client.py         # Cliente genérico SODA API con paginación
│   ├── ingestar_gastos.py     # Ingesta dataset 5phs-yqfw → tabla gasto
│   ├── ingestar_ingresos.py   # Ingesta dataset de ingresos → tabla ingreso
│   └── README.md              # Cómo correr cada script
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py            # FastAPI app + CORS
│   │   ├── database.py        # Engine, SessionLocal, get_db
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   ├── schemas.py         # Schemas Pydantic de respuesta
│   │   └── routers/
│   │       ├── gasto.py       # Endpoints de gasto
│   │       └── ingreso.py     # Endpoints de ingreso
│   └── README.md
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.js
        ├── App.vue
        ├── api/client.js          # Wrapper fetch con base URL desde env
        ├── stores/explorer.js     # Estado del drill-down (nivel actual, breadcrumb, filtros)
        ├── components/
        │   ├── TreemapExplorer.vue    # El componente estrella (D3)
        │   ├── Breadcrumb.vue         # Sector > Entidad > Tipo
        │   ├── BarraComparativa.vue   # Apropiado vs pagado
        │   ├── IngresosVsGastos.vue   # Chart.js
        │   ├── SelectorAnio.vue
        │   ├── TarjetaCifra.vue       # Número grande con contexto
        │   └── TablaDetalle.vue       # Vista tabla accesible (alternativa al treemap)
        └── utils/formato.js           # Formateo de pesos colombianos (ver sección 11.4)
```

---

## 5. Fuentes de datos

### 5.1 Fuente principal de GASTOS: datos.gov.co — dataset `5phs-yqfw`

- **Nombre:** "Información de Gastos del Presupuesto General de la Nación"
- **Publica:** Ministerio de Hacienda (datos del sistema SIIF)
- **API SODA:** `https://www.datos.gov.co/resource/5phs-yqfw.json`
- **Sin autenticación obligatoria.** Opcionalmente registrar un App Token en datos.gov.co (header `X-App-Token`) para evitar throttling. Si la ingesta es lenta o devuelve 429, registra un token gratis y agrégalo a `.env`.

**Campos conocidos del dataset (nombres de la versión CSV; los nombres SODA difieren):**

| Campo CSV | Significado |
|---|---|
| Año | Año del presupuesto |
| Mes | Mes del reporte |
| Sector | Sector del Estado (Salud, Defensa, Educación…) |
| Codigo Entidad | Código de la entidad ejecutora |
| Nombre Entidad | Entidad ejecutora (ej: MINSALUD - GESTIÓN GENERAL) |
| Nombre Tipo Gasto | FUNCIONAMIENTO / INVERSIÓN / SERVICIO DE LA DEUDA |
| Nombre Detalle del Gasto | Subcategoría (ej: Transferencias Corrientes) |
| Apropiación Inicial | Presupuesto asignado al inicio del año |
| Adiciones / Reducciones | Ajustes durante el año |
| Apropiación Vigente | Presupuesto ajustado final |
| Compromisos | Plata ya comprometida (contratos firmados) |
| Obligaciones | Plata por bienes/servicios ya recibidos |
| Pagos | Plata efectivamente pagada (= ejecutado real) |

⚠️ **INSTRUCCIÓN CRÍTICA — descubre los nombres reales de campos antes de escribir la ingesta:**
Los nombres de campos en la API SODA son distintos a los del CSV (van en minúsculas, sin tildes, con guiones bajos; "Año" suele quedar como `a_o`). NO asumas los nombres. Tu PRIMER paso de la fase de ingesta es:

```bash
curl "https://www.datos.gov.co/resource/5phs-yqfw.json?\$limit=1"
```

Inspecciona el JSON devuelto, documenta el mapeo real `campo_soda → columna_bd` como diccionario en `config.py`, y construye todo a partir de ahí. Si el dataset `5phs-yqfw` no responde o cambió de ID, busca el reemplazo en https://www.datos.gov.co buscando "Información de Gastos del Presupuesto General de la Nación" y avisa al usuario antes de continuar.

### 5.2 Fuente de INGRESOS: datos.gov.co

Existe un dataset equivalente de ingresos del PGN publicado por Minhacienda (mismo sistema SIIF). Su ID exacto debe confirmarse. Pasos:
1. Busca en la API de catálogo: `https://api.us.socrata.com/api/catalog/v1?domains=www.datos.gov.co&q=ingresos presupuesto general nación`
2. Identifica el dataset oficial de Minhacienda (verifica que el publicador sea Ministerio de Hacienda y que tenga campos de recaudo/aforo por mes).
3. Documenta el ID elegido en `config.py` y avisa al usuario cuál elegiste y por qué.
4. Si no existe un dataset de ingresos utilizable, NO bloquees el proyecto: marca la vista Ingresos vs Gastos como pendiente en `ESTADO.md` y continúa con gastos.

### 5.3 Fuente departamental (NO en esta fase)

`mapainversiones.dnp.gov.co` tiene datos de inversión por departamento/municipio, pero su API no está documentada públicamente. El filtro por departamento queda para la fase 2 del proyecto (ver sección 13). NO lo implementes ahora.

### 5.4 Reglas de la API SODA (aplícalas en `soda_client.py`)

- Paginación con `$limit` y `$offset`. Usa `$limit=50000` (máximo eficiente) y pagina hasta que la respuesta venga vacía.
- Filtra por año en servidor, no en cliente: `$where=a_o in('2023','2024','2025')` (ajusta el nombre del campo al real).
- Ordena de forma estable para que la paginación no duplique: `$order=:id`.
- Reintentos: ante 429 o 5xx, espera con backoff exponencial (2s, 4s, 8s, máx 3 reintentos) y registra en logs.
- Timeout de 60s por request.
- Los montos vienen como strings → convierte a `Decimal`, nunca a `float` (es plata pública, la precisión importa).

---

## 6. Esquema de base de datos

Crea las tablas con SQLAlchemy (modelos) y deja también el SQL de referencia en `ingesta/schema.sql`.

```sql
CREATE TABLE gasto (
    id              BIGSERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    mes             SMALLINT NOT NULL,          -- 1-12 (convierte nombres de mes a número en la ingesta)
    sector          TEXT NOT NULL,
    cod_entidad     VARCHAR(30) NOT NULL,
    entidad         TEXT NOT NULL,
    tipo_gasto      TEXT NOT NULL,              -- FUNCIONAMIENTO / INVERSIÓN / SERVICIO DE LA DEUDA
    detalle_gasto   TEXT,
    apropiacion_inicial  NUMERIC(20,2) DEFAULT 0,
    apropiacion_vigente  NUMERIC(20,2) DEFAULT 0,
    compromisos          NUMERIC(20,2) DEFAULT 0,
    obligaciones         NUMERIC(20,2) DEFAULT 0,
    pagos                NUMERIC(20,2) DEFAULT 0,
    fuente          TEXT NOT NULL DEFAULT 'datos.gov.co/5phs-yqfw',
    ingestado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_gasto UNIQUE (anio, mes, cod_entidad, tipo_gasto, detalle_gasto)
);

CREATE INDEX idx_gasto_anio_sector ON gasto (anio, sector);
CREATE INDEX idx_gasto_anio_entidad ON gasto (anio, sector, entidad);

CREATE TABLE ingreso (
    id              BIGSERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    mes             SMALLINT NOT NULL,
    concepto        TEXT NOT NULL,              -- ajusta a los campos reales del dataset que encuentres
    aforo           NUMERIC(20,2) DEFAULT 0,    -- lo presupuestado a recaudar
    recaudo         NUMERIC(20,2) DEFAULT 0,    -- lo efectivamente recaudado
    fuente          TEXT NOT NULL,
    ingestado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ingreso UNIQUE (anio, mes, concepto)
);
```

**Reglas del esquema:**
- **Upsert SIEMPRE, nunca insert ciego.** Usa `INSERT ... ON CONFLICT ON CONSTRAINT uq_gasto DO UPDATE SET ...` (en SQLAlchemy: `postgresql.insert(...).on_conflict_do_update(...)`). Esto permite re-correr la ingesta sin duplicar — es un principio innegociable del proyecto.
- El campo `detalle_gasto` puede venir NULL en algunos registros; el constraint UNIQUE de Postgres trata los NULL como distintos. Para evitar duplicados, en la ingesta normaliza NULL → string vacío `''`.
- NO cambies este esquema sin avisar al usuario primero y explicar por qué.

---

## 7. FASE 1 — Infraestructura local

**Entregable:** PostgreSQL corriendo en Docker, accesible desde host.

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:15-alpine
    container_name: politracker_db
    environment:
      POSTGRES_USER: politracker
      POSTGRES_PASSWORD: ${DB_PASSWORD:-politracker_dev}
      POSTGRES_DB: politracker
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-READY", "pg_isready -U politracker"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```
(⚠️ corrige el healthcheck: la forma correcta es `test: ["CMD-SHELL", "pg_isready -U politracker"]`)

`.env.example`:
```
DATABASE_URL=postgresql+psycopg2://politracker:politracker_dev@localhost:5432/politracker
SODA_APP_TOKEN=           # opcional, registrarse en datos.gov.co si hay throttling
ANIOS_INGESTA=2023,2024,2025
VITE_API_BASE_URL=http://localhost:8000
```

**Checkpoint Fase 1:** `docker compose up -d` levanta la BD y `psql` (o un script Python de prueba) conecta exitosamente. No avances sin verificar esto.

---

## 8. FASE 2 — Ingesta de datos

**Entregable:** las tablas `gasto` e `ingreso` llenas con datos reales 2023–2025.

### 8.1 `soda_client.py` — cliente genérico

Funciones:
- `fetch_all(dataset_id, where=None, select=None) -> Iterator[dict]`: generador que pagina automáticamente con `$limit=50000`, `$order=:id`, backoff ante errores, y hace `yield` de cada registro. Loggea progreso cada página: `"Página 3 — 150.000 registros acumulados"`.
- `fetch_sample(dataset_id, n=5) -> list[dict]`: para inspeccionar campos.

### 8.2 `ingestar_gastos.py`

Flujo:
1. Llama `fetch_sample` e imprime los campos reales del dataset. Verifica que el mapeo de `config.py` coincida; si un campo esperado no existe, ABORTA con mensaje claro en vez de ingestar basura.
2. Por cada año en `ANIOS_INGESTA`, trae los registros filtrados por año.
3. Transforma: nombres de mes → número (diccionario explícito ENERO=1...DICIEMBRE=12, tolerante a mayúsculas/tildes), montos string → Decimal (maneja vacíos como 0), NULL en detalle_gasto → ''.
4. Upsert por lotes de 5.000 registros (no registro por registro — sería lentísimo; no todo en un solo commit — si falla pierdes todo).
5. Al final imprime resumen: registros procesados, insertados, actualizados, errores, y una verificación de cordura: el total de `apropiacion_vigente` del año más reciente debe estar en el orden de los cientos de billones de pesos (el PGN 2025 ronda los $523 billones COP). Si el total da algo absurdo (millones o trillones), algo está mal en la conversión de montos — investiga antes de continuar.

### 8.3 Logging (aplica a toda la ingesta)

- Usa el módulo `logging` de Python, nivel INFO a consola, formato con timestamp.
- Loggea: inicio/fin de cada año, cada página descargada, cada lote upserteado, todo error con su registro problemático.
- Un registro malformado NO debe tumbar la ingesta completa: loggea el error, salta el registro, cuenta los saltados y repórtalos al final.

**Checkpoint Fase 2:** correr `SELECT anio, COUNT(*), SUM(apropiacion_vigente) FROM gasto GROUP BY anio;` y mostrar el resultado al usuario para validar juntos que los números tienen sentido.

---

## 9. FASE 3 — Backend FastAPI

**Entregable:** API REST corriendo en `localhost:8000` con docs automáticas en `/docs`.

### 9.1 Configuración base

- CORS habilitado para `http://localhost:5173` (dev) y el dominio de Vercel (prod, vía variable de entorno `FRONTEND_ORIGIN`).
- Todas las respuestas de montos en **string** (los NUMERIC de Postgres pierden precisión si los serializas como float de JSON). El frontend los parsea.
- Manejo de errores global: 404 con mensaje claro si no hay datos para los filtros pedidos; nunca un 500 pelado sin contexto.

### 9.2 Endpoints (contratos exactos)

**`GET /api/gasto/sectores?anio=2025`** — Nivel 1 del treemap
```json
{
  "anio": 2025,
  "total_apropiado": "523000000000000.00",
  "total_pagado": "310000000000000.00",
  "items": [
    {
      "nombre": "SALUD Y PROTECCIÓN SOCIAL",
      "apropiado": "62000000000000.00",
      "pagado": "41000000000000.00",
      "porcentaje_del_total": 11.8,
      "porcentaje_ejecucion": 66.1
    }
  ]
}
```

**`GET /api/gasto/entidades?anio=2025&sector=SALUD...`** — Nivel 2 (misma forma, items = entidades del sector)

**`GET /api/gasto/tipos?anio=2025&sector=...&entidad=...`** — Nivel 3 (items = tipos de gasto de la entidad)

**`GET /api/gasto/serie?anio=2025&sector=...`** — serie mensual para la vista de evolución (mes a mes, apropiado acumulado vs pagado acumulado)

**`GET /api/ingresos/resumen?anio=2025`** — total aforo vs recaudo, y por concepto

**`GET /api/meta`** — años disponibles, fecha de última ingesta, fuentes. El frontend lo usa para poblar el selector de año y mostrar "Datos actualizados a..."

**Reglas de agregación:** los datos en BD son mensuales y acumulativos según SIIF — VERIFICA con los datos reales si los montos de cada mes son acumulados del año o solo del mes. Si son acumulados (lo más probable en reportes SIIF), el valor anual = el del último mes disponible, NO la suma de los meses. Esta verificación es obligatoria antes de escribir los endpoints: toma una entidad, mira sus 12 meses, y decide. Documenta la conclusión en `ESTADO.md`.

**Checkpoint Fase 3:** probar cada endpoint con curl contra datos reales y validar que los totales coincidan con la verificación de cordura de la Fase 2.

---

## 10. FASE 4 — Frontend Vue

**Entregable:** SPA corriendo en `localhost:5173` consumiendo la API real.

### 10.1 Vistas

1. **Explorador (home):** el treemap con drill-down. Es la página principal y la razón de ser del producto.
2. **Ingresos vs Gastos:** comparación anual simple.
3. **Acerca de:** qué es PoliTracker, de dónde salen los datos (con links a las fuentes oficiales), y la fecha de última actualización.

### 10.2 El Treemap (componente estrella — dedícale el mayor cuidado)

Comportamiento, calcado del Spending Explorer de USAspending:
- Cada rectángulo = un sector; área proporcional a `apropiado`.
- Dentro de cada rectángulo: nombre del sector, monto en formato ciudadano ($62,3 billones), y % del total.
- **Click en rectángulo → drill-down** al nivel siguiente con transición animada (300ms, ease-out). El breadcrumb se actualiza: `Todo el presupuesto > Salud > Minsalud`.
- Click en el breadcrumb → vuelve a ese nivel.
- **Hover → tooltip** con: apropiado, pagado, % de ejecución, y una frase en lenguaje ciudadano: "De cada $100 asignados, se han pagado $66".
- Rectángulos muy pequeños (<1% del total): agrúpalos en un bloque "Otros (12 sectores)" clickeable que expande la lista.
- **Toggle Treemap / Tabla:** la tabla (`TablaDetalle.vue`) muestra los mismos datos en filas ordenables. Es la vista accesible (lectores de pantalla) y la preferida en móvil.
- En móvil (<768px): el treemap pasa a barras horizontales apiladas verticalmente (un treemap táctil pequeño es inusable). Misma data, mismo drill-down por tap.

Implementación: D3 (`d3-hierarchy`, `treemapSquarify`) renderizando a SVG dentro del componente Vue. Vue es dueño del estado (nivel actual, filtros); D3 solo calcula layout y Vue renderiza los `<rect>` con template — evita que D3 manipule el DOM directamente para no pelear con el reactivity de Vue.

### 10.3 Estado global (`stores/explorer.js`)

Usa un composable simple (`reactive` + funciones), no Pinia — el estado es pequeño y una dependencia menos. Guarda: año seleccionado, nivel actual, path del drill-down, datos cacheados por nivel (no re-pedir al volver atrás).

### 10.4 Formateo de plata colombiana (`utils/formato.js`) — CRÍTICO

- En Colombia **un billón = 10^12** (millón de millones), NO el billion gringo (10^9). Jamás traduzcas billion→billón sin convertir.
- Escala ciudadana: ≥10^12 → "billones" (ej: `$62,3 billones`), ≥10^9 → "miles de millones" (ej: `$450 mil millones`), ≥10^6 → "millones".
- Separador decimal coma, separador de miles punto (formato es-CO). Usa `Intl.NumberFormat('es-CO', ...)`.
- Los montos llegan como string del API → usa `Number()` solo para visualización (la pérdida de precisión en display es aceptable; en cálculos de porcentajes redondea a 1 decimal).

---

## 11. Diseño visual de PoliTracker

El diseño debe transmitir: **datos oficiales, confiables, sin agenda política** — pero con carácter propio. No debe parecer ni una página de gobierno aburrida ni un dashboard genérico de admin template.

### 11.1 Identidad

- **Nombre:** PoliTracker. Logo tipográfico simple: "Poli" en peso bold + "Tracker" en regular, sin ícono en el MVP.
- **Concepto visual:** "el peso visual ES el peso del gasto". El treemap es el héroe absoluto de la página — la home abre directo con él ocupando la mayor parte del viewport, precedido solo por una línea de contexto: "El Estado colombiano tiene $523 billones para gastar en 2025. Así se reparten:".

### 11.2 Paleta (tokens exactos)

| Token | Hex | Uso |
|---|---|---|
| `tinta` | `#16233A` | Texto principal, fondo del header |
| `papel` | `#FAFBFC` | Fondo general |
| `andino` | `#2D6A8F` | Color base de la escala del treemap, links, acciones |
| `oro` | `#E9B44C` | Acento — SOLO para resaltar el dato clave en foco (hover, selección). Usar con extrema moderación |
| `ejecutado` | `#2E8B57` | Verde para % de ejecución saludable (>70%) |
| `alerta` | `#C0392B` | Rojo para ejecución baja (<40%) o sobrecostos |
| `neutro` | `#6B7686` | Textos secundarios, bordes, labels |

Escala del treemap: variaciones de luminosidad de `andino` (más oscuro = más plata). NO usar una paleta arcoíris por sector — el color codifica magnitud, no categoría.

### 11.3 Tipografía

- **Display y cifras grandes:** `Archivo` (Google Fonts) — grotesca de origen latinoamericano, excelente en pesos altos para números grandes. Las cifras protagonistas van en Archivo Expanded Bold.
- **Cuerpo y UI:** `Inter`.
- **Cifras tabulares (tablas, tooltips):** Inter con `font-variant-numeric: tabular-nums` para que las columnas de números alineen.
- Jerarquía: las CIFRAS son más grandes que los títulos. En PoliTracker el dato manda.

### 11.4 Lenguaje ciudadano (copy)

- Nunca uses jerga presupuestal sin traducir. Glosario obligatorio en tooltips con ícono ⓘ:
  - "Apropiado" → "Plata asignada para gastar este año"
  - "Pagado" → "Plata que ya salió de la cuenta del Estado"
  - "Compromisos" → "Plata ya prometida en contratos firmados"
- Cada vista responde una pregunta en lenguaje natural como título: "¿En qué se gasta la plata?", "¿Cuánto entra vs cuánto sale?", "¿Quién ejecuta y quién no?"
- Tono: directo, neutral, sin opinión política. Los datos hablan.

### 11.5 Calidad base (no negociable)

- Responsive hasta 360px de ancho.
- Focus visible en todos los elementos interactivos (navegación por teclado del treemap: flechas para moverse, Enter para drill-down, Escape para subir).
- `prefers-reduced-motion`: desactiva las transiciones del treemap.
- Contraste AA mínimo en todo texto sobre los rectángulos del treemap (texto blanco sobre tonos oscuros de andino, tinta sobre tonos claros).

---

## 12. Deploy (al final, no antes de que todo funcione local)

1. **Backend + BD → Railway:** un servicio PostgreSQL + un servicio Python (FastAPI con uvicorn). Variables: `DATABASE_URL` interna de Railway, `FRONTEND_ORIGIN` con el dominio de Vercel.
2. **Ingesta:** se corre desde la máquina local apuntando `DATABASE_URL` a la BD de Railway (la pública). No montar cron aún — actualización manual por decisión del founder.
3. **Frontend → Vercel:** proyecto Vite estándar. `VITE_API_BASE_URL` apuntando al dominio de Railway.
4. Verificación post-deploy: abrir la URL de Vercel, hacer drill-down completo de 3 niveles, verificar que la vista de ingresos carga, y revisar la consola del navegador sin errores CORS.

---

## 13. Fuera de alcance (NO construir ahora, aunque parezca buena idea)

- ❌ Filtro por departamento/municipio (requiere fuente MapaInversiones — fase 2 del proyecto)
- ❌ Datos de contratos individuales / SECOP (fase 2)
- ❌ Login, usuarios, favoritos, alertas
- ❌ Cron / actualización automática de datos
- ❌ Históricos anteriores a 2023
- ❌ Comparaciones ajustadas por inflación
- ❌ Cualquier refactor fuera del scope de la fase en curso

Si durante el desarrollo descubres que algo de esta lista es necesario para el MVP, PARA y discútelo con el usuario antes de implementarlo.

---

## 14. Bitácora y forma de trabajo

Mantén un archivo `ESTADO.md` en la raíz con esta estructura, y actualízalo al cerrar cada fase:

```markdown
# Estado de PoliTracker
Última actualización: <fecha>

## Qué existe y funciona
- (lista archivo por archivo, una línea cada uno)

## Última fase completada
- (qué quedó funcionando y cómo se verificó)

## Próximo paso
- (qué sigue)

## Decisiones tomadas
| Fecha | Decisión | Por qué |

## Lo que falló y cómo se resolvió
| Fecha | Problema | Solución |
```

### Orden de ejecución estricto

```
FASE 1: Infra local (docker-compose + .env + estructura de carpetas)
   └── checkpoint: BD conecta ✓
FASE 2: Ingesta (soda_client → gastos → ingresos)
   └── checkpoint: totales validados con el usuario ✓
FASE 3: Backend (modelos → endpoints → pruebas curl)
   └── checkpoint: /docs funciona, totales coinciden ✓
FASE 4: Frontend (layout → treemap → drill-down → ingresos → pulido)
   └── checkpoint: drill-down completo funciona con datos reales ✓
FASE 5: Deploy (Railway → Vercel → verificación end-to-end)
```

**No saltes fases. No mezcles fases.** Cada checkpoint requiere mostrar evidencia (output de comando, query, screenshot) antes de continuar.

### Criterios de éxito del MVP completo

- [ ] La ingesta corre dos veces seguidas sin duplicar registros (upsert verificado)
- [ ] El total del PGN por año coincide con el orden de magnitud oficial (~$500 billones COP en 2025)
- [ ] El treemap hace drill-down de 3 niveles con datos reales, fluido, sin errores de consola
- [ ] Un ciudadano sin contexto entiende la home en 10 segundos (prueba: ¿la primera frase + el treemap responden "en qué se gasta la plata"?)
- [ ] Funciona en un celular de gama media
- [ ] La página "Acerca de" enlaza las fuentes oficiales y muestra la fecha de los datos
- [ ] Todo el código tiene manejo de errores y logs útiles

---

## 15. Errores conocidos a evitar (aprendizajes previos del proyecto)

1. **No asumas nombres de campos SODA** — verifícalos con `$limit=1` antes de codificar (sección 5.1).
2. **No uses float para plata** — Decimal en Python, NUMERIC en Postgres, string en JSON.
3. **No confundas billón colombiano con billion** — 10^12, siempre.
4. **No sumes meses sin verificar si son acumulados** (sección 9.2) — duplicarías el presupuesto x12.
5. **No dejes que D3 manipule el DOM** — D3 calcula, Vue renderiza.
6. **No uses scraping** — todo lo que necesita el MVP existe vía API SODA.
7. **No metas FastAPI en Vercel** — frontend Vercel, backend Railway.
