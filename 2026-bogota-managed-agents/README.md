# Workshop de Claude Managed Agents

Claude Community Bogotá · sábado 24 de octubre de 2026 · Universidad de La Salle

Hoy construyes un agente que te cuidaría el código mientras duermes: barre un repo en busca de vulnerabilidades, prueba cada una con un test, abre un PR por arreglo, espera el CI y mergea solo lo de bajo riesgo. La regla de qué se mergea la decide tu código, no el modelo.

No escribes el loop del agente ni montas servidores. Con Managed Agents, Anthropic corre el loop, el sandbox y la infraestructura. Tú defines el agente y decides.

## Qué es Managed Agents

Anthropic separa el agente en tres partes: la **sesión** (el registro de todo lo que pasó), el **harness** (el loop que llama a Claude y enruta sus tools) y el **sandbox** (donde corre el código). Claude más el harness son el cerebro; el sandbox y las tools son las manos. Como la sesión vive fuera de los dos, un contenedor que se cae no se lleva el trabajo y las credenciales nunca entran al sandbox.

| Pieza | Qué es |
|---|---|
| **Agent** | Modelo, system prompt, tools, MCP y skills. Tiene versiones |
| **Environment** | La plantilla del contenedor: red y paquetes |
| **Session** | Una corrida del agent en un contenedor nuevo. Vive en el servidor |
| **Events** | Lo que mandas (`user.message`, `user.define_outcome`, aprobaciones, resultados de tus tools) y lo que recibes (`agent.message`, `agent.tool_use`, `session.status_idle`…) |

Con la Messages API, el loop lo escribes tú. Con la Agent SDK, el loop corre en un proceso que tú operas. Con Managed Agents, corre en la infraestructura de Anthropic, y está hecho para trabajo largo y asíncrono: le das el trabajo, te vas y vuelves a ver el resultado.

## Antes del sábado

