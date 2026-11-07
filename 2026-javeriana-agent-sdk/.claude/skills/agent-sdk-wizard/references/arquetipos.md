# arquetipos.md — goal (step 2) → defaults for steps 3–9

Step 2 is the only answer that changes every other answer. Pick the row, and steps 3–9 already
have a sensible default: the user can accept all of them and have a running agent in two minutes.

**These are defaults, not decisions.** Still ask each question — the default is just which
option goes first with `(Recomendado)`, and which steps you may skip.

---

## The four archetypes

| | **2A · Responder preguntas** | **2B · Cambiar archivos** | **2C · Llamar mis funciones** | **2D · Conversar con memoria** |
|---|---|---|---|---|
| Style | `query()` one-shot | `query()` one-shot | `query()` one-shot | `ClaudeSDKClient` / live `Query` |
| 3 Modelo | Sonnet 5.5 | Sonnet 5.5 | Haiku 5.5 | Sonnet 5.5 |
| 4 Instrucción | 4A mínimo + reglas | 4B preset + reglas | 4A mínimo + reglas | 4A mínimo + reglas |
| 4-bis Reglas | Analista de datos | Asistente de código | Operador cuidadoso | Analista de datos |
| 5 Herramientas | 5A solo leer | 5C todo + terminal | 5D mis funciones | 5A solo leer |
| 6 Skills | **skip** → no | no | no | no |
| 7 Subagentes | **skip** → no | no | **skip** → no | **skip** → no |
| 8 Permisos | 8A lo que listé | 8B acceptEdits | 8A lo que listé | 8A lo que listé |
| 9 Hooks | **skip** → no | 9D verificar al final | 9C registro | **skip** → no |
| `cwd` | `./workspace` | `.` (their project) | `.` | `./workspace` |
| Sample data | `ventas.csv` | none — their own code | none | `ventas.csv` |
| `max_turns` | 25 | 30 | 10 | 25 |
| `max_budget_usd` | 0.15 | 0.30 | 0.10 | 0.30 |

A **skip** means: say in one line why the step does not apply, take the default, and move on
without asking. Example: *"Como solo vas a leer, no necesitas un vigilante: me salto el paso 9."*

---

## Test prompt per archetype

The wizard's "done" criterion is a real run. This is the prompt it runs with.

| Archetype | Test prompt |
|---|---|
| 2A | `¿Cuál proyecto perdió margen entre enero y marzo, y por qué? Usa ventas.csv.` |
| 2B | Ask the user for a small real task in their repo. If they have none: `Lee el README y dime en 3 viñetas qué hace este proyecto.` (read-only, safe first run) |
| 2C | Something that forces the tool: `Usa la herramienta para <lo que hace la función> con <un valor de ejemplo>.` |
| 2D | Turn 1: `¿Cuál proyecto perdió margen? Usa ventas.csv.` · Turn 2: `¿Y sin contar ese, cuál sigue?` — turn 2 is the proof that memory works. |

For 2B, never make the first run a destructive task. Prove the loop works, then let the user
point it at real work.

---

## The sample data: `ventas.csv`

`templates/ventas.csv` — 15 rows, 5 columns, no dependencies (Python's `csv` module reads it).
Copy it to `workspace/ventas.csv` whenever the archetype calls for sample data.

The one domain rule, and it is all of it:

```
margen % = (ingresos − costos) / ingresos × 100
```

There are **two** findings planted in the data, on purpose:

| Proyecto | ene | feb | mar | |
|---|---:|---:|---:|---|
| Andes Retail | 33,3 % | 34,5 % | 36,2 % | sano |
| **Bodega Norte** | **4,8 %** | **−19,4 %** | **−32,8 %** | the obvious one |
| Chía Logística | 34,8 % | 35,7 % | 36,9 % | sano |
| Data Caribe | 29,7 % | 30,8 % | 33,4 % | sano, el más grande |
| **Eje Cafetero** | 21,6 % | 20,6 % | **8,4 %** | the second one: 12 points in March alone |

A lazy prompt finds Bodega Norte and stops. A careful one finds both. That is what makes it a
useful first run: the user can see the difference their step-4 rules made, with real numbers on
their own screen.

---

## Choosing the style behind their back

Step 1 asks for a language. It does **not** ask "one-shot or session" — that is jargon, and the
goal already answers it.

- Archetypes 2A, 2B, 2C → `query()`. One call, one session, done.
- Archetype 2D → `ClaudeSDKClient` (Python) / keep the `Query` object (TypeScript). This is the
  only shape where turn 2 remembers turn 1.

Each `query()` call opens a **new** session and remembers nothing from the previous one, unless
you pass `resume` or `continue_conversation`. Say that in one line when generating 2D, because
it is the thing people assume works and it does not.
