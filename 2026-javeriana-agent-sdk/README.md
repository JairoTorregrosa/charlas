<!-- ficha:inicio · lo escribe scripts/catalogo.py desde charlas.toml · no lo edites a mano -->
# Crea tu primer agente con la Claude Agent SDK

<a href="Crea-tu-primer-agente-Agent-SDK-Javeriana-2026.pdf"><img src="portada.jpg" alt="Portada del deck «Crea tu primer agente con la Claude Agent SDK»" width="100%"></a>

<table>
<tr><td>📅 <b>Cuándo</b></td><td>7 de noviembre de 2026</td></tr>
<tr><td>📍 <b>Dónde</b></td><td>Pontificia Universidad Javeriana · Bogotá</td></tr>
<tr><td>🎤 <b>Formato</b></td><td>Workshop · 3,5 h</td></tr>
<tr><td>🎟️ <b>Evento</b></td><td><a href="https://luma.com/claude-x1bt">Claude Community Bogotá</a> · Luma</td></tr>
<tr><td>📑 <b>Deck</b></td><td><a href="Crea-tu-primer-agente-Agent-SDK-Javeriana-2026.pdf">49 slides en PDF</a> · <a href="https://github.com/JairoTorregrosa/charlas/raw/main/2026-javeriana-agent-sdk/Crea-tu-primer-agente-Agent-SDK-Javeriana-2026.pdf">descargar</a></td></tr>
<tr><td>🧪 <b>Demo</b></td><td><a href="python">python/</a> · <a href="typescript">typescript/</a></td></tr>
<tr><td>🛠️ <b>Skill</b></td><td><a href=".claude/skills/agent-sdk-wizard"><code>agent-sdk-wizard</code></a></td></tr>
</table>

<details>
<summary>👀 Las 49 slides de un vistazo</summary>

<a href="Crea-tu-primer-agente-Agent-SDK-Javeriana-2026.pdf"><img src="vistazo.jpg" alt="Las 49 slides del deck en miniatura" width="100%"></a>

</details>

<sub><a href="../README.md">← Todas las charlas</a> · anterior: <a href="../2026-lasalle-managed-agents/">Agentes en la nube con Claude Managed Agents</a></sub>
<!-- ficha:fin -->

Segunda edición del [workshop de septiembre](../2026-bogota-agent-sdk/). Un solo hilo, **un asistente de viaje**, y siempre la misma pregunta:

> Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.

En `01` el modelo contesta que no puede. En `08` contesta: jueves 12 de noviembre de 2026, 06:15, BOG → MDE, LATAM, reserva ABC123. En `10` entrega lo mismo como JSON validado.

## El recorrido: una pieza por archivo

| # | Pieza | Qué aparece | Código |
|---|---|---|---|
| 01 | `query()` | Un prompt entra, una respuesta sale, el proceso termina. Sin tools no puede. | [py](python/01_query.py) · [ts](typescript/01_query.ts) |
| 02 | el stream | Todo lo que pasa adentro: arranque, tool call, tool result, texto, recibo. | [py](python/02_stream.py) · [ts](typescript/02_stream.ts) |
| 03 | tool propia | `hoy()`: una función tuya que el LLM decide llamar. | [py](python/03_tool.py) · [ts](typescript/03_tool.ts) |
| 04 | MCP | Un servidor de correo falso en otro proceso. Tools que no escribiste tú. | [py](python/04_mcp.py) · [ts](typescript/04_mcp.ts) |
| 05 | skill | El procedimiento en markdown. Se carga cuando se usa, no antes. | [py](python/05_skill.py) · [ts](typescript/05_skill.ts) |
| 06 | permisos y hooks | Quién decide si una tool corre. El `deny` no tumba al agente. | [py](python/06_permisos_hooks.py) · [ts](typescript/06_permisos_hooks.ts) |
| 07 | subagente | Contexto aparte, un solo resultado de vuelta. | [py](python/07_subagente.py) · [ts](typescript/07_subagente.ts) |
| 08 | todo junto | Con topes de turnos y de dinero (`max_turns`, `max_budget_usd`) y la bitácora en `salidas/<fecha-hora>/`. | [py](python/08_agente_vuelo.py) · [ts](typescript/08_agente_vuelo.ts) |
| 09 | conversar | El contraste: conversar es una función más y hay que pedirla. | [py](python/09_conversar.py) · [ts](typescript/09_conversar.ts) |
| 10 | salida estructurada | `output_format` con JSON Schema: datos que otro programa puede usar. | [py](python/10_salida_estructurada.py) · [ts](typescript/10_salida_estructurada.ts) |

