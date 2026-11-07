"""Crear y reutilizar environments, agents y archivos; bajar los outputs de una sesión."""
import hashlib
import time
from pathlib import Path
from typing import Any

import anthropic

from taller import estado
from taller.config import BETA, SALIDAS


def guardar_entorno(client: anthropic.Anthropic, clave: str, config: dict[str, Any]) -> str:
    return estado.sincronizar(
        f"entorno:{clave}",
        config,
        crear=lambda: client.beta.environments.create(name=f"taller-{clave}", config=config),
        actualizar=lambda env_id: client.beta.environments.update(env_id, config=config),
    )


def guardar_agente(client: anthropic.Anthropic, clave: str, config: dict[str, Any]) -> str:
    """Crea el agent una vez. Si su configuración cambia, guarda una versión nueva."""

    def actualizar(agent_id: str) -> Any:
        version = client.beta.agents.retrieve(agent_id).version
        return client.beta.agents.update(agent_id, version=version, **config)

    return estado.sincronizar(
        f"agente:{clave}",
        config,
        crear=lambda: client.beta.agents.create(**config),
        actualizar=actualizar,
    )


def subir_archivo(client: anthropic.Anthropic, ruta: Path) -> str:
    def subir() -> Any:
        with ruta.open("rb") as f:
            return client.beta.files.upload(file=(ruta.name, f))

    # Si el contenido cambia, se sube de nuevo; si no, se reutiliza el mismo archivo.
    contenido = hashlib.sha256(ruta.read_bytes()).hexdigest()
    return estado.sincronizar(f"archivo:{ruta.resolve()}", contenido, crear=subir)


def bajar_salidas(
    client: anthropic.Anthropic,
    session_id: str,
    espera_max: float = 30,
    subidos: tuple[str, ...] = (),
) -> list[Path]:
    """Baja lo que el agente dejó en /mnt/session/outputs/.

    Los archivos aparecen unos segundos después de que la sesión queda idle, así
    que se consulta hasta que la lista deje de crecer o se acabe la espera.
    subidos: IDs de los archivos que tú montaste. La sesión los lista como copias
    con otro ID, así que se reconocen por nombre y tamaño y no se bajan como si
    fueran resultados del agente.
    """
    montados = set()
    for file_id in subidos:
        original = client.beta.files.retrieve_metadata(file_id, betas=[BETA])
        montados.add((original.filename, original.size_bytes))
    destino = SALIDAS / session_id
    limite = time.monotonic() + espera_max
    archivos: dict[str, Any] = {}
    estable = 0
    while time.monotonic() < limite and estable < 2:
        antes = set(archivos)
        for archivo in client.beta.files.list(scope_id=session_id, betas=[BETA]):
            if (archivo.filename, archivo.size_bytes) not in montados:
                archivos[archivo.id] = archivo
        # Dos consultas seguidas sin archivos nuevos: se da por completa la lista.
        estable = estable + 1 if archivos and set(archivos) == antes else 0
        time.sleep(3)

    if not archivos:
        print(f"El agente no dejó archivos en /mnt/session/outputs/ (esperé {espera_max:.0f} s).")
        return []
    if estable < 2:
        print(f"Bajando lo que apareció en {espera_max:.0f} s. Si falta algo, vuelve a llamar bajar_salidas.")

    destino.mkdir(parents=True, exist_ok=True)
    rutas = []
    for archivo in archivos.values():
        ruta = destino / Path(archivo.filename).name
        # Dos outputs con el mismo nombre (o que solo cambian en mayúsculas, que en
        # macOS es el mismo archivo) no se pisan.
        if ruta.name.lower() in {r.name.lower() for r in rutas}:
            ruta = ruta.with_name(f"{ruta.stem}-{archivo.id[-6:]}{ruta.suffix}")
        ruta.write_bytes(client.beta.files.download(archivo.id).read())
        rutas.append(ruta)
        print(f"  bajado: {ruta.relative_to(SALIDAS.parent)}")
    return rutas


def resumen_costo(client: anthropic.Anthropic, session_id: str) -> str:
    uso = client.beta.sessions.retrieve(session_id).usage
    if uso.list_cost is None:
        # El costo puede tardar unos segundos en aparecer después del idle.
        time.sleep(3)
        uso = client.beta.sessions.retrieve(session_id).usage
    # El monto viene en centavos de dólar, como string.
    costo = f"US${float(uso.list_cost.amount) / 100:.2f}" if uso.list_cost else "sin dato"
    activo = f"{uso.active_seconds:.0f} s" if uso.active_seconds is not None else "sin dato"
    # input_tokens no incluye lo que se leyó de la caché, que suele ser la mayor parte.
    cache = uso.cache_read_input_tokens or 0
    return (
        f"tokens: {(uso.input_tokens or 0) + cache:,} de entrada ({cache:,} de caché), "
        f"{uso.output_tokens or 0:,} de salida · tiempo activo: {activo} · costo de lista: {costo}"
    ).replace(",", ".")
