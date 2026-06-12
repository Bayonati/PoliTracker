"""Ingesta del dataset de gastos del PGN (5phs-yqfw) hacia la tabla `gasto`.

El dataset crudo tiene más granularidad que nuestro esquema (rubros de 4° y 5°
nivel, fuente de financiación, situación de fondos). Por eso AGREGAMOS los
registros crudos por la llave única (anio, mes, cod_entidad, tipo_gasto,
detalle_gasto) sumando los montos, antes de hacer upsert. Sin esta agregación
el upsert sobrescribiría filas y se perdería plata.
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
logger = logging.getLogger("ingestar_gastos")

BATCH_SIZE = 5_000

# Campos de montos que se suman al agregar
CAMPOS_MONTO = [
    "apropiacion_inicial", "apropiacion_vigente",
    "compromisos", "obligaciones", "pagos",
]


def parse_decimal(valor) -> Decimal:
    """Convierte string de monto a Decimal; vacíos/None cuentan como 0."""
    if valor is None or str(valor).strip() == "":
        return Decimal("0")
    return Decimal(str(valor))


def parse_mes(nombre_mes: str) -> int:
    """Nombre de mes en español -> número 1-12, tolerante a mayúsculas/tildes."""
    clave = (
        str(nombre_mes).strip().lower()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u")
    )
    if clave not in config.MESES:
        raise ValueError(f"Mes desconocido: {nombre_mes!r}")
    return config.MESES[clave]


def verificar_campos() -> None:
    """Aborta si el dataset no tiene los campos que espera el mapeo de config."""
    muestra = fetch_sample(config.DATASET_GASTOS, n=3)
    if not muestra:
        logger.error("El dataset %s no devolvió registros de muestra", config.DATASET_GASTOS)
        sys.exit(1)
    presentes = set()
    for reg in muestra:
        presentes.update(reg.keys())
    faltantes = set(config.CAMPOS_GASTO) - presentes
    if faltantes:
        logger.error(
            "ABORTANDO: el dataset no tiene los campos esperados %s. "
            "Campos reales: %s", sorted(faltantes), sorted(presentes),
        )
        sys.exit(1)
    logger.info("Campos del dataset verificados: %s", sorted(config.CAMPOS_GASTO))


def ingestar_anio(anio: int) -> dict:
    """Descarga, agrega y upserta todos los registros de un año."""
    logger.info("=== Año %s: descargando ===", anio)
    agregados: dict[tuple, dict] = {}
    procesados = 0
    saltados = 0

    for reg in fetch_all(config.DATASET_GASTOS, where=f"anio='{anio}'"):
        procesados += 1
        try:
            mes = parse_mes(reg["nombremes"])
            detalle = (reg.get("nombredetallegasto") or "").strip()
            llave = (anio, mes, reg["codigoentidad"].strip(),
                     reg["nombretipogasto"].strip(), detalle)
            if llave not in agregados:
                agregados[llave] = {
                    "anio": anio,
                    "mes": mes,
                    "sector": reg["sector"].strip(),
                    "cod_entidad": llave[2],
                    "entidad": reg["nombreentidad"].strip(),
                    "tipo_gasto": llave[3],
                    "detalle_gasto": detalle,
                    "fuente": config.FUENTE_GASTOS,
                    **{c: Decimal("0") for c in CAMPOS_MONTO},
                }
            fila = agregados[llave]
            fila["apropiacion_inicial"] += parse_decimal(reg.get("apropiacioninicial"))
            fila["apropiacion_vigente"] += parse_decimal(reg.get("apropiacionvigente"))
            fila["compromisos"] += parse_decimal(reg.get("compromisos"))
            fila["obligaciones"] += parse_decimal(reg.get("obligaciones"))
            fila["pagos"] += parse_decimal(reg.get("pagos"))
        except (KeyError, ValueError, InvalidOperation) as exc:
            saltados += 1
            logger.error("Registro saltado (%s): %r", exc, reg)

    logger.info("Año %s: %s registros crudos -> %s filas agregadas (%s saltados)",
                anio, f"{procesados:,}", f"{len(agregados):,}", saltados)

    filas = list(agregados.values())
    upserteadas = 0
    with db.engine.begin() as conn:
        for i in range(0, len(filas), BATCH_SIZE):
            lote = filas[i:i + BATCH_SIZE]
            stmt = pg_insert(db.gasto).values(lote)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_gasto",
                set_={
                    "sector": stmt.excluded.sector,
                    "entidad": stmt.excluded.entidad,
                    **{c: getattr(stmt.excluded, c) for c in CAMPOS_MONTO},
                    "fuente": stmt.excluded.fuente,
                    "ingestado_en": text("now()"),
                },
            )
            conn.execute(stmt)
            upserteadas += len(lote)
            logger.info("Año %s: lote upserteado (%s/%s filas)",
                        anio, f"{upserteadas:,}", f"{len(filas):,}")

    return {"procesados": procesados, "filas": len(filas), "saltados": saltados}


def verificacion_cordura() -> None:
    """El total vigente del último mes del año más reciente debe rondar los
    cientos de billones de COP (PGN 2025 ~ $523 billones)."""
    sql = text("""
        SELECT anio, mes, SUM(apropiacion_vigente) AS total
        FROM gasto
        WHERE anio = (SELECT MAX(anio) FROM gasto)
          AND mes = (SELECT MAX(mes) FROM gasto g2 WHERE g2.anio = gasto.anio)
        GROUP BY anio, mes
    """)
    with db.engine.connect() as conn:
        fila = conn.execute(sql).first()
    if fila is None:
        logger.error("Verificación de cordura: la tabla gasto quedó vacía")
        sys.exit(1)
    total = fila.total
    billones = total / Decimal("1000000000000")
    logger.info("Cordura: año %s mes %s -> apropiación vigente total = $%.1f billones COP",
                fila.anio, fila.mes, billones)
    if not (Decimal("100") <= billones <= Decimal("2000")):
        logger.error(
            "El total ($%s) está fuera del orden de magnitud esperado "
            "(cientos de billones). Revisa la conversión de montos.", total,
        )
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
    logger.info("Ingesta de gastos terminada OK")


if __name__ == "__main__":
    main()
