"""Guarda los IDs de lo que se crea en la API, para no duplicar recursos.

Los agents no se pueden borrar, solo archivar. Si cada corrida creara uno
nuevo, la org terminaría llena de agents iguales. Con este archivo, la segunda
corrida reutiliza el mismo agent; si su configuración cambió, se guarda como
una versión nueva del mismo agent.
"""
import hashlib
import json
import os
from collections.abc import Callable
from typing import Any

from taller.config import RAIZ, huella_key

# Un archivo por key: si alguien cambia de org, no reutiliza IDs que esa key no ve.
ARCHIVO = RAIZ / f".estado-{huella_key()}.json"


def _leer() -> dict[str, dict[str, str]]:
    if not ARCHIVO.exists():
        return {}
    return json.loads(ARCHIVO.read_text())


def _escribir(estado: dict[str, dict[str, str]]) -> None:
    # Escribir aparte y reemplazar: un Ctrl+C a mitad no deja el JSON truncado.
    temporal = ARCHIVO.with_suffix(".tmp")
    temporal.write_text(json.dumps(estado, indent=2, ensure_ascii=False) + "\n")
    os.replace(temporal, ARCHIVO)


def huella(spec: Any) -> str:
    texto = json.dumps(spec, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode()).hexdigest()[:16]


def sincronizar(
    clave: str,
    spec: Any,
    crear: Callable[[], Any],
    actualizar: Callable[[str], Any] | None = None,
) -> str:
    """Devuelve el ID del recurso `clave`, creándolo o actualizándolo si hace falta."""
    estado = _leer()
    actual = estado.get(clave)
    nueva = huella(spec)
    if actual and actual["huella"] == nueva:
        return actual["id"]
    if actual and actualizar is not None:
        actualizar(actual["id"])
        recurso_id = actual["id"]
    else:
        recurso_id = crear().id
    estado[clave] = {"id": recurso_id, "huella": nueva}
    _escribir(estado)
    return recurso_id


def ids() -> dict[str, str]:
    return {clave: valor["id"] for clave, valor in _leer().items()}


def olvidar(clave: str) -> None:
    estado = _leer()
    estado.pop(clave, None)
    _escribir(estado)
