"""Schemas Pydantic de respuesta. Los montos van como string para no perder
precisión al serializar NUMERIC como float de JSON."""
from pydantic import BaseModel


class ItemGasto(BaseModel):
    nombre: str
    apropiado: str
    pagado: str
    porcentaje_del_total: float
    porcentaje_ejecucion: float
    num_items: int = 0


class RespuestaNivel(BaseModel):
    anio: int
    total_apropiado: str
    total_pagado: str
    items: list[ItemGasto]


class PuntoSerie(BaseModel):
    mes: int
    apropiado: str
    pagado: str


class RespuestaSerie(BaseModel):
    anio: int
    items: list[PuntoSerie]


class ItemIngreso(BaseModel):
    concepto: str
    aforo: str
    recaudo: str
    porcentaje_recaudo: float


class RespuestaIngresos(BaseModel):
    anio: int
    total_aforo: str
    total_recaudo: str
    total_gasto_apropiado: str
    total_gasto_pagado: str
    items: list[ItemIngreso]


class RespuestaMeta(BaseModel):
    anios: list[int]
    ultima_ingesta: str | None
    fuentes: list[str]
