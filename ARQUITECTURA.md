# PoliTracker - Arquitectura y Flujos

## 1. Arquitectura General del Sistema

```mermaid
graph TD
    A["🌐 FUENTES DE DATOS OFICIALES<br/>(datos.gov.co - Minhacienda)"]
    
    A1["📊 Dataset 5phs-yqfw<br/>Gastos del PGN<br/>246K registros"]
    A2["📈 Dataset 22f3-gynv<br/>Ingresos por Vigencia<br/>10K registros"]
    
    B["⚙️ INGESTA DE DATOS<br/>(Python Scripts)"]
    B1["soda_client.py<br/>Paginación + Reintentos"]
    B2["ingestar_gastos.py<br/>Limpia + Agrega + Upsert"]
    B3["ingestar_ingresos.py<br/>Limpia + Agrega + Upsert"]
    
    C["🗄️ POSTGRESQL 15<br/>Puerto 5433<br/>45K gastos | 4K ingresos"]
    
    D["🔌 BACKEND FASTAPI<br/>Puerto 8000<br/>6 Endpoints REST"]
    
    E["🎨 FRONTEND VUE 3<br/>Puerto 5173<br/>SPA - Treemap D3 + Tabla"]
    
    F["👤 CIUDADANO COLOMBIANO<br/>Sin login | Datos públicos"]
    
    A --> A1
    A --> A2
    A1 --> B
    A2 --> B
    B --> B1
    B --> B2
    B --> B3
    B1 --> C
    B2 --> C
    B3 --> C
    C --> D
    D --> E
    E --> F
```

---

## 2. Flujo de Datos - Drill-Down del Treemap

```mermaid
sequenceDiagram
    participant Usuario
    participant Frontend as Vue 3 SPA
    participant API as FastAPI Backend
    participant BD as PostgreSQL
    
    Usuario->>Frontend: Abre http://localhost:5173
    Frontend->>API: GET /api/meta
    API->>BD: SELECT DISTINCT anio FROM gasto
    BD-->>API: [2023, 2024, 2025]
    API-->>Frontend: {anios: [...], fecha_ingesta: ...}
    Frontend->>Frontend: Renderiza selector año
    
    rect rgb(200, 220, 255)
    Note over Usuario,BD: NIVEL 1: SECTORES
    Usuario->>Frontend: Click en treemap / Selecciona 2025
    Frontend->>API: GET /api/gasto/sectores?anio=2025
    API->>BD: SELECT sector, SUM(apropiadacion_vigente)...<br/>WHERE anio=2025 AND mes=12<br/>GROUP BY sector
    BD-->>API: 32 filas con sectores
    API-->>Frontend: {items: [{SALUD: $66.9T, DEFENSA: $45T, ...}]}
    Frontend->>Frontend: D3 calcula treemap layout<br/>Vue renderiza 32 rectángulos
    end
    
    rect rgb(220, 255, 200)
    Note over Usuario,BD: NIVEL 2: ENTIDADES DEL SECTOR
    Usuario->>Frontend: Click en bloque "SALUD Y PROTECCIÓN SOCIAL"
    Frontend->>API: GET /api/gasto/entidades?anio=2025&sector=SALUD...
    API->>BD: SELECT entidad, SUM(...)<br/>WHERE anio=2025 AND sector=SALUD AND mes=12<br/>GROUP BY entidad
    BD-->>API: 9 filas con entidades
    API-->>Frontend: {items: [{MINSALUD: $64.9T, ...}]}
    Frontend->>Frontend: Treemap re-calcula<br/>Breadcrumb: "Todo > Salud"
    end
    
    rect rgb(255, 220, 200)
    Note over Usuario,BD: NIVEL 3: TIPOS DE GASTO
    Usuario->>Frontend: Click en "MINISTERIO DE SALUD"
    Frontend->>API: GET /api/gasto/tipos?anio=2025&sector=SALUD&entidad=MINSALUD...
    API->>BD: SELECT tipo_gasto, SUM(...)<br/>WHERE anio=2025 AND sector=SALUD<br/>AND entidad=MINSALUD AND mes=12<br/>GROUP BY tipo_gasto
    BD-->>API: 2 filas (FUNCIONAMIENTO, INVERSIÓN)
    API-->>Frontend: {items: [{FUNCIONAMIENTO: $63T, INVERSIÓN: $1.9T}]}
    Frontend->>Frontend: Treemap final (nivel máximo)
    end
    
    Usuario->>Frontend: Click en breadcrumb o toggle tabla
    Frontend->>Frontend: Vuelve a nivel anterior<br/>o cambia vista
```

