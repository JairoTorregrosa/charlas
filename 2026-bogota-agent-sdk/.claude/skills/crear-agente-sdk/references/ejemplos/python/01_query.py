"""01 · query() — un prompt entra, una respuesta sale.

Sin tools. El modelo solo puede contestar con texto, así que a la pregunta del
taller responde que no puede ver tu correo. Ese "no puedo" es el punto de
partida: los archivos 02 a 08 le van dando las piezas que le faltan.

Fíjate en que el script corre y termina. Un agente no necesita un chat.

    uv run python 01_query.py
"""

import asyncio

from claude_agent_sdk import ClaudeAgentOptions, query

from mostrar import corto

PREGUNTA = "Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."

SYSTEM_PROMPT = """Eres un asistente personal. Respondes en español, corto y con datos.
Usa tus tools y skills; no adivines fechas ni reservas."""


async def main():
    opciones = ClaudeAgentOptions(
        model="claude-sonnet-5",
        system_prompt=SYSTEM_PROMPT,
        tools=[],                       # ninguna tool: solo texto
        setting_sources=[],             # nada del disco: ni skills ni CLAUDE.md de quien corre esto
        strict_mcp_config=True,         # ni los conectores de claude.ai de tu cuenta
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},   # ni tu memoria personal
        max_turns=2,
        max_budget_usd=0.05,
        stderr=lambda _: None,
    )

    print(f"PREGUNTA  {PREGUNTA}\n")
    async for m in query(prompt=PREGUNTA, options=opciones):
        # El stream trae varios mensajes; aquí solo nos interesa el último.
        if type(m).__name__ == "ResultMessage":
            print(f"RESPUESTA {corto(m.result or '', 400)}\n")
            print(f"RECIBO    USD {m.total_cost_usd:.4f} · {m.duration_ms / 1000:.1f}s")


asyncio.run(main())   # en un notebook esta línea falla: allí se usa `await main()`
