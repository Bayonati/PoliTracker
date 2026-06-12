"""Ingesta del dataset de ingresos del PGN (22f3-gynv) hacia la tabla `ingreso`.

El dataset trae varias filas por rubro/mes (separadas por fuente de
financiación y situación de fondos), así que agregamos por
(anio, mes, concepto=nombrerubro) sumando aforo vigente y recaudo acumulado.
"""
import logging
import sys
from decimal import Decimal, InvalidOperation

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert

import config
import db
from soda_client import fetch_all, fetch_sample

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ingestar_ingresos")

BATCH_SIZE = 5_000


def parse_decimal(valor) -> Decimal:
    if valor is None or str(valor).strip() == "":
        return Decimal("0")
    return Decimal(str(valor))


def verificar_campos() -> None:
    muestra = fetch_sample(config.DATASET_INGRESOS, n=3)
    if not muestra:
        logger.error("El dataset %s no devolvió registros de muestra", config.DATASET_INGRESOS)
        sys.exit(1)
    presentes = set()
    for reg in muestra:
        presentes.update(reg.keys())
    faltantes = set(config.CAMPOS_INGRESO) - presentes
    if faltantes:
        logger.error("ABORTANDO: faltan campos %s. Campos reales: %s",
                     sorted(faltantes), sorted(presentes))
        sys.exit(1)
    logger.info("Campos del dataset de ingresos verificados")


def ingestar_anio(anio: int) -> dict:
    logger.info("=== Año %s: descargando ingresos ===", anio)
    agregados: dict[tuple, dict] = {}
    procesados = 0
    saltados = 0

    for reg in fetch_all(config.DATASET_INGRESOS, where=f"anio='{anio}'"):
        procesados += 1
        try:
            mes = int(reg["numeromes"])
            if not 1 <= mes <= 12:
                raise ValueError(f"Mes fuera de rango: {mes}")
            concepto = (reg.get("nombrerubro") or "").strip()
            if not concepto:
                raise ValueError("Rubro vacío")
            llave = (anio, mes, concepto)
            if llave not in agregados:
                agregados[llave] = {
                    "anio": anio, "mes": mes, "concepto": concepto,
                    "aforo": Decimal("0"), "recaudo": Decimal("0"),
                    "fuente": config.FUENTE_INGRESOS,
                }
            fila = agregados[llave]
            fila["aforo"] += parse_decimal(reg.get("aforovigente"))
            fila["recaudo"] += parse_decimal(reg.get("recaudoefectivoacumulado"))
        except (KeyError, ValueError, InvalidOperation) as exc:
            saltados += 1
            logger.error("Registro saltado (%s): %r", exc, reg)

    logger.info("Año %s: %s crudos -> %s filas agregadas (%s saltados)",
                anio, f"{procesados:,}", f"{len(agregados):,}", saltados)

    filas = list(agregados.values())
    with db.engine.begin() as conn:
        for i in range(0, len(filas), BATCH_SIZE):
            lote = filas[i:i + BATCH_SIZE]
            stmt = pg_insert(db.ingreso).values(lote)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_ingreso",
                set_={
                    "aforo": stmt.excluded.aforo,
                    "recaudo": stmt.excluded.recaudo,
                    "fuente": stmt.excluded.fuente,
                    "ingestado_en": text("now()"),
                },
            )
            conn.execute(stmt)
            logger.info("Año %s: lote upserteado (%s filas)", anio, len(lote))

    return {"procesados": procesados, "filas": len(filas), "saltados": saltados}


def verificacion_cordura() -> None:
    """El aforo total del último mes del año más reciente debe rondar los
    cientos de billones de COP."""
    sql = text("""
        SELECT anio, mes, SUM(aforo) AS total
        FROM ingreso
        WHERE anio = (SELECT MAX(anio) FROM ingreso)
          AND mes = (SELECT MAX(mes) FROM ingreso i2 WHERE i2.anio = ingreso.anio)
        GROUP BY anio, mes
    """)
    with db.engine.connect() as conn:
        fila = conn.execute(sql).first()
    if fila is None:
        logger.error("Verificación de cordura: la tabla ingreso quedó vacía")
        sys.exit(1)
    billones = fila.total / Decimal("1000000000000")
    logger.info("Cordura: año %s mes %s -> aforo total = $%.1f billones COP",
                fila.anio, fila.mes, billones)
    if not (Decimal("100") <= billones <= Decimal("2000")):
        logger.error("Aforo total fuera del orden de magnitud esperado: %s", fila.total)
        sys.exit(1)


def main() -> None:
    db.ensure_schema()
    verificar_campos()
    resumen = {}
    for anio in config.ANIOS_INGESTA:
        resumen[anio] = ingestar_anio(anio)
    logger.info("=== RESUMEN ===")
    for anio, r in resumen.items():
        logger.info("Año %s: %s crudos, %s filas upserteadas, %s saltados",
                    anio, f"{r['procesados']:,}", f"{r['filas']:,}", r["saltados"])
    verificacion_cordura()
    logger.info("Ingesta de ingresos terminada OK")


if __name__ == "__main__":
    main()
