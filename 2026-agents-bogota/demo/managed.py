#!/usr/bin/env python3
"""Demo 3: las tres palancas convertidas en un agente que corre en Managed Agents.

1. Crea el agente: system prompt + toolset (y skills si las adjuntas).
2. Sube el CSV y abre una sesión con el archivo montado y la pregunta.
3. Imprime los eventos en vivo: tool calls, resultados y la respuesta.
Anthropic corre el loop.

Uso:
    export ANTHROPIC_API_KEY=...
    export MANAGED_ENV_ID=env_...        # environment creado en Console (general-assistant-env)
    python managed.py ["pregunta"]

Docs: platform.claude.com/docs/en/managed-agents/{agent-setup,sessions,events-and-streaming}
Requiere: pip install -U anthropic   (>= 1.0)
"""
import os
import sys
from pathlib import Path

import anthropic

AQUI = Path(__file__).parent
CSV = AQUI / "contabilidad.csv"
MOUNT = "/mnt/session/uploads/contabilidad.csv"
PREGUNTA_DEFAULT = "¿Cómo cambió el margen por proyecto de junio a julio, y por qué?"

# Palanca 1: system prompt. Objetivo, reglas y formato de salida.
SYSTEM = f"""Eres un analista financiero.
Objetivo: analizar el margen por proyecto.
Reglas: ingresos en cuentas que empiezan por 4; costos en cuentas 6 y 7. Margen = (ingreso - costo) / ingreso.
El archivo está en {MOUNT}. Separador ';', decimal con coma. Period 6 = junio, 7 = julio.
Salida: una tabla con margen por proyecto (junio, julio, cambio en puntos), el cálculo y la causa del cambio. Responde en español."""


def main() -> None:
    for var in ("ANTHROPIC_API_KEY", "MANAGED_ENV_ID"):
        if var not in os.environ:
            raise SystemExit(f"Falta {var} en el entorno.")
    pregunta = " ".join(sys.argv[1:]) or PREGUNTA_DEFAULT
    client = anthropic.Anthropic()

    # Palanca 2: tools. El toolset trae bash, archivos, web. Palanca 3: skills=[...] si hay una subida.
    agent = client.beta.agents.create(
        name="Analista financiero (demo)",
        model="claude-opus-5",
        system=SYSTEM,
        tools=[{"type": "agent_toolset_20260401"}],
    )
    print(f"agente  {agent.id}")

    archivo = client.beta.files.upload(file=CSV)
    print(f"archivo {archivo.id}  → {MOUNT}")

    session = client.beta.sessions.create(
        agent=agent.id,
        environment_id=os.environ["MANAGED_ENV_ID"],
        resources=[{"type": "file", "file_id": archivo.id, "mount_path": MOUNT}],
        initial_events=[{"type": "user.message", "content": [{"type": "text", "text": pregunta}]}],
    )
    print(f"sesión  {session.id}\n")

    # El loop corre en Anthropic; aquí solo se observa.
    with client.beta.sessions.events.stream(session.id) as stream:
        for ev in stream:
            t = ev.type
            if t == "agent.message":
                print("\n[agente]")
                for b in ev.content:
                    if getattr(b, "type", "") == "text":
                        print(b.text)
            elif t == "agent.tool_use":
                print(f"[tool_use] {getattr(ev, 'name', '')}  {str(getattr(ev, 'input', ''))[:120]}")
            elif t == "agent.tool_result":
                print("[tool_result] ok")
            elif t == "session.status_idle":
                print("\nsesión idle.")
                break
            elif t.startswith("session.status"):
                print(f"[{t}]")


if __name__ == "__main__":
    main()