---

## 3. Estructura de Carpetas y Responsabilidades

```mermaid
graph LR
    subgraph ingesta["📥 Ingesta de Datos (Python)"]
        I1["config.py<br/>Constantes + mapeos"]
        I2["soda_client.py<br/>Cliente SODA"]
        I3["db.py<br/>Engine + tablas"]
        I4["ingestar_gastos.py<br/>ETL: 5phs-yqfw"]
        I5["ingestar_ingresos.py<br/>ETL: 22f3-gynv"]
    end
    
    subgraph backend["🔌 Backend (FastAPI)"]
        B1["main.py<br/>App + CORS"]
        B2["database.py<br/>Conexión + sesión"]
        B3["models.py<br/>SQLAlchemy ORM"]
        B4["schemas.py<br/>Pydantic respuestas"]
        B5["routers/gasto.py<br/>4 endpoints"]
        B6["routers/ingreso.py<br/>2 endpoints"]
    end
    
    subgraph frontend["🎨 Frontend (Vue 3)"]
        F1["App.vue<br/>SPA raíz<br/>3 vistas"]
        F2["stores/explorer.js<br/>Estado global"]
        F3["api/client.js<br/>Fetch wrapper"]
        F4["components/<br/>TreemapExplorer.vue<br/>TablaDetalle.vue<br/>BarraComparativa.vue<br/>IngresosVsGastos.vue<br/>..."]
        F5["utils/formato.js<br/>es-CO currency"]
    end
    
    subgraph data["🗄️ Base de Datos"]
        D1["gasto<br/>45.792 rows"]
        D2["ingreso<br/>3.999 rows"]
    end
    
    I1 --> I4
    I1 --> I5
    I2 --> I4
    I2 --> I5
    I3 --> I4
    I3 --> I5
    I4 --> D1
    I5 --> D2
    
    B1 --> B2
    B2 --> B3
    B1 --> B4
    B1 --> B5
    B1 --> B6
    B3 --> D1
    B3 --> D2
    
    F1 --> F2
    F1 --> F4
    F2 --> F3
    F3 --> B1
    F4 --> F5
    F4 --> F2
    
    style ingesta fill:#fff3e0
    style backend fill:#f3e5f5
    style frontend fill:#e8f5e9
    style data fill:#fce4ec
```

---

## 4. Vistas del Frontend

```mermaid
graph TD
    APP["🎨 APP.VUE - SPA Principal"]
    
    subgraph VISTAS["--- 3 VISTAS ---"]
        V1["📊 EXPLORADOR - Home<br/>━━━━━━━━━━━━━━━<br/>✓ Treemap drill-down 3 niveles<br/>✓ Toggle Mapa/Tabla<br/>✓ Barra apropiado vs pagado<br/>✓ Breadcrumb navegable"]
        
        V2["📈 INGRESOS vs GASTOS<br/>━━━━━━━━━━━━━━━<br/>✓ Gráfica Chart.js<br/>✓ Tabla conceptos con recaudo<br/>✓ Comparativa aforo vs recaudado"]
        
        V3["ℹ️ ACERCA DE<br/>━━━━━━━━━━━━━━━<br/>✓ ¿Qué es PoliTracker?<br/>✓ Links fuentes oficiales<br/>✓ Glosario ciudadano<br/>✓ Fecha última ingesta"]
    end
    
    subgraph NAVEGACION["--- COMPONENTES COMPARTIDOS ---"]
        N1["🗓️ SelectorAnio.vue<br/>2023 | 2024 | 2025"]
        N2["🗂️ Breadcrumb.vue<br/>Todo › Sector › Entidad"]
        N3["🔄 Toggle Mapa/Tabla<br/>Treemap ↔ DataTable"]
    end
    
    APP --> V1
    APP --> V2
    APP --> V3
    
    V1 --> N1
    V1 --> N2
    V1 --> N3
```

---

## 5. Endpoints FastAPI

