# PoliTracker - Arquitectura y Flujos

## 1. Arquitectura General del Sistema

```mermaid
graph TD
    A["🌐 Fuentes de Datos Oficiales<br/>(datos.gov.co - Minhacienda)"]
    
    A1["Dataset 5phs-yqfw<br/>Gastos del PGN<br/>246K registros"]
    A2["Dataset 22f3-gynv<br/>Ingresos por Vigencia<br/>10K registros"]
    
    B["⚙️ Ingesta de Datos<br/>(Python)"]
    B1["soda_client.py<br/>Paginación + Reintentos"]
    B2["ingestar_gastos.py<br/>Agrega + Upsert"]
    B3["ingestar_ingresos.py<br/>Agrega + Upsert"]
    
    C["🗄️ PostgreSQL 15<br/>(Puerto 5433)<br/>45K gastos + 4K ingresos"]
    
    D["🔌 Backend FastAPI<br/>(Puerto 8000)<br/>6 endpoints REST"]
    
    E["🎨 Frontend Vue 3<br/>(Puerto 5173)<br/>SPA Interactivo"]
    
    F["👤 Ciudadano Colombiano<br/>(Sin login)<br/>Datos públicos + claros"]
    
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
    
    style A fill:#e1f5ff
    style C fill:#fff3e0
    style D fill:#f3e5f5
    style E fill:#e8f5e9
    style F fill:#fce4ec
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
    APP["App.vue<br/>SPA Principal"]
    
    subgraph VISTAS["3 VISTAS"]
        V1["📊 EXPLORADOR<br/>(Home)<br/>- Treemap drill-down<br/>- Toggle mapa/tabla<br/>- Barra ejecución<br/>- Breadcrumb"]
        
        V2["📈 INGRESOS vs GASTOS<br/>- Gráfica Chart.js<br/>- Tabla conceptos<br/>- Comparativa aforo/recaudo"]
        
        V3["ℹ️ ACERCA DE<br/>- ¿Qué es PoliTracker?<br/>- Links fuentes oficiales<br/>- Glosario ciudadano<br/>- Fecha ingesta"]
    end
    
    subgraph NAVEGACION["NAVEGACIÓN"]
        N1["Selector Año<br/>2023, 2024, 2025"]
        N2["Breadcrumb<br/>Todo > Sector > Entidad"]
        N3["Toggle Mapa/Tabla<br/>D3 vs DataTable"]
    end
    
    APP --> V1
    APP --> V2
    APP --> V3
    
    V1 --> N1
    V1 --> N2
    V1 --> N3
    
    style APP fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style V1 fill:#c8e6c9
    style V2 fill:#c8e6c9
    style V3 fill:#c8e6c9
    style N1 fill:#a5d6a7
    style N2 fill:#a5d6a7
    style N3 fill:#a5d6a7
```

---

## 5. Endpoints FastAPI

```mermaid
graph LR
    API["🔌 FastAPI<br/>localhost:8000"]
    
    subgraph GASTO["Gasto - 4 Endpoints"]
        E1["GET /gasto/sectores?anio<br/>→ 32 sectores + montos"]
        E2["GET /gasto/entidades?anio&sector<br/>→ N entidades del sector"]
        E3["GET /gasto/tipos?anio&sector&entidad<br/>→ Tipos de gasto"]
        E4["GET /gasto/serie?anio&sector&entidad<br/>→ Serie mensual"]
    end
    
    subgraph INGRESO["Ingresos - 2 Endpoints"]
        E5["GET /ingresos/resumen?anio<br/>→ Aforo vs recaudo + conceptos"]
        E6["GET /meta<br/>→ Años, fecha ingesta, fuentes"]
    end
    
    API --> GASTO
    API --> INGRESO
    
    E1 -.Drill-down.-> E2
    E2 -.Drill-down.-> E3
    E4 -.Serie temporal.-> E1
    
    style API fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px
    style E1 fill:#ce93d8
    style E2 fill:#ce93d8
    style E3 fill:#ce93d8
    style E4 fill:#ce93d8
    style E5 fill:#ba68c8
    style E6 fill:#ba68c8
```

---

## 6. Propósito Final

```mermaid
graph LR
    A["📊 Datos Brutos<br/>246K registros SODA"]
    B["⚙️ Procesados<br/>Limpieza + Agregación<br/>45K registros útiles"]
    C["💾 Almacenados<br/>PostgreSQL<br/>Consultas rápidas"]
    D["🔌 Servidos<br/>FastAPI REST<br/>JSON con montos"]
    E["🎨 Visualizados<br/>Vue 3 + D3<br/>Treemap interactivo"]
    F["👤 Entendibles<br/>Ciudadano colombiano<br/>Sin login, sin jerga"]
    
    A -->|Ingesta| B
    B -->|Upsert| C
    C -->|Queries SQL| D
    D -->|APIs REST| E
    E -->|UI/UX clara| F
    
    style A fill:#fff3e0
    style B fill:#fff9c4
    style C fill:#fce4ec
    style D fill:#f3e5f5
    style E fill:#e8f5e9
    style F fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
```

---

## 7. Stack Tecnológico

```mermaid
graph TB
    subgraph DATOS["📥 Datos"]
        D1["SODA API<br/>datos.gov.co"]
        D2["5phs-yqfw<br/>Gastos"]
        D3["22f3-gynv<br/>Ingresos"]
    end
    
    subgraph INGESTA["⚙️ Procesamiento"]
        I1["Python 3.11"]
        I2["SQLAlchemy 2.x<br/>Decimal math"]
        I3["Requests<br/>HTTP client"]
    end
    
    subgraph BD["🗄️ Persistencia"]
        B1["PostgreSQL 15"]
        B2["Upsert<br/>Sin duplicados"]
    end
    
    subgraph BACKEND["🔌 API"]
        BA["FastAPI 0.115"]
        BA1["Pydantic"]
        BA2["Uvicorn"]
    end
    
    subgraph FRONTEND["🎨 Web"]
        F1["Vue 3.5<br/>SPA"]
        F2["Vite 6.4<br/>Dev server"]
        F3["TailwindCSS"]
        F4["D3-hierarchy<br/>Treemap"]
        F5["Chart.js<br/>Gráficas"]
    end
    
    subgraph INFRA["☁️ Infraestructura"]
        INF1["Docker"]
        INF2["Docker Compose"]
    end
    
    D1 --> D2
    D1 --> D3
    D2 --> I1
    D3 --> I1
    I1 --> I2
    I1 --> I3
    I2 --> B1
    B1 --> B2
    B2 --> BA
    BA --> BA1
    BA --> BA2
    BA --> F1
    F1 --> F2
    F1 --> F3
    F1 --> F4
    F1 --> F5
    INF1 --> B1
    INF2 --> INF1
    
    style DATOS fill:#fff3e0
    style INGESTA fill:#fff9c4
    style BD fill:#fce4ec
    style BACKEND fill:#f3e5f5
    style FRONTEND fill:#e8f5e9
    style INFRA fill:#e0f2f1
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
