<!-- ficha:inicio · lo escribe scripts/catalogo.py desde charlas.toml · no lo edites a mano -->
# Crea tu primer agente con la Claude Agent SDK

<a href="Crea-tu-primer-agente-Agent-SDK-Javeriana-2026.pdf"><img src="portada.jpg" alt="Portada del deck «Crea tu primer agente con la Claude Agent SDK»" width="100%"></a>

<table>
<tr><td>📅 <b>Cuándo</b></td><td>7 de noviembre de 2026</td></tr>
<tr><td>📍 <b>Dónde</b></td><td>Pontificia Universidad Javeriana · Bogotá</td></tr>
<tr><td>🎤 <b>Formato</b></td><td>Workshop · 3,5 h</td></tr>
<tr><td>🎟️ <b>Evento</b></td><td><a href="https://luma.com/claude-x1bt">Claude Community Bogotá</a></td></tr>
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

Kit del workshop de Claude Community Bogotá en la **Pontificia Universidad
Javeriana**, sábado 7 de noviembre de 2026. Ponente: Jairo Torregrosa.
Segunda edición del workshop del 19 de septiembre en la Universidad Santo Tomás.

Un solo hilo de principio a fin: **un asistente de viaje**. Siempre la misma
pregunta:

> Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo.

En el primer archivo el modelo contesta que no puede. En el octavo contesta:
jueves 12 de noviembre de 2026, 06:15, BOG → MDE, LATAM, reserva ABC123. En el
décimo entrega lo mismo como JSON validado. Entre medias le vas dando una pieza
por archivo, y esas piezas son los primitivos de la SDK.

## 1 · Instala lo que falta

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

## 2 · Autentícate (elige uno)

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

## 3 · Corre

```
git clone https://github.com/JairoTorregrosa/charlas
cd charlas/2026-javeriana-agent-sdk
cd python && uv sync && uv run python 01_query.py
# o:  cd typescript && npm install && npm run 01
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
| 08 | todo junto | Con topes de turnos y de dinero (`max_turns`, `max_budget_usd`), y la bitácora en `salidas/<fecha-hora>/`. |
| 09 | conversar | El contraste: conversar es una función más y hay que pedirla. |
| 10 | salida estructurada | `output_format` con JSON Schema: el agente entrega datos que otro programa puede usar. |

Empieza por `python/README.md` o `typescript/README.md`. El modelo de todos los
scripts es `claude-sonnet-5-5`; una corrida completa del 08 cuesta alrededor de
US$0,01–0,04.

## Mira lo que le entra al agente

`08_agente_vuelo` deja una carpeta por corrida en `salidas/`:

- `eventos.jsonl`: todos los eventos del SDK, crudos, uno por línea.
- `transcript.md`: llamada por llamada al LLM, qué entró al contexto, cuántos tokens leyó y qué respondió.

## Crea tu propio agente

Abre Claude Code dentro de esta carpeta (`claude`) y escribe `/agent-sdk-wizard`.
Revisa tu máquina y tu autenticación, te pregunta paso a paso (idea, objetivo,
Python o TypeScript, datos, tools, skill, guardrails), cada opción con un
diagrama de cómo queda tu agente, escribe un buen system prompt, crea la skill
si tu agente la necesita, y lo corre para probarlo.

## Doc oficial

- Agent SDK · <https://code.claude.com/docs/en/agent-sdk/overview>
- CLI `ant` · <https://platform.claude.com/docs/en/api/sdks/cli>
