"""Modelos SQLAlchemy (estilo declarativo 2.x) que reflejan el esquema de la ingesta."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Numeric, SmallInteger, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Gasto(Base):
    __tablename__ = "gasto"
    __table_args__ = (
        UniqueConstraint("anio", "mes", "cod_entidad", "tipo_gasto", "detalle_gasto",
                         name="uq_gasto"),
        Index("idx_gasto_anio_sector", "anio", "sector"),
        Index("idx_gasto_anio_entidad", "anio", "sector", "entidad"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    anio: Mapped[int]
    mes: Mapped[int] = mapped_column(SmallInteger)
    sector: Mapped[str] = mapped_column(Text)
    cod_entidad: Mapped[str] = mapped_column(String(30))
    entidad: Mapped[str] = mapped_column(Text)
    tipo_gasto: Mapped[str] = mapped_column(Text)
    detalle_gasto: Mapped[str | None] = mapped_column(Text)
    apropiacion_inicial: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    apropiacion_vigente: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    compromisos: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    obligaciones: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    pagos: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    fuente: Mapped[str] = mapped_column(Text, default="datos.gov.co/5phs-yqfw")
    ingestado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   server_default=func.now())


class Ingreso(Base):
    __tablename__ = "ingreso"
    __table_args__ = (
        UniqueConstraint("anio", "mes", "concepto", name="uq_ingreso"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    anio: Mapped[int]
    mes: Mapped[int] = mapped_column(SmallInteger)
    concepto: Mapped[str] = mapped_column(Text)
    aforo: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    recaudo: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    fuente: Mapped[str] = mapped_column(Text)
    ingestado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   server_default=func.now())
