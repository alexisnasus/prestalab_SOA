"""
Bus Client robusto para registro/heartbeats y llamadas entre servicios.

- Usa BUS_URL (o BUS_HOST/BUS_PORT) para hablar con el bus.
- /register y /heartbeat incluyen fallback TCP crudo para tolerar respuestas HTTP no estándares.
- call_service_via_bus intenta /route; si el bus no enruta, hace fallback directo a http://<servicio>:8000.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# =========================
# Config
# =========================
BUS_URL = os.getenv("BUS_URL") or f"http://{os.getenv('BUS_HOST','bus')}:{os.getenv('BUS_PORT','5000')}"
MAX_RETRIES = int(os.getenv("BUS_REGISTER_RETRIES", "10"))
RETRY_DELAY = float(os.getenv("BUS_REGISTER_DELAY", "2.5"))  # segundos
HEARTBEAT_INTERVAL = int(os.getenv("BUS_HEARTBEAT_INTERVAL", "30"))

# Puerto interno por defecto de los microservicios (expuestos como 8001.. en el host)
SERVICE_PORT = os.getenv("SERVICE_PORT", "8000")

# Parse para fallback TCP
_parsed = urlparse(BUS_URL)
BUS_SCHEME = _parsed.scheme or "http"
BUS_HOST = _parsed.hostname or "bus"
BUS_PORT = _parsed.port or 5000


# =========================
# Utilidades internas
# =========================
async def _sleep_backoff(attempt: int) -> None:
    """Backoff lineal con ligero jitter."""
    delay = RETRY_DELAY * (1 + 0.15 * attempt)
    await asyncio.sleep(delay)


async def _post_httpx(path: str, payload: Optional[dict], timeout: float = 5.0) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
        return await client.post(f"{BUS_URL}{path}", json=payload)


async def _post_raw_tcp(path: str, payload: Optional[dict], timeout: float = 5.0) -> bool:
    """
    Fallback: envía un POST HTTP/1.0 “manual” por socket y no valida la status line.
    Considera éxito si pudo escribir y leer algo del socket sin excepciones.
    """
    body = b""
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = (
        f"POST {path} HTTP/1.0\r\n"
        f"Host: {BUS_HOST}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii") + body

    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(BUS_HOST, BUS_PORT), timeout=timeout)
        writer.write(req)
        await writer.drain()
        # Leemos sin validar headers/status (el bus puede responder con status line “rara”)
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(reader.read(64 * 1024), timeout=timeout)
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return True
    except Exception as e:
        logger.debug(f"Fallback TCP falló: {e}")
        return False


# =========================
# API pública
# =========================
async def register_service(
    app: FastAPI,
    service_name: str,
    service_url: str,
    description: Optional[str] = None,
    version: str = "1.0.0",
    custom_endpoints: Optional[List[str]] = None,
) -> bool:
    """
    Registra el servicio en el bus (con reintentos y fallback TCP).
    """
    # Recolectar endpoints de la app si no se pasan explícitos
    if custom_endpoints is None:
        endpoints = sorted({getattr(r, "path", None) for r in app.routes if getattr(r, "path", None)})
    else:
        endpoints = list(custom_endpoints)

    data = {
        "service_name": service_name,
        "service_url": service_url,
        "description": description or f"Servicio {service_name}",
        "version": version,
        "endpoints": endpoints,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = await _post_httpx("/register", data, timeout=6.0)
            if resp.status_code in (200, 201):
                logger.info(f"[{service_name}] [OK] REGISTERED -> {BUS_URL} (endpoints={len(endpoints)})")
                return True
            else:
                logger.warning(f"[{service_name}] Bus respondió {resp.status_code}: {resp.text[:200]}")
        except (httpx.RemoteProtocolError, httpx.LocalProtocolError) as e:
            logger.warning(f"[{service_name}] Protocolo no estándar del bus ({type(e).__name__}). Fallback TCP…")
            ok = await _post_raw_tcp("/register", data, timeout=6.0)
            if ok:
                logger.info(f"[{service_name}] [OK] REGISTERED (fallback TCP) -> {BUS_HOST}:{BUS_PORT}")
                return True
        except httpx.ConnectError:
            logger.warning(f"[{service_name}] Intento {attempt}/{MAX_RETRIES}: bus no disponible en {BUS_URL}")
        except Exception as e:
            logger.warning(f"[{service_name}] Error registrando: {type(e).__name__}: {e}")

        if attempt < MAX_RETRIES:
            await _sleep_backoff(attempt)

    logger.error(
        f"[{service_name}] ✗ No se pudo registrar en el bus tras {MAX_RETRIES} intentos. "
        "El servicio seguirá funcionando pero no será descubrible."
    )
    return False


async def send_heartbeat(service_name: str) -> bool:
    """
    Envía un heartbeat al bus. Fallback TCP si la respuesta HTTP es no estándar.
    """
    try:
        resp = await _post_httpx(f"/heartbeat/{service_name}", None, timeout=4.0)
        return resp.status_code == 200
    except (httpx.RemoteProtocolError, httpx.LocalProtocolError):
        ok = await _post_raw_tcp(f"/heartbeat/{service_name}", None, timeout=4.0)
        return ok
    except Exception:
        return False


def setup_heartbeat(service_name: str, interval: int = HEARTBEAT_INTERVAL) -> None:
    """
    Lanza una tarea periódica para enviar heartbeats.
    """
    async def heartbeat_task():
        while True:
            await asyncio.sleep(interval)
            ok = await send_heartbeat(service_name)
            if not ok:
                logger.debug(f"[{service_name}] heartbeat falló (se reintenta)")

    asyncio.create_task(heartbeat_task())


async def call_service_via_bus(
    target_service: str,
    method: str,
    endpoint: str,
    payload: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """
    Llama a otro servicio:
      1) Intenta /route del bus (por si existe en tu implementación).
      2) Si /route no sirve (eco o protocolo raro), hace fallback DIRECTO a http://<servicio>:8000.
    Devuelve JSON si es posible; si no, {status_code, text}.
    """
    # 1) Intento vía /route (si el bus llegara a enrutar en el futuro)
    try:
        async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
            r = await client.post(
                f"{BUS_URL}/route",
                json={
                    "target_service": target_service,
                    "method": method,
                    "endpoint": endpoint,
                    "payload": payload,
                },
            )
        try:
            j = r.json()
            # Si el bus implementa enrutado “real”, suele devolver {"success": true, "data": ...}
            if isinstance(j, dict) and j.get("success") is True:
                return j.get("data")
        except Exception:
            # cuerpo no-JSON o un “eco”; seguimos al fallback
            pass
    except Exception:
        # errores de conexión/protocolo: seguimos al fallback
        pass

    # 2) Fallback DIRECTO (DNS interno de Docker)
    url = f"http://{target_service}:{SERVICE_PORT}{endpoint}"
    async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
        m = method.upper()
        if m == "GET":
            resp = await client.get(url, params=payload or {})
        elif m == "POST":
            resp = await client.post(url, json=payload or {})
        elif m == "PUT":
            resp = await client.put(url, json=payload or {})
        elif m == "DELETE":
            resp = await client.delete(url, json=payload or {})
        else:
            raise ValueError(f"Método no soportado: {method}")

    try:
        return resp.json()
    except Exception:
        return {"status_code": resp.status_code, "text": resp.text}
