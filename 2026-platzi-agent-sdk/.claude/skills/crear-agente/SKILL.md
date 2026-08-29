---
name: crear-agente
description: Crea un agente nuevo con el Claude Agent SDK en la forma del taller (un `agent_<nombre>.py` más su carpeta `workspace_<nombre>/` con skill, ayudante y MCP), preguntando un primitivo a la vez con AskUserQuestion y probándolo al final. Úsalo cuando pidan "crea un agente", "quiero mi propio agente", "haz el tuyo", "un agente que haga X", "agent wizard", "nuevo agente paso a paso". No es para explicar el SDK (ver `docs/`), ni para arreglar un agente que ya existe (léelo y usa `docs/errores.md`), ni para la Messages API o Managed Agents.
---

# crear-agente: un primitivo a la vez, hasta que corra

El usuario sabe qué quiere que haga el agente. Este skill le pregunta, en el orden del notebook, qué primitivo del SDK necesita para cada cosa, y con las respuestas escribe el agente en la forma del taller y lo corre una vez.

Trabajas en la carpeta del taller (la que tiene `demo.ipynb`, `proveedores.py`, `agent_parcero.py`). El agente nuevo se crea al lado de los tres que ya existen.

## Reglas

1. Una `AskUserQuestion` por paso, una sola pregunta por llamada, sin `multiSelect`. Entre 2 y 4 opciones; la recomendada primero, con `(Recomendado)` en la etiqueta. La UI agrega "Otra" sola.
2. Tras cada respuesta, una línea confirmando la decisión y la siguiente pregunta. No avances sin respuesta.
3. Español, tuteo, frases cortas. Ninguna variante de "explicar como a un niño" en nada que vea el usuario.
4. Cada opción corresponde a código exacto de `docs/options.md`, `docs/tools.md`, `docs/workspace.md` y `docs/permisos_hooks.md`. Si no está ahí, no lo escribas.
5. Los prompts que generes son markdown simple: encabezados, viñetas y algún backtick. Nada de etiquetas XML.
6. El agente nuevo sigue la forma del taller: constantes `SYSTEM_PROMPT` y `USER_PROMPT`, un archivo de salida vigilado por un hook, `max_turns` y `max_budget_usd` siempre, cerebro por `proveedores.py`.
7. Si el usuario dice "todo recomendado", toma la opción recomendada de cada paso restante, genera, corre y muestra las decisiones al final.

## Los pasos

| # | Pregunta | `header` | Opciones (recomendada primero) | Produce |
|---|---|---|---|---|
| 1 | ¿Qué hace tu agente? | `Objetivo` | Lee archivos y escribe un informe · Busca en internet y arma una tabla · Lee papers o documentos largos · Lo mío es otra cosa | Nombre (kebab-case, sin acentos), el archivo de salida, el `USER_PROMPT` de prueba |
| 2 | ¿Qué personalidad tiene? | `Personaje` | Neutro y directo · Con humor y personalidad · Formal, para clientes | Bloque `# Quién eres` del `SYSTEM_PROMPT` |
| 3 | ¿Qué puede hacer en el mundo? | `Manos` | Leer archivos de su carpeta · Leer y correr comandos · Leer páginas de internet | `tools` y `allowed_tools`; con Bash, el hook `solo_comandos` |
| 4 | ¿Necesita un procedimiento tuyo? | `Skill` | Sí, lo escribimos ahora · No por ahora | `workspace_<n>/.claude/skills/<skill>/SKILL.md` y una línea en el prompt |
| 5 | ¿La tarea se reparte? | `Ayudante` | No, un solo agente · Sí, un ayudante por archivo o sección | `workspace_<n>/.claude/agents/<ayudante>.md`, `"Agent"` en `allowed_tools`, el filtro por `parent_tool_use_id` |
| 6 | ¿Herramientas de otros? | `MCP` | Ninguna · Buscar en internet (Exa y Firecrawl, sin llave) · Papers (alphaXiv, con login) · Otro servidor (URL o comando) | `workspace_<n>/.mcp.json` y `mcp__<servidor>__*` en `allowed_tools` |
| 7 | ¿Cuánto puede gastar? | `Tope` | 25 vueltas y USD 0.50 · 15 vueltas y USD 0.25 · 40 vueltas y USD 1.00 | `max_turns`, `max_budget_usd` y la línea del prompt que lo avisa |
| 8 | ¿Con qué cerebro corre? | `Cerebro` | El del notebook (`TALLER_PROVEEDOR`) · Suscripción de Claude · OpenRouter gratis · ChatGPT vía LiteLLM | Nada en el código: `proveedores.py` lo resuelve; solo cambia cómo se corre |

