#!/usr/bin/env python3
"""El loop de un agente en ~100 líneas.

Un modelo (Claude) + una tool (bash) + un loop. Nada más.
Basado en la forma de anthropics/claude-quickstarts/agents/agent.py (Messages API).

Uso:
    export ANTHROPIC_API_KEY=...
    python agent.py "¿Cómo cambió el margen por proyecto de junio a julio, y por qué?"

Requiere: pip install anthropic
"""
import os
import subprocess
import sys

import anthropic

MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-5")
CSV = os.environ.get("AGENT_CSV", "contabilidad.csv")
MAX_TURNOS = 20

SYSTEM = f"""Eres un analista financiero. Trabajas en el directorio actual, donde está {CSV}
(separador ';', decimal con coma, columnas como Period, AccountId, Debito, Credito, ProjectId, CostCenterName).
Reglas: ingresos = cuentas que empiezan por 4; costos = cuentas que empiezan por 6 y 7.
Margen = (ingreso - costo) / ingreso. Period 6 = junio, 7 = julio.
Usa la tool bash (python3, awk, head) para inspeccionar y calcular. Verifica antes de responder.
Salida: cifra por proyecto, el cálculo que hiciste y la causa probable del cambio."""

TOOLS = [{
    "name": "bash",
    "description": "Ejecuta un comando de shell en el directorio actual y devuelve stdout y stderr.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "El comando a ejecutar."}},
        "required": ["command"],
    },
}]


def ejecutar_bash(command: str) -> str:
    """La única tool. Corre el comando y devuelve lo que el modelo necesita."""
    r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    salida = (r.stdout + r.stderr).strip()
    return salida[-6000:] if salida else "(sin salida)"


def main() -> None:
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise SystemExit("Falta ANTHROPIC_API_KEY en el entorno.")
    pregunta = " ".join(sys.argv[1:]) or "¿Cómo cambió el margen por proyecto de junio a julio, y por qué?"
    client = anthropic.Anthropic()
    contexto = [{"role": "user", "content": pregunta}]  # el contexto es la única memoria

    for turno in range(1, MAX_TURNOS + 1):  # ---- el loop ----
        respuesta = client.messages.create(
            model=MODEL, max_tokens=4096, system=SYSTEM, tools=TOOLS, messages=contexto,
        )
        contexto.append({"role": "assistant", "content": respuesta.content})

        if respuesta.stop_reason != "tool_use":  # ---- la parada ----
            texto = "".join(b.text for b in respuesta.content if b.type == "text")
            print(f"\n[turno {turno}] respuesta final:\n{texto}")
            return

        resultados = []
        for bloque in respuesta.content:  # ---- la tool ----
            if bloque.type == "tool_use":
                cmd = bloque.input["command"]
                print(f"\n[turno {turno}] tool_use bash: {cmd}")
                salida = ejecutar_bash(cmd)
                print(f"[turno {turno}] tool_result: {salida[:400]}{'…' if len(salida) > 400 else ''}")
                resultados.append({"type": "tool_result", "tool_use_id": bloque.id, "content": salida})
        contexto.append({"role": "user", "content": resultados})

    print(f"\nSe alcanzó el máximo de {MAX_TURNOS} turnos sin respuesta final.")


if __name__ == "__main__":
    main()
