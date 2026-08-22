---
name: entregar-al-benchmark
description: Empaqueta y envía la entrega del equipo al Quick Golden Bench (leaderboard del hackathon) con submit.py. Úsala cuando pidan "entregar", "someter", "subir la corrida", "enviar al leaderboard" o "hacer submit" de las 7 preguntas del caso financiero de Quick.
---

# Entregar al Quick Golden Bench

Leaderboard: <https://quick-golden-bench.vercel.app>. No hay token ni cuenta: el endpoint es abierto.

## Qué se entrega

```
answers/q01.json … answers/q07.json      respuesta por pregunta (obligatorio)
traces/q01.events.jsonl … q07            traza del agente  (sin ella, tope 0.50)
```

`answers/qNN.json` — estas claves y ninguna más:

```json
{
  "question_id": "q04",
  "answer": { "values": { "2026-05": 22086527729 } },
  "summary": "lo que le dirías al CFO, en prosa",
  "method": "cómo lo calculaste",
  "code": "el código que produjo las cifras",
  "caveats": ["límites reales de los datos"],
  "conventions": ["convenciones propias, si difieren del enunciado"]
}
```

`question_id`, `answer` y `summary` son obligatorias. `answer` puede ser `null` si los datos
no permiten responder: con `caveats` explícitos eso vale 0.25; una cifra inventada vale 0.

## Guardar la traza (según el stack)

| Stack | Cómo |
|---|---|
| Claude Code | `claude -p "$(cat prompts/q04.md)" --output-format stream-json --verbose > traces/q04.events.jsonl` |
| Agent SDK | vuelca cada `SDKMessage` como una línea JSON (con `_message_type` o el stream-json crudo) |
| Managed Agents | guarda el stream de eventos de la sesión (`sevt_…`) tal cual → `traces/q04.events.jsonl` |
| Messages API | los content blocks uno por línea (`thinking`/`text`/`server_tool_use`/`*_tool_result`) + un `usage_summary` con `total_cost_usd` |
| Otro | escribe ATIF-v1.7 directo → `traces/q04.atif.json` |

La traza es la mitad del puntaje: el juez lee el código que ejecutaste para ver si sostiene
la cifra, si te auto-verificaste y si declaraste tus límites.

## Enviar

```bash
curl -sO https://quick-golden-bench.vercel.app/submit.py

python3 submit.py --team TU-EQUIPO --model claude-sonnet-5 \
  --tooling "Claude Code" --pack-only     # revisa el zip primero

python3 submit.py --team TU-EQUIPO --model claude-sonnet-5 --tooling "Claude Code"
```

`submit.py` es stdlib pura: no instala nada. Calcula el sha256 de cada archivo, arma el
`manifest.json`, comprime y hace POST. Deja el zip en `submissions/<equipo>/<run>.zip`.

Opciones: `--answers DIR` `--traces DIR` (por defecto `answers/` y `traces/`), `--notes`,
`--run-id`, `--to URL`.

## Reglas

- Si `submit.py` falla, **no lo arregles inventando datos**: dice exactamente qué archivo y
  qué clave están mal. Corrige el archivo y reintenta.
- No agregues claves al JSON de respuesta: el contrato las rechaza y la pregunta puntúa 0.
- No entregues sin traza para "ir rápido": el tope pasa a 0.50 en esas preguntas.
- Declara el `--model` que realmente corriste. Si no coincide con la traza, la fila sale
  marcada `NO COINCIDE`.
- Puedes enviar varias veces: cada envío es una fila nueva (equipo × modelo × corrida).

## Cómo se ordena el leaderboard

`puntaje = calidad × 2 / (2 + costo_usd)`. Calidad 0.90 a $4 (0.300) le gana a 1.00 a $40
(0.048). Correr barato y bien vale más que correr perfecto y caro.
