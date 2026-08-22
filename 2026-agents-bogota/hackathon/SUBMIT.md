# Cómo competir — una pantalla

Da igual tu stack: **Claude Agent SDK, Claude Code, Managed Agents, LangGraph o un loop
propio**. El bench no ejecuta tu agente: tú lo corres donde quieras y entregas **la
respuesta y la traza**.

## 0. Baja el enviador (una vez)

```bash
curl -sO https://quick-golden-bench.vercel.app/submit.py
```

Solo stdlib: no instala nada y no hace falta token ni cuenta. Si tienes el repo, `bench
submit` hace lo mismo.

## 1. Produce dos cosas por pregunta

```
answers/q01.json … answers/q07.json     ← la respuesta (obligatorio)
traces/q01.events.jsonl  (o .atif.json) ← la traza    (opcional pero decisiva)
```

`answers/qNN.json`:

```json
{
  "question_id": "q04",
  "answer": { "values": { "2026-05": 0, "2026-06": 0, "2026-07": 0 },
              "definition": "facturación = FC − DV ± notas, en cuentas 4, por Period" },
  "summary": "La facturación real fue … (lo que le dirías al CFO)",
  "method": "cómo lo calculaste y con qué convenciones",
  "code": "el código que produjo las cifras",
  "caveats": ["límites reales de los datos"],
  "conventions": ["si usaste una convención distinta a la del enunciado, decláralo aquí"]
}
```

- `answer` puede ser `null` si concluyes que los datos no permiten responder: con `caveats`
  explícitos eso vale **0.25**; una cifra inventada vale **0.0**.
- La forma de `answer` la sugiere cada enunciado (`preguntas/qNN.md`).
  El juez compara sustancia, no claves: usa las que tengan sentido, pero incluye las cifras.

## 2. Guarda la traza (según tu stack)

| Stack | Cómo |
|---|---|
| **Claude Code** | `claude -p "$(cat prompt-q04.md)" --output-format stream-json --verbose > traces/q04.events.jsonl` |
| **Claude Agent SDK** | vuelca cada `SDKMessage` como JSON por línea (lo que ya hace `events.py` del kit) → `traces/q04.events.jsonl` |
| **Managed Agents** | guarda el stream de eventos de la sesión (`sevt_…`, `agent.tool_use`, `agent.message`…) tal cual → `traces/q04.events.jsonl` |
| **Otro / propio** | escribe ATIF-v1.7 directo (`traces/q04.atif.json`) o cualquier JSONL con los eventos y prueba `bench convert` |

Comprueba el paquete antes de entregar:

```bash
python3 submit.py --team mi-equipo --model claude-sonnet-5 --pack-only
```

**Sin traza, cada pregunta tiene tope 0.5**: una cifra sin trayectoria no es auditable.
Además, si la traza no trae `model`, tu fila sale marcada `modelo no verificado`, y si no
trae coste ni tokens, no entras al ranking de valor (ver §4).

## 3. Envía (un comando)

```bash
python3 submit.py --team mi-equipo --model claude-sonnet-5 --tooling "Claude Agent SDK"
```

Por defecto lee `answers/` y `traces/` y envía a <https://quick-golden-bench.vercel.app>.
Empaqueta (`manifest.json` con sha256 de cada archivo), sube el zip y te devuelve el
`run_id`. El zip queda en `submissions/<equipo>/<run-id>.zip` por si hay que reintentar.
Puedes enviar varias veces: **cada envío es una fila** (equipo × modelo × run).

`--pack-only` genera el zip sin enviarlo. Sin red, ese zip se entrega por el canal del evento.

## 4. Cómo se puntúa

**Calidad** (0–1), media de las 7 preguntas. Por pregunta:

| Dimensión | Peso | Qué mide |
|---|---|---|
| `outcome_exact` | 3 (1 en preguntas abiertas) | tus cifras vs las de la golden, con la tolerancia que fija la golden |
| `outcome_judge` | 3 (4 en abiertas) | ¿coincide en sustancia? ¿cubre los hechos clave? ¿evita los errores descalificantes? |
| `trace_support` | 2 | el código que ejecutaste **sostiene** la cifra |
| `trace_verification` | 1 | te auto-verificaste (recuento por otro método, cruce de fuentes, cuadre de totales) |
| `honesty` | 1 | supuestos y límites declarados; nada inventado |

Topes y suelos: sin traza → `trace_*` = 0 y **tope 0.5**; `answer: null` con caveats → **mínimo 0.25**;
manifest roto, schema inválido o pregunta no entregada → **0.0 visible con motivo** (no se descarta en silencio).

**Coste**: USD de la corrida, leído de tu traza (`total_cost_usd`). Si no viene, se estima
desde los tokens con el precio del modelo declarado y se marca `est.`. Si no hay ni tokens,
sales del ranking de valor marcado `n/d`.

**Valor** (ranking principal): `valor = calidad × 2 / (2 + coste_usd)`.
Es decir: 0.90 de calidad a **$4** (valor 0.300) gana a 1.00 a **$40** (0.048), y pierde
contra 0.90 a **$0.50** (0.720). También se publican las columnas *calidad*, *coste* y
*calidad/USD* para ordenar por lo que quieras.

El juez está fijado por versión (modelo, prompt, rúbrica, golden) y cada resultado lo
registra: si cambia cualquiera de los cuatro, es otra versión del benchmark.
