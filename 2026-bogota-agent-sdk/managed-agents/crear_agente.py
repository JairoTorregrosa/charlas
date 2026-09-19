"""Crea el agente y el entorno en Claude Managed Agents.

Un agente es la definición: modelo, system prompt, tools, MCP y skills. Un
entorno dice dónde corren las sesiones. Los dos se crean una vez y se reusan:
varias sesiones pueden apuntar al mismo entorno y cada una recibe su sandbox.

    uv run python crear_agente.py

Al final imprime dos líneas para pegar en .env.
"""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()                                      # managed-agents/.env: AGENT_ID, ENVIRONMENT_ID, SKILL_ID
load_dotenv(__import__("pathlib").Path(__file__).resolve().parent.parent / ".env")   # .env de la raíz del kit: ANTHROPIC_API_KEY

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""

cliente = Anthropic()   # lee ANTHROPIC_API_KEY del entorno; el SDK pone el header beta solo

agente = cliente.beta.agents.create(
    name="Asistente de viaje · Bogotá",
    model="claude-sonnet-5",
    system=SYSTEM_PROMPT,
    tools=[{"type": "agent_toolset_20260401"}],   # bash, read, write, edit, glob, grep, web
)

entorno = cliente.beta.environments.create(
    name="taller-bogota",
    # "unrestricted" es el default de la API y da salida completa a internet.
    # Para producción la doc recomienda "limited".
    config={"type": "cloud", "networking": {"type": "unrestricted"}},
)

print(f"agente  {agente.id}  ({agente.name})")
print(f"entorno {entorno.id}  ({entorno.name})")
print("\nPega esto en tu .env:\n")
print(f"AGENT_ID={agente.id}")
print(f"ENVIRONMENT_ID={entorno.id}")