```mermaid
graph LR
    API["🔌 FASTAPI<br/>localhost:8000<br/>6 ENDPOINTS"]
    
    subgraph GASTO["📊 GASTOS - 4 ENDPOINTS"]
        E1["GET /gasto/sectores?anio<br/>━━━━━━━━━━━━━━━<br/>Responde: 32 sectores<br/>Con: apropiado, pagado, %"]
        E2["GET /gasto/entidades?anio&sector<br/>━━━━━━━━━━━━━━━<br/>Responde: N entidades<br/>Dentro del sector elegido"]
        E3["GET /gasto/tipos?anio&sector&entidad<br/>━━━━━━━━━━━━━━━<br/>Responde: Tipos de gasto<br/>FUNCIONAMIENTO | INVERSIÓN"]
        E4["GET /gasto/serie?anio<br/>━━━━━━━━━━━━━━━<br/>Responde: 12 meses<br/>Apropiado + Pagado"]
    end
    
    subgraph INGRESO["💰 INGRESOS - 2 ENDPOINTS"]
        E5["GET /ingresos/resumen?anio<br/>━━━━━━━━━━━━━━━<br/>Responde: Aforo vs recaudo<br/>Desglose por concepto"]
        E6["GET /meta<br/>━━━━━━━━━━━━━━━<br/>Responde: Años, fecha,<br/>Fuentes oficiales"]
    end
    
    API --> GASTO
    API --> INGRESO
    
    E1 -->|drill-down| E2
    E2 -->|drill-down| E3
```

---

## 6. Propósito Final - Pipeline Completo

```mermaid
graph LR
    A["📊 DATOS BRUTOS<br/>━━━━━━━━━━━━<br/>246K registros<br/>SODA API"]
    
    B["⚙️ PROCESADOS<br/>━━━━━━━━━━━━<br/>Limpieza<br/>Agregación<br/>45K útiles"]
    
    C["💾 ALMACENADOS<br/>━━━━━━━━━━━━<br/>PostgreSQL<br/>Indexed<br/>Upsert"]
    
    D["🔌 SERVIDOS<br/>━━━━━━━━━━━━<br/>FastAPI<br/>6 endpoints<br/>JSON"]
    
    E["🎨 VISUALIZADOS<br/>━━━━━━━━━━━━<br/>Vue 3<br/>D3 Treemap<br/>Chart.js"]
    
    F["👤 ENTENDIBLES<br/>━━━━━━━━━━━━<br/>Ciudadano<br/>Sin login<br/>Sin jerga"]
    
    A -->|Script Python| B
    B -->|INSERT ON CONFLICT| C
    C -->|SELECT ... WHERE| D
    D -->|fetch /api| E
    E -->|Drill-down| F
```

---

## 7. Stack Tecnológico Completo

| Capa | Tecnología | Detalles |
|------|-----------|----------|
| **📥 Datos** | SODA API (datos.gov.co) | 246K registros: 5phs-yqfw (gastos) + 22f3-gynv (ingresos) |
| **⚙️ Ingesta** | Python 3.11 + SQLAlchemy 2.x | Paginación + Upsert + Decimal math (sin float) |
| **🗄️ BD** | PostgreSQL 15 (Puerto 5433) | 45K gastos + 4K ingresos, Indexed, Unique constraints |
| **🔌 Backend** | FastAPI 0.115 + Uvicorn | 6 endpoints REST, Pydantic, CORS habilitado |
| **🎨 Frontend** | Vue 3.5 + Vite 6.4 | SPA, TailwindCSS, D3-hierarchy, Chart.js |
| **☁️ Infra** | Docker + Docker Compose | Orquestación local, volúmenes persistentes |

### Dependencias principales
```
Backend:
  - fastapi==0.115.6
  - sqlalchemy==2.0.36
  - psycopg2-binary==2.9.10
  - uvicorn[standard]==0.34.0

Ingesta:
  - requests==2.32.3
  - python-dotenv==1.0.1

Frontend:
  - vue@3.5.38
  - vite@6.4.3
  - tailwindcss@3.4.19
  - d3-hierarchy@3.1.2
  - chart.js@4.5.1
```

---

## Resumen de Flujo Completo

1. **Minhacienda publica datos en SODA API** → 246K registros de gastos + 10K de ingresos
2. **Script Python descarga y limpia** → Agrega por llave única (sin duplicados)
3. **Upsert a PostgreSQL** → 45K filas de gasto + 4K de ingreso (Oct 2026)
4. **Backend FastAPI query** → 6 endpoints REST que responden en JSON
5. **Frontend Vue hace fetch** → Treemap D3 con drill-down de 3 niveles
6. **Ciudadano colombiano entiende** → Gráficas claras, sin login, datos públicos

---

**Propósito:** Que cualquier ciudadano, sin conocimientos técnicos, entienda en qué se gasta su dinero de impuestos.
