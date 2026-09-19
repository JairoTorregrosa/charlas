# Crea tu primer Agente con la Claude Agent SDK

Kit del taller de Claude Community Bogotá, sábado 19 de septiembre de 2026.
Ponente: Jairo Torregrosa.

Un solo hilo de principio a fin: **un asistente de viaje**. Siempre la misma
pregunta.

> Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.

En el primer archivo el modelo contesta que no puede. En el octavo contesta:
jueves 24 de septiembre de 2026, 06:15, BOG → MDE, LATAM, reserva ABC123. Entre
medias le vas dando una pieza por archivo, y esas piezas son los primitivos de
la SDK.

**Slides:** [Crea-tu-primer-agente-Agent-SDK-Bogota-2026.pdf](Crea-tu-primer-agente-Agent-SDK-Bogota-2026.pdf)

```
git clone https://github.com/JairoTorregrosa/charlas
cd charlas/2026-bogota-agent-sdk
cd python && uv sync          # o: cd typescript && npm install
uv run python 01_query.py     # o: npm run 01
```

## Requisitos

| Para qué | Qué necesitas |
|---|---|
| `python/` y `typescript/` | Claude Code instalado y con sesión iniciada (`claude` → `/login`) |
| `python/` | [uv](https://docs.astral.sh/uv/) |
| `typescript/` | Node 18 o más |
| `managed-agents/` | cuenta de Console y API key (la suscripción de claude.ai no sirve) |
| todo | git |

## El mapa

```
2026-bogota-agent-sdk/
├── python/           el recorrido completo, un archivo por primitivo, más el notebook
├── typescript/       el mismo recorrido, en TypeScript
├── managed-agents/   el mismo asistente sin harness tuyo: lo corre Anthropic
└── .claude/skills/   las skills del taller para tu propio Claude Code
```

## El recorrido

| # | Primitivo | Qué aparece |
|---|---|---|
| 01 | `query()` | Un prompt entra, una respuesta sale, el proceso termina. Sin tools no puede. |
| 02 | el stream | Todo lo que pasa adentro: arranque, tool call, tool result, texto, recibo. |
| 03 | tool propia | `hoy()`: una función tuya que el LLM decide llamar. |
| 04 | MCP | Un servidor de correo falso en otro proceso. Tools que no escribiste tú. |
| 05 | skill | El procedimiento en markdown. Se carga cuando se usa, no antes. |
| 06 | permisos y hooks | Quién decide si una tool corre. El `deny` no tumba al agente. |
| 07 | subagente | Contexto aparte, un solo resultado de vuelta. |
| 08 | todo junto | Con topes de turnos y de dinero, y la bitácora: `salidas/<fecha-hora>/eventos.jsonl` y `transcript.md`. |
| 09 | conversar | El contraste: conversar es una función más y hay que pedirla. |

Empieza por `python/README.md` o `typescript/README.md`.

## Sobre la autenticación

Hoy usamos tu sesión de Claude Code porque es lo más rápido para un taller: el
SDK trae adentro su propio Claude Code y usa tus credenciales. Para producción
es API key. Anthropic lo dice explícito: no permite ofrecer el login de
claude.ai ni sus límites en productos de terceros construidos sobre el Agent SDK.

`managed-agents/` es API key desde el primer comando, sin excepción.

## Doc oficial

- Agent SDK · <https://code.claude.com/docs/en/agent-sdk/overview>
- Managed Agents · <https://platform.claude.com/docs/en/managed-agents/overview>

## Mira lo que le entra al agente

`08_agente_vuelo` deja una carpeta por corrida en `salidas/`:

- `eventos.jsonl`: todos los eventos del SDK, crudos, uno por línea.
- `transcript.md`: llamada por llamada al LLM, qué papeles nuevos entraron al contexto, cuántos tokens leyó y qué respondió.

La bitácora vive en `observar.py` y `observar.ts`. Úsala en cada agente que construyas: leer el transcript es la forma más rápida de entender por qué un agente hizo lo que hizo.

## Crea tu propio agente

Abre Claude Code dentro de esta carpeta y escribe `/crear-agente-sdk`. La skill pregunta el objetivo y el lenguaje, genera el agente con su carpeta de trabajo, sus porteros y su bitácora, y lo corre una vez. `references/ideas.md` trae un primer agente pequeño para las ocho familias de ideas que más se repitieron en el workshop.