1. Crea tu cuenta en [platform.claude.com](https://platform.claude.com) y redime los créditos del taller en tu organización.
   Después de redimir el QR, para usar esos créditos de API en **Claude Desktop**: **Help → Troubleshoot → Enable Developer Mode**, luego **Developer → Configure 3rd Party Inference**, elige **Claude API** en el desplegable y vuelve a iniciar sesión.
2. Crea una API key en **Settings → API keys** (empieza por `sk-ant-` y solo se muestra una vez).
3. Instala [uv](https://docs.astral.sh/uv/getting-started/installation/), [Claude Code](https://claude.com/claude-code) y el CLI `ant` (`brew install anthropics/tap/ant`, o mira la [guía del CLI](https://platform.claude.com/docs/en/cli-sdks-libraries/cli/quickstart)). Entra con `ant auth login`.
4. Clona este repo y prepara el entorno:

   ```sh
   git clone https://github.com/JairoTorregrosa/charlas && cd charlas/2026-bogota-managed-agents
   cp .env.example .env      # pega tu key en .env
   uv sync
   uv run pasos/0_preparacion.py
   ```

5. En GitHub, crea tu copia del repo de práctica: abre [taller-cafe-origen-api](https://github.com/JairoTorregrosa/taller-cafe-origen-api) y usa **Use this template → Create a new repository** (público, en tu cuenta). Tiene vulnerabilidades puestas a propósito y un CI que corre los tests.

Si el paso 0 sale en verde, estás listo. No gasta créditos.

## Pista A · El vuln-patcher

Claude Code escribe el código. Tú describes el trabajo, revisas la propuesta y tomas las decisiones.

### Parte 1 · Descríbelo (20 min)

En Claude Code, dentro de este repo:

```
/claude-api managed-agents-onboard
```

Cuando te pregunte qué quieres, pega esto (cambia tu usuario):

```
Quiero un agente que revise mi repo TU-USUARIO/taller-cafe-origen-api en busca de
vulnerabilidades con la skill security-audit de Cloudflare (está en agente/skills/security-audit),
que pruebe cada hallazgo con un test, abra un PR por arreglo, espere el CI y mergee solo lo de
bajo riesgo. Por ahora lo disparo yo desde la terminal; después quiero que corra cada lunes a las 3 a. m.
```

Claude te devuelve una propuesta. Antes de aceptarla, decide tú:

- **¿Dónde vive la regla de "bajo riesgo"?** Si vive en el prompt, un README con instrucciones escondidas puede saltársela. ¿Cómo lo resuelve la propuesta?
- **¿Qué red tiene el sandbox?** ¿`limited` con qué hosts? ¿Para qué necesita cada uno?
- **¿Qué tools del MCP de GitHub quedan prendidas?** ¿Cuáles se pausan para pedir permiso?
- **¿Cómo se sabe que terminó?** Revisa la rúbrica del outcome que propone.
- **¿Cuánto puede gastar?** La skill reparte el trabajo entre varios agentes, y cada uno consume tokens.

Después compara con la versión de referencia: [`agente/agents/vuln-patcher.md`](agente/agents/vuln-patcher.md). Fíjate en la sección "How the security-audit skill applies here": la skill está escrita para cualquier agente, y ahí se traduce a Managed Agents (sus subagentes son workflow runs, el contenedor de la sesión es su sandbox).

Para seguir todos con la misma base, crea la de referencia:

```sh
cd agente
ant apply --dry-run -v agents/vuln-patcher.md environments/cloud.yaml vaults/github.yaml   # muestra el plan, no crea nada
ant apply agents/vuln-patcher.md environments/cloud.yaml vaults/github.yaml                # lo crea; los IDs quedan en claude-lock.json
cd ..
```

### Parte 2 · Primera corrida: solo auditar (30 min)

En `.env`, pon `TALLER_REPO_VULN=tu-usuario/taller-cafe-origen-api` y corre:

```sh
uv run pasos/vuln_patcher.py --solo-auditar
```

Sin token de GitHub, la sesión clona tu repo público pero no puede subir nada, y vas a ver en gris un aviso `mcp_authentication_failed_error`: es el MCP de GitHub sin credencial, y en esta parte no se usa. Abre el link de la sesión en la Console y mira cómo trabaja: reconocimiento, cazadores, verificadores, y el evaluador del outcome revisando el reporte. Cuando termine, lee `salidas/<sesión>/report.md`.

- ¿Qué encontró? ¿Cómo probó cada hallazgo?
- ¿Encontró algo que no debería obedecer? (Pista: lee el README del repo en modo código.)

### Parte 3 · Que arregle y que el merge lo decida tu código (35 min)

1. Crea un [fine-grained token](https://github.com/settings/personal-access-tokens/new) solo para tu repo de práctica, con **Contents: Read and write**, **Pull requests: Read and write**, **Checks: Read**, **Actions: Read** y **Commit statuses: Read**. Ponlo en `.env` como `GITHUB_TOKEN`.
2. Corre la versión completa:

   ```sh
   uv run pasos/vuln_patcher.py
   ```

El token va a dos sitios: al mount del repo, para que `git push` funcione, y a un **vault**, para el MCP de GitHub. El vault inyecta el token en la salida hacia el servidor MCP, así que nunca entra al sandbox.

Cuando el agente pide `merge_pull_request`, la sesión se pausa y tu terminal decide con [`src/taller/merge_gate.py`](src/taller/merge_gate.py): solo pasa un PR que toca archivos de dependencias, con 40 líneas o menos, sin saltos de versión major y con todo el CI en verde. Los arreglos de código quedan abiertos para que los revises tú.

### Parte 4 · Que corra solo (demo)

El mismo agente con un **deployment**: cada lunes a las 3 a. m. crea su propia sesión. Como nadie está mirando la terminal a esa hora, el merge gate corre en un webhook que recibe `session.status_idled` y contesta la llamada pausada.

## Tu agente

Vuelve a correr `/claude-api managed-agents-onboard` con el agente que escribiste en el registro. Antes de crear nada, pídele el `ant apply --dry-run`.

## Pista B · Tres casos en Python

Si no tienes GitHub o `ant` a mano, o terminaste la Pista A, hay tres casos listos. Cada uno es un script que puedes leer de arriba abajo; lo repetido (el loop de eventos, los IDs, bajar archivos) está en `src/taller/`.

| Caso | La historia | Qué aprendes | Comando |
|---|---|---|---|
| 1 · El bug del viernes | Los tests del facturador fallan. El agente encuentra la causa y te deja un parche, que el script prueba en tu máquina | Environment, agent, session, events; archivos de entrada y `outputs` | `uv run pasos/1_bug_del_viernes.py` |
| 2 · La bandeja de soporte | Seis tickets de una tienda de café. El agente responde, pero cada reembolso pasa por ti, y uno de los tickets intenta engañarlo | Custom tools que corren en tu máquina, humano en el loop, mínimo privilegio, presupuesto | `uv run pasos/2_bandeja_de_soporte.py` |
| 3 · El cierre de mes | Conciliar las facturas del ERP con el extracto del banco, con los archivos como salen en la vida real | La skill `xlsx` y un outcome con rúbrica que un evaluador revisa | `uv run pasos/3_cierre_de_mes.py` |

## Al terminar

```sh
uv run pasos/limpieza.py
```

Borra las sesiones, environments, archivos y memorias que crearon los scripts y archiva sus agents. Lo que creó `ant apply` se archiva con `ant` (mira `ant beta:agents archive --help`).

## Cosas que confunden

- **Abrir el stream antes de mandar el mensaje.** El stream solo entrega lo que pasa después de abrirlo.
- **`idle` no siempre es "terminé".** Con `stop_reason` `requires_action`, la sesión espera que respondas una custom tool o una aprobación. Una llamada pausada espera para siempre. `src/taller/sesion.py` resuelve esto.
- **Se cayó el wifi.** La sesión sigue en el servidor. No vuelvas a correr el caso (crea otra sesión y cobra otra vez): `uv run pasos/reanudar.py <session_id>`.
- **`web_fetch` solo abre URLs que ya aparecieron en la conversación**, y con red `limited` solo las de `allowed_hosts`.
- **Los outputs tardan unos segundos** en aparecer después de que la sesión queda idle.
- **Los agents no se borran, se archivan.** Por eso no se crea un agent por corrida: los scripts guardan los IDs en `.estado-*.json` y `ant apply` en `claude-lock.json`.
- **Cuesta tokens más US$0,08 por hora de sesión en `running`.** Cada script imprime su costo al final y cada sesión tiene tope (`budget`).
- **Managed Agents no tiene retención cero de datos.** No le pases datos personales ni de tu empresa.

## Datos y créditos

- Todos los datos de los casos son inventados.
- `agente/skills/security-audit` es una copia sin cambios de la [skill de Cloudflare](https://github.com/cloudflare/security-audit-skill) (MIT).
- SDK de Python fijado en `anthropic==1.16.0`. El 21-oct salió la 2.0 con cambios que rompen; el taller se queda en la 1.x.

## Documentación

- [Overview](https://platform.claude.com/docs/en/managed-agents/overview) · [Quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart) · [Eventos](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) · [Permisos](https://platform.claude.com/docs/en/managed-agents/permission-policies) · [Outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes) · [GitHub](https://platform.claude.com/docs/en/managed-agents/github) · [Vaults](https://platform.claude.com/docs/en/managed-agents/vaults) · [Deployments](https://platform.claude.com/docs/en/managed-agents/scheduled-deployments)
- [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents) (Anthropic Engineering)
- [Build your own vulnerability harness](https://blog.cloudflare.com/build-your-own-vulnerability-harness) (Cloudflare)
- Talleres oficiales: [anthropics/cwc-workshops](https://github.com/anthropics/cwc-workshops)
