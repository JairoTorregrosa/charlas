# system-prompt.md — build the agent's system prompt (step 4)

Read this before filling `{{SYSTEM_PROMPT}}`. The system prompt is the part of the agent the user
will feel most; a one-line "Eres un asistente útil" is a bug. Build it from the user's answers,
show it to them in full before generating, and accept edits.

## Facts already verified (2026-11-07)

- Anthropic's prompting guide for current models: be clear and direct (treat Claude like a
  brilliant new employee with no context); **say why** a rule exists, because the model
  generalizes from the reason; use numbered steps when order matters; separate parts with XML
  tags; one sentence of role already helps; 3–5 diverse examples in `<example>` tags are the most
  reliable way to steer format. Source:
  platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Same guide, agentic section: ask the agent to read before claiming ("never speculate about a
  file you have not opened"), to weigh reversibility and ask before destructive or shared-state
  actions, and to keep scope minimal (no extra files or features nobody asked for).
- Agent SDK: `system_prompt` as a plain string **replaces** Claude Code's default prompt (the
  agent knows only what you write plus tool definitions). The preset
  `{"type": "preset", "preset": "claude_code", "append": "…"}` keeps Claude Code's coding
  behaviour and adds yours. Source: code.claude.com/docs/en/agent-sdk/modifying-system-prompts
- Structured output: `output_format={"type": "json_schema", "schema": …}` (Python) /
  `outputFormat` (TS); the validated object arrives in the result's `structured_output`; failure
  ends with `error_max_structured_output_retries`. Source:
  code.claude.com/docs/en/agent-sdk/structured-outputs

## Do this

1. Collect, from step 2 (goal/idea), step 4 (rules) and step 5 (tools): who uses the agent, what
   a good result looks like, the data it works on, what it must never do, and the output format.
   If one of these is unknown and matters, ask **one** short question (not an `AskUserQuestion`
   with previews — a plain line); otherwise pick a sensible default and say so.
2. Fill the skeleton below, in the user's language. Every rule gets a short *why*. Name tools by
   their exact names (`Read`, `mcp__agenda__hoy`) and say when to use each.
3. Keep it 25–60 lines. Longer is fine only when it carries domain rules the agent cannot know.
4. Show it to the user in a fenced block: *"Este es el cerebro de tu agente. ¿Le cambio algo?"*
   Apply edits, then generate.
5. If the result feeds another program (a dashboard, a spreadsheet, an API), propose structured
   output: write a small JSON Schema (3–8 fields, `required` listed, descriptions in Spanish) and
   in the prompt describe the fields' meaning, not the JSON syntax, and add: "entrega el
   resultado solo por la salida estructurada; no lo repitas como texto" (otherwise the model
   tends to print the JSON twice).

## Skeleton

```
<rol>
Eres {{quién es, en una frase concreta: oficio + para quién trabaja}}.
</rol>

<contexto>
{{Quién usa al agente y para qué. Qué datos hay y dónde (rutas relativas a cwd). Fecha y zona
horaria si importan: "pide la fecha con la herramienta X; no la adivines".}}
</contexto>

<objetivo>
{{El resultado que cuenta como terminado, verificable: "un informe en entregas/x.md con …".}}
</objetivo>

<como_trabajas>
1. {{Primer paso: casi siempre leer/inspeccionar antes de opinar.}}
2. {{Pasos intermedios con la herramienta exacta para cada uno.}}
3. {{Verificar: re-leer lo escrito, cuadrar números contra la fuente.}}
4. Cuando termines, para. No sigas mejorando lo que ya cumple el objetivo.
</como_trabajas>

<herramientas>
- {{Tool}}: {{cuándo usarla}}. {{cuándo NO}}.
- Si una herramienta falla, lee el error y prueba otra vía una vez; si vuelve a fallar, dilo.
</herramientas>

<limites>
- No inventes datos: si algo no está en los archivos o en una herramienta, dilo. {{why: el
  usuario va a tomar decisiones con esto.}}
- {{Acciones prohibidas o que requieren confirmación, con el porqué (irreversibles, públicas,
  dinero).}}
- Solo haz lo que se pidió: no crees archivos ni funciones extra.
</limites>

<formato_de_salida>
{{Estructura exacta de la respuesta final: secciones, longitud, idioma, tono. Si hay salida
estructurada, qué significa cada campo.}}
</formato_de_salida>

<ejemplo>
{{Opcional pero valioso: un ejemplo corto de buena salida. 1 si es corto; 3 diversos si el
formato es delicado.}}
</ejemplo>
```

## Rules

- Never ship the prompt with a `{{…}}` left in it.
- Rules phrased positively when possible ("responde en 3 viñetas" beats "no escribas mucho").
- No shouting (`MUST`, `NUNCA` in caps) unless it is a hard safety limit; current models
  over-apply emphatic rules.
- Read-only agents still get `<limites>`: "no tienes permiso de escribir; si te lo piden,
  explica qué harías".
- Subagent prompts (step 7) follow the same skeleton, shorter: rol, objetivo, herramientas,
  formato de lo que devuelve al agente principal.
- Agents that act on money, messages to other people or deletions: in `<limites>`, require
  leaving a draft instead of acting, and say why.