El mismo recorrido en una sola pantalla: [`python/notebook.ipynb`](python/notebook.ipynb).

## Córrelo

```
git clone https://github.com/JairoTorregrosa/charlas
cd charlas/2026-javeriana-agent-sdk
cd python && uv sync && uv run python 01_query.py
# o:  cd typescript && npm install && npm run 01
```

El modelo de todos los scripts es `claude-sonnet-5-5`. Una corrida completa del `08` cuesta alrededor de US$0,01–0,04. Sigue con [`python/README.md`](python/README.md) o [`typescript/README.md`](typescript/README.md).

<details>
<summary>Instala lo que falta</summary>

| | Mac (Terminal) | Windows (PowerShell) |
|---|---|---|
| git | `xcode-select --install` | `winget install Git.Git` |
| uv (Python) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Node 20.11+ (solo TypeScript) | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| **ant** (CLI de Claude Platform) | `brew install anthropics/tap/ant` | `winget install Anthropic.Ant` |
| Claude Code (para el wizard) | `curl -fsSL https://claude.ai/install.sh \| bash` | `irm https://claude.ai/install.ps1 \| iex` |

Sin Homebrew ni winget: `ant` también viene como zip en
[github.com/anthropics/anthropic-cli/releases](https://github.com/anthropics/anthropic-cli/releases).
Cierra y abre la terminal después de instalar, para que aparezcan los comandos.

</details>

<details>
<summary>Autentícate: tres formas, elige una</summary>

**A · `ant auth login` (recomendado).** No creas ninguna API key.

```
ant auth login        # abre el navegador: entra con el MISMO correo con el que redimiste los créditos
ant auth status       # debe decir tu correo y la organización que tiene los créditos
```

El SDK lee esa sesión solo. Cada script imprime `[auth]` con lo que quedó.
Ojo: si ya tienes Claude Code logueado con Pro o Max, esa sesión le gana a la de
`ant`. Los scripts del kit lo resuelven fijando `ANTHROPIC_PROFILE` (lo verás en
`[auth] sesión de ant, perfil «…»`); en tus propios agentes haz lo mismo.

**B · API key.** Créala en [platform.claude.com/settings/keys](https://platform.claude.com/settings/keys)
en la organización que tiene los créditos, y pégala en `.env`:

```
cp .env.example .env          # Windows: copy .env.example .env
# edita .env →  ANTHROPIC_API_KEY=sk-ant-api03-...
```

**C · Tu suscripción Pro/Max** (solo para uso personal; no gasta los créditos):
`claude setup-token` y pega el token en `.env` como `CLAUDE_CODE_OAUTH_TOKEN=`.
Anthropic no permite ofrecer el login de claude.ai en productos de terceros.

Si hay una key o un token en el entorno, ganan sobre la sesión de `ant`.

</details>

## Mira lo que le entra al agente

`08_agente_vuelo` deja una carpeta por corrida en `salidas/`:

| Archivo | Qué trae |
|---|---|
| `eventos.jsonl` | Todos los eventos del SDK, crudos, uno por línea. |
| `transcript.md` | Llamada por llamada al LLM: qué entró al contexto, cuántos tokens leyó y qué respondió. |

## Crea el tuyo: `/agent-sdk-wizard`

Abre Claude Code dentro de esta carpeta (`claude`) y escribe `/agent-sdk-wizard`. Revisa tu máquina y tu autenticación, pregunta paso a paso (idea, objetivo, Python o TypeScript, datos, tools, skill, guardrails) con un diagrama de cómo queda tu agente en cada opción, escribe el system prompt, crea la skill si hace falta y corre el agente para probarlo.

La copia de este kit es la del día del workshop. La versión al día vive en [jaiskills](https://github.com/JairoTorregrosa/jaiskills/tree/main/skills/models/agent-sdk-wizard).

## Doc oficial

- Agent SDK · <https://code.claude.com/docs/en/agent-sdk/overview>
- CLI `ant` · <https://platform.claude.com/docs/en/api/sdks/cli>