Saltos: si el paso 1 es "Lee papers", el paso 6 propone alphaXiv primero. Si el paso 3 no incluye internet ni el paso 6 tiene MCP, no preguntes por búsqueda. El paso 1 y el 7 nunca se saltan.

Sub-pregunta del paso 1: si eligen "Lo mío es otra cosa", pide en una línea qué hace y qué archivo entrega. De ahí sacas nombre, archivo y prompt de prueba.

Sub-pregunta del paso 3, solo con "Leer y correr comandos": ¿qué comandos? Opciones: `git clone` y lecturas (`ls`, `wc`, `find`, `head`, `cat`) · Solo lecturas · Los que diga yo. Van al hook `solo_comandos`.

## Generar

Con las respuestas, crea en la carpeta del taller:

| Archivo | Desde | Cuándo |
|---|---|---|
| `agent_<nombre>.py` | `templates/agent.py.tmpl` | siempre |
| `workspace_<nombre>/.claude/skills/<skill>/SKILL.md` | `templates/SKILL.md.tmpl` | paso 4 = sí |
| `workspace_<nombre>/.claude/agents/<ayudante>.md` | `templates/ayudante.md.tmpl` | paso 5 = sí |
| `workspace_<nombre>/.mcp.json` | bloque de abajo | paso 6 ≠ ninguna |
| `workspace_<nombre>/.gitkeep` | vacío | si no hay ningún otro archivo en la carpeta |

No escribas el agente de memoria: parte de la plantilla y sustituye cada `{{CAMPO}}`. Los campos están listados al inicio de cada plantilla. Si un paso se saltó, borra el bloque correspondiente (están marcados con `# --- si ...`).

`.mcp.json` para el paso 6:

```json
{ "mcpServers": {
    "exa": { "type": "http", "url": "https://mcp.exa.ai/mcp" },
    "firecrawl": { "type": "http", "url": "https://mcp.firecrawl.dev/v2/mcp" } } }
```

alphaXiv no va en `.mcp.json` (pide OAuth): el agente lo carga con `setting_sources=["user", "project"]` y `allowed_tools` con `mcp__alphaxiv__*`; el usuario lo registra con `claude mcp add --transport http alphaxiv https://api.alphaxiv.org/mcp/v1 --scope user` y autentica en `claude` → `/mcp`. Copia esa nota al docstring del agente.

Añade el archivo de salida a `.gitignore` (`workspace_<nombre>/<archivo>`) para que las corridas no ensucien el repo.

## Probar

El skill no termina hasta que el agente corre.

1. Si el paso 8 no es "el del notebook", exporta `TALLER_PROVEEDOR=<proveedor>` en el comando.
2. `uv run agent_<nombre>.py "<USER_PROMPT de prueba>"`.
3. Muestra la línea `[fin]`: vueltas, costo, segundos. Abre el archivo de salida y muestra las primeras líneas.
4. Si falla, arregla antes de decir que está listo. `docs/errores.md` tiene síntoma, causa y arreglo. Errores frecuentes: el modelo escribe fuera de la carpeta (falta `{cwd}` en el prompt), pide permiso para `Edit` (agrégalo a `allowed_tools`; el hook sigue vigilando el archivo), se queda sin vueltas (sube `max_turns` o achica la tarea).

## Cerrar

Tres cosas, sin re-explicar el SDK:

- La tabla de decisiones: paso, respuesta, opción del SDK que produjo.
- Cómo correrlo otra vez: desde la terminal y desde el notebook (`from agent_<nombre> import <nombre>` y `await <nombre>(...)`).
- Qué probar después: cambiar el personaje, apretar el hook, darle un ayudante más.
