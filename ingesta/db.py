"""Conexión a PostgreSQL y definición de tablas (SQLAlchemy Core) para la ingesta."""
import logging

from sqlalchemy import (
    BigInteger, Column, DateTime, Index, Integer, MetaData, Numeric,
    SmallInteger, Table, Text, String, UniqueConstraint, create_engine,
)
from sqlalchemy.sql import func

from config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
metadata = MetaData()

gasto = Table(
    "gasto", metadata,
    Column("id", BigInteger, primary_key=True),
    Column("anio", Integer, nullable=False),
    Column("mes", SmallInteger, nullable=False),
    Column("sector", Text, nullable=False),
    Column("cod_entidad", String(30), nullable=False),
    Column("entidad", Text, nullable=False),
    Column("tipo_gasto", Text, nullable=False),
    Column("detalle_gasto", Text),
    Column("apropiacion_inicial", Numeric(20, 2), server_default="0"),
    Column("apropiacion_vigente", Numeric(20, 2), server_default="0"),
    Column("compromisos", Numeric(20, 2), server_default="0"),
    Column("obligaciones", Numeric(20, 2), server_default="0"),
    Column("pagos", Numeric(20, 2), server_default="0"),
    Column("fuente", Text, nullable=False, server_default="datos.gov.co/5phs-yqfw"),
    Column("ingestado_en", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("anio", "mes", "cod_entidad", "tipo_gasto", "detalle_gasto",
                     name="uq_gasto"),
    Index("idx_gasto_anio_sector", "anio", "sector"),
    Index("idx_gasto_anio_entidad", "anio", "sector", "entidad"),
)

ingreso = Table(
    "ingreso", metadata,
    Column("id", BigInteger, primary_key=True),
    Column("anio", Integer, nullable=False),
    Column("mes", SmallInteger, nullable=False),
    Column("concepto", Text, nullable=False),
    Column("aforo", Numeric(20, 2), server_default="0"),
    Column("recaudo", Numeric(20, 2), server_default="0"),
    Column("fuente", Text, nullable=False),
    Column("ingestado_en", DateTime(timezone=True), nullable=False, server_default=func.now()),
    UniqueConstraint("anio", "mes", "concepto", name="uq_ingreso"),
)


def ensure_schema() -> None:
    """Crea las tablas si no existen."""
    metadata.create_all(engine)
    logger.info("Esquema verificado/creado")
