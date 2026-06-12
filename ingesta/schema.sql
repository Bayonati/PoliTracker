-- Esquema de referencia de PoliTracker (las tablas se crean desde db.py con SQLAlchemy)

CREATE TABLE IF NOT EXISTS gasto (
    id              BIGSERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    mes             SMALLINT NOT NULL,          -- 1-12 (nombres de mes convertidos a número en la ingesta)
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

CREATE INDEX IF NOT EXISTS idx_gasto_anio_sector ON gasto (anio, sector);
CREATE INDEX IF NOT EXISTS idx_gasto_anio_entidad ON gasto (anio, sector, entidad);

CREATE TABLE IF NOT EXISTS ingreso (
    id              BIGSERIAL PRIMARY KEY,
    anio            INTEGER NOT NULL,
    mes             SMALLINT NOT NULL,
    concepto        TEXT NOT NULL,              -- nombrerubro del dataset 22f3-gynv
    aforo           NUMERIC(20,2) DEFAULT 0,    -- lo presupuestado a recaudar
    recaudo         NUMERIC(20,2) DEFAULT 0,    -- recaudo efectivo acumulado del año
    fuente          TEXT NOT NULL,
    ingestado_en    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ingreso UNIQUE (anio, mes, concepto)
);
