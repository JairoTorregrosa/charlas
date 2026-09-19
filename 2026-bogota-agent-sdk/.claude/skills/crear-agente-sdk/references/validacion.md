# Correr, validar y entregar

## Corre, valida y repite

```
uv sync && uv run python agente.py          # Python
npm install && npx tsx agente.ts            # TypeScript
```

Comprueba en la salida, en este orden:

1. El `init` lista exactamente las tools y servidores MCP que declaraste, ninguno más. Si aparecen conectores de claude.ai, falta `strict_mcp_config`.
2. El agente usó las tools esperadas (líneas `->`).
3. El recibo final: `subtype` `success`, turns y costo por debajo de los topes.
4. Existe `salidas/<fecha-hora>/` con `eventos.jsonl` y `transcript.md`. Abre el transcript y léelo: cada tool result debe aparecer como papel nuevo en la llamada siguiente, y los tokens leídos deben crecer de llamada en llamada.

Si alguna comprobación falla: busca el síntoma en `references/gotchas.md`, arregla solo eso, corre otra vez y vuelve a validar las cuatro. Repite hasta que pasen. No declares el agente terminado sin una corrida exitosa; si no se puede correr (sin sesión, sin red), dilo y deja el comando exacto.

## Entrega

Responde con: la ruta de los archivos, el comando para correrlo, la ruta del `transcript.md` con la invitación a leerlo llamada por llamada, el recibo de la corrida (turns, llamadas al LLM, segundos, USD) y una tabla de tres filas con el system prompt, las tools y los guardrails que quedaron. Sugiere un único siguiente paso.
