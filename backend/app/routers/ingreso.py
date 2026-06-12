"""Endpoints de ingresos y metadatos de la plataforma."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, union
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Gasto, Ingreso
from ..schemas import ItemIngreso, RespuestaIngresos, RespuestaMeta

router = APIRouter(prefix="/api", tags=["ingresos"])


@router.get("/ingresos/resumen", response_model=RespuestaIngresos)
def resumen(anio: int = Query(...), db: Session = Depends(get_db)):
    """Total aforo vs recaudo del año (último mes acumulado) y desglose por
    concepto. Incluye el total de gasto del mismo año para la vista
    Ingresos vs Gastos."""
    mes = db.scalar(select(func.max(Ingreso.mes)).where(Ingreso.anio == anio))
    if mes is None:
        raise HTTPException(status_code=404,
                            detail=f"No hay datos de ingresos para el año {anio}.")
    filas = db.execute(
        select(
            Ingreso.concepto,
            func.sum(Ingreso.aforo).label("aforo"),
            func.sum(Ingreso.recaudo).label("recaudo"),
        )
        .where(Ingreso.anio == anio, Ingreso.mes == mes)
        .group_by(Ingreso.concepto)
        .order_by(func.sum(Ingreso.aforo).desc())
    ).all()
    filas = [f for f in filas if (f.aforo or 0) > 0 or (f.recaudo or 0) > 0]
    total_aforo = sum(f.aforo or Decimal(0) for f in filas)
    total_recaudo = sum(f.recaudo or Decimal(0) for f in filas)

    # Total de gasto del mismo año para comparar entra vs sale
    mes_gasto = db.scalar(select(func.max(Gasto.mes)).where(Gasto.anio == anio))
    gasto_ap = gasto_pg = Decimal(0)
    if mes_gasto is not None:
        fila_g = db.execute(
            select(
                func.sum(Gasto.apropiacion_vigente).label("ap"),
                func.sum(Gasto.pagos).label("pg"),
            ).where(Gasto.anio == anio, Gasto.mes == mes_gasto)
        ).first()
        gasto_ap = fila_g.ap or Decimal(0)
        gasto_pg = fila_g.pg or Decimal(0)

    return RespuestaIngresos(
        anio=anio,
        total_aforo=str(total_aforo),
        total_recaudo=str(total_recaudo),
        total_gasto_apropiado=str(gasto_ap),
        total_gasto_pagado=str(gasto_pg),
        items=[
            ItemIngreso(
                concepto=f.concepto,
                aforo=str(f.aforo or Decimal(0)),
                recaudo=str(f.recaudo or Decimal(0)),
                porcentaje_recaudo=round(float((f.recaudo or 0) / f.aforo * 100), 1)
                if f.aforo and f.aforo > 0 else 0.0,
            )
            for f in filas
        ],
    )


@router.get("/meta", response_model=RespuestaMeta)
def meta(db: Session = Depends(get_db)):
    """Años disponibles, fecha de última ingesta y fuentes oficiales."""
    anios_gasto = select(Gasto.anio).distinct()
    anios_ingreso = select(Ingreso.anio).distinct()
    anios = sorted({a for (a,) in db.execute(union(anios_gasto, anios_ingreso))})
    ultima = db.scalar(select(func.max(Gasto.ingestado_en)))
    ultima_ing = db.scalar(select(func.max(Ingreso.ingestado_en)))
    if ultima is None or (ultima_ing is not None and ultima_ing > ultima):
        ultima = ultima_ing
    fuentes = sorted({
        f for (f,) in db.execute(
            union(select(Gasto.fuente).distinct(), select(Ingreso.fuente).distinct())
        )
    })
    return RespuestaMeta(
        anios=anios,
        ultima_ingesta=ultima.isoformat() if ultima else None,
        fuentes=fuentes,
    )
