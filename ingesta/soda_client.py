"""Cliente genérico para la API SODA de datos.gov.co con paginación y reintentos."""
import logging
import time
from typing import Iterator, Optional

import requests

from config import SODA_APP_TOKEN, SODA_BASE_URL

logger = logging.getLogger(__name__)

PAGE_SIZE = 50_000
TIMEOUT = 60
MAX_RETRIES = 3


def _headers() -> dict:
    h = {"Accept": "application/json"}
    if SODA_APP_TOKEN:
        h["X-App-Token"] = SODA_APP_TOKEN
    return h


def _get_with_retries(url: str, params: dict) -> list[dict]:
    """GET con backoff exponencial (2s, 4s, 8s) ante 429 o 5xx."""
    for intento in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=_headers(), timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                espera = 2 ** (intento + 1)
                logger.warning(
                    "HTTP %s de la API SODA, reintento %s/%s en %ss",
                    resp.status_code, intento + 1, MAX_RETRIES, espera,
                )
                time.sleep(espera)
                continue
            resp.raise_for_status()
        except requests.RequestException as exc:
            if intento >= MAX_RETRIES:
                raise
            espera = 2 ** (intento + 1)
            logger.warning("Error de red (%s), reintento en %ss", exc, espera)
            time.sleep(espera)
    raise RuntimeError(f"API SODA no respondió tras {MAX_RETRIES} reintentos: {url}")


def fetch_all(dataset_id: str, where: Optional[str] = None,
              select: Optional[str] = None) -> Iterator[dict]:
    """Generador que pagina automáticamente todo el dataset.

    Ordena por :id para que la paginación sea estable y no duplique registros.
    """
    url = f"{SODA_BASE_URL}/{dataset_id}.json"
    offset = 0
    pagina = 0
    total = 0
    while True:
        params = {"$limit": PAGE_SIZE, "$offset": offset, "$order": ":id"}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        registros = _get_with_retries(url, params)
        if not registros:
            break
        pagina += 1
        total += len(registros)
        logger.info("Página %s — %s registros acumulados", pagina, f"{total:,}".replace(",", "."))
        yield from registros
        if len(registros) < PAGE_SIZE:
            break
        offset += PAGE_SIZE


def fetch_sample(dataset_id: str, n: int = 5) -> list[dict]:
    """Trae n registros para inspeccionar los campos reales del dataset."""
    url = f"{SODA_BASE_URL}/{dataset_id}.json"
    return _get_with_retries(url, {"$limit": n})
