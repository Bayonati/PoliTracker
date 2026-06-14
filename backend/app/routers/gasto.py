"""Endpoints de gasto: niveles del treemap y serie mensual.

Regla de agregación (verificada con datos reales del SIIF): los montos
mensuales son ACUMULADOS del año, así que el valor anual es el del último
mes disponible — nunca la suma de los meses.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Gasto
from ..schemas import ItemGasto, PuntoSerie, RespuestaNivel, RespuestaSerie

router = APIRouter(prefix="/api/gasto", tags=["gasto"])


def ultimo_mes(db: Session, anio: int) -> int:
    mes = db.scalar(select(func.max(Gasto.mes)).where(Gasto.anio == anio))
    if mes is None:
        raise HTTPException(
            status_code=404,
            detail=f"No hay datos de gasto para el año {anio}. "
                   f"Verifica los años disponibles en /api/meta.",
        )
    return mes


def construir_respuesta(anio: int, filas) -> RespuestaNivel:
    filas = [f for f in filas if f.apropiado and f.apropiado > 0]
    if not filas:
        raise HTTPException(status_code=404,
                            detail="No hay datos para los filtros pedidos.")
    total_ap = sum(f.apropiado for f in filas)
    total_pg = sum(f.pagado or Decimal(0) for f in filas)
    items = [
        ItemGasto(
            nombre=f.nombre,
            apropiado=str(f.apropiado),
            pagado=str(f.pagado or Decimal(0)),
            porcentaje_del_total=round(float(f.apropiado / total_ap * 100), 1),
            porcentaje_ejecucion=round(float((f.pagado or 0) / f.apropiado * 100), 1),
            num_items=getattr(f, 'num_items', 0),
        )
        for f in filas
    ]
    return RespuestaNivel(
        anio=anio,
        total_apropiado=str(total_ap),
        total_pagado=str(total_pg),
        items=items,
    )


@router.get("/sectores", response_model=RespuestaNivel)
def sectores(anio: int = Query(...), db: Session = Depends(get_db)):
    """Nivel 1 del treemap: el presupuesto repartido por sector."""
    mes = ultimo_mes(db, anio)
    filas = db.execute(
        select(
            Gasto.sector.label("nombre"),
            func.sum(Gasto.apropiacion_vigente).label("apropiado"),
            func.sum(Gasto.pagos).label("pagado"),
            func.count(func.distinct(Gasto.entidad)).label("num_items"),
        )
        .where(Gasto.anio == anio, Gasto.mes == mes)
        .group_by(Gasto.sector)
        .order_by(func.sum(Gasto.apropiacion_vigente).desc())
    ).all()
    return construir_respuesta(anio, filas)


@router.get("/entidades", response_model=RespuestaNivel)
def entidades(anio: int = Query(...), sector: str = Query(...),
              db: Session = Depends(get_db)):
    """Nivel 2: entidades dentro de un sector."""
    mes = ultimo_mes(db, anio)
    filas = db.execute(
        select(
            Gasto.entidad.label("nombre"),
            func.sum(Gasto.apropiacion_vigente).label("apropiado"),
            func.sum(Gasto.pagos).label("pagado"),
            func.count(func.distinct(Gasto.tipo_gasto)).label("num_items"),
        )
        .where(Gasto.anio == anio, Gasto.mes == mes, Gasto.sector == sector)
        .group_by(Gasto.entidad)
        .order_by(func.sum(Gasto.apropiacion_vigente).desc())
    ).all()
    return construir_respuesta(anio, filas)


@router.get("/tipos", response_model=RespuestaNivel)
def tipos(anio: int = Query(...), sector: str = Query(...),
          entidad: str = Query(...), db: Session = Depends(get_db)):
    """Nivel 3: tipos de gasto de una entidad."""
    mes = ultimo_mes(db, anio)
    filas = db.execute(
        select(
            Gasto.tipo_gasto.label("nombre"),
            func.sum(Gasto.apropiacion_vigente).label("apropiado"),
            func.sum(Gasto.pagos).label("pagado"),
            func.count(func.distinct(Gasto.detalle_gasto)).label("num_items"),
        )
        .where(Gasto.anio == anio, Gasto.mes == mes,
               Gasto.sector == sector, Gasto.entidad == entidad)
        .group_by(Gasto.tipo_gasto)
        .order_by(func.sum(Gasto.apropiacion_vigente).desc())
    ).all()
    return construir_respuesta(anio, filas)


@router.get("/serie", response_model=RespuestaSerie)
def serie(anio: int = Query(...), sector: str | None = Query(None),
          entidad: str | None = Query(None), db: Session = Depends(get_db)):
    """Serie mensual: apropiado y pagado acumulados mes a mes."""
    stmt = (
        select(
            Gasto.mes,
            func.sum(Gasto.apropiacion_vigente).label("apropiado"),
            func.sum(Gasto.pagos).label("pagado"),
        )
        .where(Gasto.anio == anio)
        .group_by(Gasto.mes)
        .order_by(Gasto.mes)
    )
    if sector:
        stmt = stmt.where(Gasto.sector == sector)
    if entidad:
        stmt = stmt.where(Gasto.entidad == entidad)
    filas = db.execute(stmt).all()
    if not filas:
        raise HTTPException(status_code=404,
                            detail="No hay datos para los filtros pedidos.")
    return RespuestaSerie(
        anio=anio,
        items=[PuntoSerie(mes=f.mes, apropiado=str(f.apropiado), pagado=str(f.pagado))
               for f in filas],
    )
