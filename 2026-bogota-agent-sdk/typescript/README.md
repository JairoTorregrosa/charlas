# Kit TypeScript — Crea tu primer Agente con la Claude Agent SDK

Claude Community Bogotá · sábado 19 de septiembre de 2026 · Jairo Torregrosa

Nueve archivos, un primitivo por archivo, un solo hilo: **un asistente de viaje**
que contesta «Revisa mis correos de la última semana y dime cuándo es mi próximo
vuelo». Cada archivo se corre solo y se lee en una pantalla.

## Requisitos

- Node.js 18 o superior (`node -v`). El SDK trae su propio binario de Claude Code.
- Una sesión de Claude Code iniciada en la máquina (`claude` en la terminal, y login).
  No hace falta `ANTHROPIC_API_KEY`.
- Opcional: `bun`, que corre los mismos archivos sin `tsx`.

## Instalación

```bash
npm install
```

## Cómo correr

```bash
npm run 01          # y así hasta npm run 09
npx tsx 01_query.ts # lo mismo, sin pasar por los scripts
bun 01_query.ts     # si tienes bun
npm run 08 -- "¿Cuándo sale mi próximo vuelo?"   # el 08 acepta la pregunta por argumento
npm run check       # tsc --noEmit
```

## El recorrido

| Archivo | Primitivo | Qué mirar |
|---|---|---|
| `01_query.ts` | `query()` | Entra un prompt, sale una respuesta, el programa termina. Sin tools el agente no puede mirar el correo y lo dice. |
| `02_stream.ts` | El stream | Cada mensaje etiquetado: `init`, tool call, tool result, texto del LLM y el recibo con costo, duración y `num_turns`. |
| `03_tool.ts` | Tool propia | `tool()` con esquema zod y `createSdkMcpServer()`. El nombre que ve el agente es `mcp__reloj__hoy`. La diferencia entre `tools` (qué existe) y `allowedTools` (qué se aprueba). |
| `04_mcp.ts` + `gmail_mcp.ts` | Servidor MCP | Un servidor entero con dos tools, `buscar` y `leer`, sobre cuatro correos falsos. En el `init` aparece `gmail=connected`. |
| `05_skill.ts` + `workspace/.claude/skills/buscar-vuelo/SKILL.md` | Skill | Una skill es un archivo en disco. `cwd` dice dónde mirar y `settingSources: ["project"]` autoriza leer ese `.claude`. Se ve la llamada a `Skill` antes de las tools. |
| `06_permisos_hooks.ts` | Permisos y hooks | `allowedTools`, `disallowedTools`, `permissionMode` y un hook `PreToolUse` que niega leer el correo de publicidad con un motivo. El LLM lee el motivo y sigue con los demás. |
| `07_subagente.ts` | Subagente | `agents: { "lector-de-correos": {...} }`. El principal solo delega. Los mensajes de adentro traen `parent_tool_use_id`. |
| `08_agente_vuelo.ts` | Todo junto | Tool propia + MCP + skill + `maxTurns` + `maxBudgetUsd`. Acepta la pregunta por argumento y guarda la traza completa en `salidas/`. |
| `09_conversar.ts` | Sesiones | Cada `query()` arranca una sesión nueva. Conversar hay que pedirlo: se guarda el `session_id` y se pasa en `resume`. El mismo turno se corre sin `resume` y con `resume`. |

## Los datos del hilo

La tool `hoy()` devuelve siempre **sábado 19 de septiembre de 2026**. El servidor
`gmail` tiene cuatro correos:

| id | De | Asunto | Fecha |
|---|---|---|---|
| c1 | Avianca | ¡Vuela a Cartagena desde $189.900! | 2026-09-15 (publicidad) |
| c2 | Wingo | Tu vuelo BOG → CTG | 2026-09-13 (el vuelo ya pasó, reserva WX7Q2) |
| c3 | LATAM | Confirmación de reserva | 2026-09-16 (**la respuesta**: BOG → MDE, jueves 24 de septiembre 06:15, reserva ABC123) |
| c4 | Booking.com | Tu reserva en Medellín | 2026-09-17 (hotel, El Poblado, 24 al 26, BK-88412) |

La respuesta correcta del `08` es el vuelo de LATAM del jueves 24 de septiembre a
las 06:15 con reserva ABC123.

## El aislamiento, línea por línea

Estos ejemplos corren en la máquina de quien los ejecuta. Tres opciones mantienen
fuera su configuración personal:

- `env: { ...process.env, CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" }` — el agente no
  carga la memoria automática de quien corre el script. En TypeScript el objeto
  `env` reemplaza el entorno del subproceso entero, así que hay que esparcir
  `process.env` para conservar `PATH` y `HOME`.
- `settingSources: []` — no lee `~/.claude/settings.json` ni el `.claude` del
  proyecto ni los `CLAUDE.md`. El `05` y el `08` usan `["project"]` porque la skill
  vive justo ahí, en `workspace/.claude/`.
- `strictMcpConfig: true` — solo entran los servidores MCP declarados en el código.
  Sin esta línea, en una cuenta con suscripción entran los conectores de claude.ai
  y el agente termina hablando con el Gmail real de quien proyecta.

Además, todos llevan `maxTurns` y `maxBudgetUsd` para que una corrida en vivo no
se vaya de las manos. Cada archivo cuesta entre uno y tres centavos de dólar (un agente propio con subagente puede costar diez veces más cuando algo falla: deja siempre los topes).

## Cosas que muerden

- **Con una lista explícita de `tools`, la tool `Skill` hay que incluirla a mano.**
  Con `tools: []` la opción `skills` no alcanza: el agente ve la skill en el `init`
  pero no tiene con qué invocarla. Por eso el `05` y el `08` llevan `tools: ["Skill"]`.
- **Los permisos no se heredan del bloque `agents`.** El `tools` de una definición
  de subagente dice qué tools existen para él; la aprobación sigue viniendo del
  `allowedTools` global. Sin él, el subagente reporta que le negaron el permiso.
- **Los subagentes corren en segundo plano por defecto.** Una llamada a la tool
  `Agent` que omite `run_in_background` arranca un subagente que no bloquea, y el
  principal responde antes de tener el resultado. El `07` se lo pide explícito en
  el prompt.
- **La tool de subagentes se llama `Agent` en los bloques `tool_use` y `Task` en la
  lista de tools del `init`.** En la opción `tools` va como `"Task"`.
- **`forwardSubagentText: true`** es lo que hace visible lo que dice el subagente.
  Sin esa opción solo llegan sus tool calls.
- **Tool search difiere las tools de servidores MCP del SDK**: el agente ve el
  nombre y carga el esquema cuando lo necesita, así que puede aparecer una llamada
  a `ToolSearch` antes de tu tool. `alwaysLoad: true` en `createSdkMcpServer` la
  evita y deja la demo limpia.
- **El stream se recorre hasta el final.** Salir con `break` al llegar al `result`
  deja mensajes de cierre sin leer.
- **`num_turns` cuenta vueltas del loop** (modelo → tools → modelo), no turnos de
  conversación. Una sola pregunta puede dar ocho vueltas.

## Versiones con las que está probado

- `@anthropic-ai/claude-agent-sdk` 0.3.269 (npm marca 0.3.278 como `latest`)
- Node 26.9.0, bun 1.3.14, TypeScript 7.0.2, zod 4.6.2
- Modelo `claude-sonnet-5` en todos los ejemplos
