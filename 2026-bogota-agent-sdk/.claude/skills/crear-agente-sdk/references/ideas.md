# Ideas de primer agente, por categoría

Verificado el 2026-09-18. Las URLs y comandos de los MCP cambian: confírmalos en la documentación del proveedor antes de usarlos.

Las ocho categorías salen de 392 propuestas de asistentes al workshop. Cada sección describe una versión pequeña y local que se termina en una tarde, con datos de ejemplo en `workspace/datos/`. El sistema real se conecta cuando esa versión ya corre bien.

Convenciones: los MCP se declaran inline en `mcp_servers`; la tool propia vive en un servidor en proceso y se llama `mcp__<servidor>__<tool>`; la skill va en `workspace/.claude/skills/<nombre>/SKILL.md` y exige `"Skill"` en `tools`. Topes de partida: `max_turns=12`, `max_budget_usd=0.25`. Cada corrida deja `salidas/<fecha>/eventos.jsonl` y `salidas/<fecha>/transcript.md`.

## Contenido

- 1. Asistente personal y gestión de proyectos (~77)
- 2. Código, QA y DevOps (~67)
- 3. Datos y análisis (~43)
- 4. Finanzas y contabilidad (~41)
- 5. Ventas y prospección (~36)
- 6. Marketing, contenido y diseño (~32)
- 7. Investigación y monitoreo (~30)
- 8. Documentos, atención y educación (~23 docs, ~16 atención, ~19 tutor)
- Reglas comunes a las ocho

## 1. Asistente personal y gestión de proyectos (~77)

- **Primer agente recomendado**: resumen de la mañana. Lee `datos/agenda.json`, `datos/correos/*.md` y `datos/tareas.md`, y escribe `salidas/hoy.md` con tres prioridades, choques de agenda y correos que piden respuesta.
- **Tools nativas**: `Read`, `Glob`, `Grep` para recorrer los archivos de ejemplo; `Write` solo para el resumen.
- **Tool propia**: `mcp__agenda__hoy` devuelve la fecha actual, la zona horaria y los eventos del día como JSON. El system prompt exige pedirla siempre y no adivinar fechas.
- **MCP reales**:
  - Linear: `https://mcp.linear.app/mcp` (solo lectura: `https://mcp.linear.app/mcp/readonly`). OAuth 2.1, o API key de Linear como `Authorization: Bearer`. Fuente: https://linear.app/docs/mcp
  - Notion: `https://mcp.notion.com/mcp`. Solo OAuth; la doc dice que aún no hay autorización no interactiva. Alternativa documentada: el servidor local `makenotion/notion-mcp-server` con token de integración, marcado como sin mantenimiento activo. Fuente: https://developers.notion.com/guides/mcp/get-started-with-mcp
  - Atlassian Rovo (Jira, Confluence): `https://mcp.atlassian.com/v2/mcp`. OAuth 2.1 o API token. Fuente: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/
  - Google Workspace (Gmail `https://gmailmcp.googleapis.com/mcp/v1`, Calendar `https://calendarmcp.googleapis.com/mcp/v1`, Drive `https://drivemcp.googleapis.com/mcp/v1`). OAuth 2.0 con proyecto de Google Cloud y cliente OAuth propio; está en Developer Preview y pide inscripción al programa. Fuente: https://developers.google.com/workspace/guides/configure-mcp-servers
  - Memory (referencia): `npx -y @modelcontextprotocol/server-memory`, archivo en `MEMORY_FILE_PATH`. Sin auth. Fuente: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- **Skill del agente**: `resumen-del-dia`. 1) Pide la fecha con `mcp__agenda__hoy`. 2) Lista los eventos y marca choques de horario. 3) Lee los correos y separa los que piden respuesta de los informativos. 4) Cruza tareas vencidas con huecos de la agenda. 5) Escribe `salidas/hoy.md` con tres prioridades y una línea de justificación por cada una. 6) Si un dato falta, lo dice en el resumen.
- **Guardrail**: `disallowed_tools` con `Bash`, `Edit`, `WebFetch`. Con Gmail o Calendar reales, niega las tools de envío, borrado y creación de eventos: el agente deja borradores. Hook `PreToolUse` que rechaza `Write` fuera de `salidas/`. Topes: 12 turns, USD 0.25.
- **Qué mirar en el transcript**: que la primera llamada sea `mcp__agenda__hoy` y que cada prioridad cite un archivo que el agente sí leyó.

## 2. Código, QA y DevOps (~67)

- **Primer agente recomendado**: revisor de un diff local. Recibe `datos/cambio.diff` y el repositorio de ejemplo, y escribe `salidas/revision.md` con hallazgos ordenados por severidad, cada uno con archivo y línea.
- **Tools nativas**: `Read`, `Glob`, `Grep` para seguir el código que toca el diff; `Bash` únicamente para correr los tests.
- **Tool propia**: `mcp__repo__correr_tests` ejecuta la suite y devuelve `{pasaron, fallaron, salida_recortada}`. Con esta tool se puede quitar `Bash`.
- **MCP reales**:
  - GitHub (oficial): `https://api.githubcopilot.com/mcp/`. OAuth o PAT como `Authorization: Bearer`; es el ejemplo que usa la doc del SDK. Local: `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> ghcr.io/github/github-mcp-server`, con `--read-only` para quitar las tools de escritura. Fuente: https://github.com/github/github-mcp-server
  - Sentry: `https://mcp.sentry.dev/mcp` (acepta `/{organizationSlug}/{projectSlug}`). OAuth. Sin humano: `npx @sentry/mcp-server@latest --access-token=<token>` o `SENTRY_ACCESS_TOKEN`. Fuentes: https://mcp.sentry.dev/ y https://github.com/getsentry/sentry-mcp
  - Playwright (Microsoft): `npx @playwright/mcp@latest`, con `--headless` e `--isolated`. Sin auth. Fuente: https://github.com/microsoft/playwright-mcp
  - Git (referencia): `uvx mcp-server-git --repository path/to/git/repo`. Sin auth. Fuente: https://github.com/modelcontextprotocol/servers/tree/main/src/git
  - Datadog: MCP remoto oficial en GA. El endpoint depende del sitio de la cuenta y la doc lo genera con un selector; aquí no se copia ninguna URL. OAuth, token de acceso como `Authorization: Bearer`, o cabeceras `DD_API_KEY` y `DD_APPLICATION_KEY`. Fuente: https://docs.datadoghq.com/bits_ai/mcp_server/setup/
  - Linear y Atlassian (categoría 1) para leer el ticket que originó el cambio.
- **Skill del agente**: `revisar-diff`. 1) Lee el diff completo y lista los archivos tocados. 2) Abre cada archivo y las funciones que llaman a lo modificado. 3) Corre los tests y anota cuáles fallan. 4) Clasifica hallazgos en bug, riesgo o estilo. 5) Escribe `salidas/revision.md` con archivo, línea, evidencia y arreglo sugerido. 6) No modifica código.
- **Guardrail**: `disallowed_tools` con `Edit` y `Write` sobre el repositorio (hook: `Write` solo en `salidas/`). Hook sobre `Bash` que niega `git push`, `git reset`, `rm`, `curl` y cualquier comando distinto al de tests. En GitHub, PAT de solo lectura y sin tools de merge ni de comentario. Topes: 15 vueltas, USD 0.40.
- **Qué mirar en el transcript**: cuántos archivos abrió antes de opinar y si cada hallazgo tiene detrás un `Read` o un `Grep` que lo respalde.

## 3. Datos y análisis (~43)

- **Primer agente recomendado**: auditor de calidad de un CSV. Toma `datos/ventas.csv` y produce `salidas/calidad.md` con nulos, duplicados, rangos imposibles y tres preguntas de negocio respondidas con su consulta SQL.
- **Tools nativas**: `Read` para el encabezado y una muestra; `Write` para el informe. El cálculo lo hace la tool propia o DuckDB.
- **Tool propia**: `mcp__datos__perfil_columna` devuelve tipo inferido, porcentaje de nulos, cardinalidad, mínimo, máximo y cinco valores de ejemplo de una columna.
- **MCP reales**:
  - MotherDuck / DuckDB: local `uvx mcp-server-motherduck --db-path /absolute/path/to/your.duckdb` (el README indica que abre el archivo en solo lectura). Remoto `https://api.motherduck.com/mcp` con OAuth o `Authorization: Bearer <motherduck_token>`. Fuentes: https://github.com/motherduckdb/mcp-server-motherduck y https://motherduck.com/docs/sql-reference/mcp/
  - Supabase: `https://mcp.supabase.com/mcp?read_only=true&project_ref=<id>`. OAuth, o personal access token en `Authorization` para CI. Fuente: https://supabase.com/docs/guides/getting-started/mcp
  - DBHub (Postgres, MySQL y otros): `npx -y @bytebase/dbhub --config dbhub.toml` con `readonly = true`. Es el ejemplo de base de datos de la doc del SDK. Fuente: https://code.claude.com/docs/en/agent-sdk/mcp
  - Filesystem (referencia): `npx -y @modelcontextprotocol/server-filesystem <carpeta>`. Sin auth. Fuente: la misma página del SDK.
- **Skill del agente**: `auditar-tabla`. 1) Lee el encabezado y veinte filas. 2) Perfila cada columna con la tool. 3) Propone reglas de calidad y cuenta cuántas filas viola cada una. 4) Responde tres preguntas de negocio mostrando la consulta usada. 5) Escribe el informe con hallazgo, evidencia numérica y fila de ejemplo. 6) Nunca corrige el archivo fuente.
- **Guardrail**: base de datos siempre en solo lectura (`read_only=true`, `readonly = true`, usuario sin permisos de escritura). Hook que niega cualquier SQL que contenga `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` o `COPY ... TO`. Sin `WebFetch`, para que los datos no salgan. Topes: 15 vueltas, USD 0.40.
- **Qué mirar en el transcript**: que los números del informe aparezcan en algún resultado de tool. Una cifra sin `tool_result` detrás es inventada.

## 4. Finanzas y contabilidad (~41)

- **Primer agente recomendado**: clasificador de gastos del mes. Lee `datos/extracto.csv` y `datos/categorias.md`, asigna categoría a cada movimiento y entrega `salidas/gastos.md` con totales, suscripciones repetidas y movimientos dudosos para revisión humana.
- **Tools nativas**: `Read` para extracto y reglas; `Write` para el informe; `Grep` para buscar comercios repetidos.
- **Tool propia**: `mcp__finanzas__sumar_por_categoria` recibe las asignaciones y devuelve totales exactos por categoría y el descuadre contra el saldo del extracto. La suma la hace el código.
- **MCP reales**:
  - Stripe: `https://mcp.stripe.com`. OAuth, o restricted API key como `Authorization: Bearer`. La doc distingue `stripe_api_read` de `stripe_api_write` y exige confirmación humana para reembolsos y pagos salientes. Fuente: https://docs.stripe.com/mcp
  - MotherDuck / DuckDB (categoría 3) para consultar extractos grandes con SQL.
  - Google Workspace, Sheets (`https://sheetsmcp.googleapis.com/mcp/v1`), con las mismas condiciones de la categoría 1.
  - No se verificó MCP oficial de bancos colombianos, de la DIAN ni de proveedores locales de facturación electrónica.
- **Skill del agente**: `clasificar-gastos`. 1) Lee las reglas de categorías. 2) Clasifica cada movimiento y marca como dudoso lo que ninguna regla cubre. 3) Pide los totales a la tool y verifica que cuadren con el extracto. 4) Detecta cobros repetidos mes a mes. 5) Escribe el informe con tabla de totales, lista de dudosos y descuadre. 6) No recomienda inversiones ni movimientos de dinero.
- **Guardrail**: nunca pagar, transferir, comprar ni ejecutar órdenes. En Stripe, restricted key de solo lectura y `disallowed_tools=["mcp__stripe__stripe_api_write"]`. Hook que rechaza (`deny`) una escritura con números de cuenta o de documento sin enmascarar; el motivo le pide al LLM enmascararlos y reintentar. Un hook `PreToolUse` permite o niega: no reescribe el contenido. Sin `WebSearch` ni `WebFetch` mientras haya datos reales. Topes: 12 turns, USD 0.30.
- **Qué mirar en el transcript**: si los totales vienen de la tool o si el modelo sumó de memoria, y qué hizo con los movimientos que no entendió.

## 5. Ventas y prospección (~36)

- **Primer agente recomendado**: investigador de una cuenta. Recibe una fila de `datos/leads.csv`, consulta la web pública de la empresa y escribe `salidas/<empresa>.md` con ficha, tres señales de compra con su URL y un borrador de primer mensaje.
- **Tools nativas**: `WebSearch` y `WebFetch` para la investigación; `Read` para el lead y la propuesta de valor; `Write` para la ficha.
- **Tool propia**: `mcp__crm__buscar_cuenta` busca en un `crm.json` local y devuelve etapa, último contacto y dueño, o `null` si la cuenta no existe.
- **MCP reales**:
  - HubSpot: `https://mcp.hubspot.com`. OAuth 2.0 con PKCE y una app o conector creado en la cuenta; lectura y escritura sobre el CRM. La doc no ofrece token estático. Fuentes: https://developers.hubspot.com/mcp y https://developers.hubspot.com/docs/apps/developer-platform/build-apps/integrate-with-the-remote-hubspot-mcp-server
  - Zapier: `https://mcp.zapier.com/api/v1/connect`. OAuth, o token de conexión como `Authorization: Bearer` generado en mcp.zapier.com; cada llamada exitosa consume dos tareas del plan. Fuente: https://docs.zapier.com/mcp/get-started/connect/python.md
  - Fetch (referencia): `uvx mcp-server-fetch`. Sin auth. Fuente: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch
  - Notion o Google Sheets (categoría 1) cuando el CRM es una tabla.
- **Skill del agente**: `investigar-cuenta`. 1) Busca la cuenta en el CRM local y, si existe, parte de ese historial. 2) Investiga solo fuentes públicas de la empresa. 3) Anota tres señales con URL y fecha. 4) Relaciona cada señal con la propuesta de valor. 5) Escribe la ficha y un borrador de mensaje de menos de 120 palabras. 6) Marca el borrador como pendiente de aprobación.
- **Guardrail**: el agente nunca envía correos ni mensajes y nunca modifica el CRM: escribe borradores. Hook sobre `WebFetch` que niega redes sociales personales y sitios que exigen sesión. Sin datos personales sensibles en la ficha, solo cargo y empresa. Topes: 15 vueltas, USD 0.50 (la web es la parte cara).
- **Qué mirar en el transcript**: cuántas búsquedas hizo por cuenta y si las señales de la ficha salen de páginas que sí abrió.

## 6. Marketing, contenido y diseño (~32)

- **Primer agente recomendado**: redactor con guía de marca. Lee `datos/marca.md` y `datos/brief.md`, produce tres variantes de copy para una publicación y una tabla que verifica cada regla de la guía. Entrega `salidas/copys.md`.
- **Tools nativas**: `Read` para guía y brief; `Write` para las variantes; `WebFetch` opcional para leer la landing a la que apunta la campaña.
- **Tool propia**: `mcp__marca__validar_copy` devuelve longitud por red, palabras prohibidas encontradas y si el llamado a la acción está presente.
- **MCP reales**:
  - Figma: `https://mcp.figma.com/mcp`. OAuth. Fuente: https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
  - Meta Ads (oficial): `https://mcp.facebook.com/ads`. La página consultada no detalla la auth; confírmala ahí. Puede crear y editar campañas, conjuntos y anuncios, es decir, gastar presupuesto. Fuente: https://developers.facebook.com/documentation/ads-commerce/ads-ai-connectors/ads-mcp-server/ads-mcp-server-overview
  - Playwright (categoría 2) para capturar y revisar una landing.
  - Shopify Dev MCP: `npx -y @shopify/dev-mcp@latest`. Sin auth. Consulta documentación y esquemas de Shopify; no accede a datos de una tienda. Fuente: https://shopify.dev/docs/apps/build/devmcp
- **Skill del agente**: `redactar-con-marca`. 1) Lee la guía y extrae tono, palabras prohibidas y límites. 2) Lee el brief y resume audiencia y objetivo en una línea. 3) Escribe tres variantes con ángulos distintos. 4) Valida cada una con la tool y corrige las que fallen. 5) Entrega las variantes con su tabla de cumplimiento. 6) No publica.
- **Guardrail**: nunca publicar ni tocar campañas. En Meta Ads permite solo tools de lectura en `allowed_tools`, niega por nombre las de creación y edición, y usa una cuenta publicitaria de prueba. En Figma, solo lectura de archivos. Topes: 10 vueltas, USD 0.25.
- **Qué mirar en el transcript**: si llamó la tool de validación después de escribir y si corrigió tras un resultado negativo o lo ignoró.

## 7. Investigación y monitoreo (~30)

- **Primer agente recomendado**: vigía de una lista corta de fuentes. Lee `datos/fuentes.md` (cinco URLs: convocatorias, una entidad pública, dos medios), compara contra `datos/visto.json` y escribe `salidas/novedades.md` solo con lo nuevo, con fecha y enlace.
- **Tools nativas**: `WebFetch` para las fuentes fijas; `WebSearch` para ampliar un hallazgo; `Read` y `Write` para estado e informe.
- **Tool propia**: `mcp__vigia__ya_visto` recibe una URL o un título y devuelve si ya fue reportado y cuándo. `mcp__vigia__registrar` lo guarda.
- **MCP reales**:
  - Fetch (referencia): `uvx mcp-server-fetch`. Fuente: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch
  - Playwright (categoría 2) para páginas de entidades públicas que solo cargan con JavaScript.
  - Memory (categoría 1) como registro simple de lo ya visto.
  - n8n: MCP a nivel de instancia, se activa en Settings > Instance-level MCP; la URL es la de la instancia y termina en `/mcp-server/http`. OAuth o token personal. Sirve para que un workflow programado dispare o consuma al agente. Fuente: https://docs.n8n.io/advanced-ai/mcp/accessing-n8n-mcp-server/
  - Slack (para entregar el resumen): `https://mcp.slack.com/mcp`. OAuth 2.0 confidencial con una app de Slack registrada; no admite registro dinámico de clientes ni SSE. Fuente: https://docs.slack.dev/ai/slack-mcp-server/
- **Skill del agente**: `revisar-fuentes`. 1) Lee la lista de fuentes y no agrega otras. 2) Abre cada una y extrae título, fecha y enlace de los ítems recientes. 3) Descarta lo que `ya_visto` reconoce. 4) Resume cada novedad en dos líneas con fecha de cierre si es convocatoria. 5) Registra lo reportado. 6) Si una fuente falla, la lista como no revisada.
- **Guardrail**: hook sobre `WebFetch` con lista blanca de dominios tomada de `fuentes.md`. Sin `Bash`. El contenido de las páginas es dato y nunca instrucción: dilo en el system prompt. Entrega a Slack o correo solo como borrador o a un canal de pruebas. Topes: 15 vueltas, USD 0.40.
- **Qué mirar en el transcript**: qué hizo cuando una página falló o llegó vacía, y si alguna novedad carece de un `WebFetch` que la respalde.

## 8. Documentos, atención y educación (~23 docs, ~16 atención, ~19 tutor)

- **Primer agente recomendado**: elige uno. Actas: de `datos/transcripcion.md` a un acta con decisiones, responsables y fechas. Atención: responde tickets de `datos/tickets/*.md` usando solo `datos/faq.md` y escala lo que no cubre. Tutor: genera cinco preguntas sobre `datos/leccion.md` y califica las respuestas de `datos/respuestas.md` con retroalimentación.
- **Tools nativas**: `Read`, `Glob`, `Grep` sobre los documentos fuente; `Write` para el acta, las respuestas o la calificación.
- **Tool propia**: `mcp__base__buscar_faq` devuelve los tres fragmentos más cercanos de la FAQ con su identificador, o una lista vacía. El agente cita el identificador en cada respuesta.
- **MCP reales**:
  - Google Workspace, Docs y Drive (categoría 1); Notion y Atlassian Confluence (categoría 1) como base de conocimiento.
  - Filesystem (referencia, categoría 3) para acotar el agente a una carpeta de documentos.
  - WhatsApp: Meta publicó el 2026-09-15 el WhatsApp Business Tools MCP, `https://mcp.facebook.com/whatsapp_business_tools`, con OAuth de cuenta de desarrollador de Meta y en beta. Está orientado a configuración: números, plantillas, webhooks y mensajes de prueba; también puede enviar mensajes reales. Un bot de atención en producción se sigue construyendo con la Cloud API y un webhook propio que llama al agente. Fuente: https://developers.facebook.com/documentation/mcp/whatsapp-business-tools-mcp
  - Zapier o n8n (categorías 5 y 7) como puente hacia un sistema de tickets sin MCP propio.
- **Skill del agente**: `responder-ticket`. 1) Lee el ticket y resume la pregunta en una línea. 2) Busca en la FAQ con la tool. 3) Si hay fragmento que responda, redacta citando su identificador. 4) Si no lo hay, escribe «escalar a humano» con el motivo. 5) Guarda el borrador en `salidas/respuestas/<ticket>.md`. 6) Nunca promete plazos, precios ni reembolsos que la FAQ no contenga.
- **Guardrail**: nunca enviar mensajes a clientes: solo borradores. Hook que enmascara cédulas, teléfonos y correos antes de escribir. En verificación de documentos y contratos el agente señala hallazgos y la decisión es humana. En el tutor, la nota final la confirma una persona. Topes: 12 turns, USD 0.30.
- **Qué mirar en el transcript**: los casos sin respuesta en la FAQ. Ahí se ve si el agente escaló o rellenó con conocimiento propio.

## Reglas comunes a las ocho

1. **Solo lectura primero.** La primera versión lee y escribe únicamente en `salidas/`. Los servidores que ofrecen modo de lectura lo traen en la URL o en una bandera: Linear `/mcp/readonly`, Supabase `?read_only=true`, GitHub `--read-only`, DBHub `readonly = true`.
2. **Hacia afuera, borrador.** Enviar, publicar, pagar, comprar, agendar a terceros o modificar un CRM quedan como borrador para que una persona apruebe. Niega esas tools por nombre en `disallowed_tools`; cuando dependa de los argumentos, usa un hook `PreToolUse` cuyo motivo de `deny` sea una instrucción para el modelo.
3. **Datos de prueba antes que reales.** Archivos de ejemplo en `workspace/datos/`, cuenta sandbox, proyecto de pruebas, canal de pruebas. Con datos reales, enmascara PII antes de escribir y quita `WebFetch` y `WebSearch` si no hacen falta.
4. **Secretos por variables de entorno.** Ninguna key en el archivo del agente ni en la skill: `os.environ["X"]` o `process.env.X`, pasados al MCP por `env` (stdio) o `headers` (remoto).
5. **OAuth y scripts.** La doc del SDK lo dice así: «The SDK doesn't open a browser or run an interactive OAuth flow». Un servidor que exige autorización y no tiene token queda en estado `needs-auth` y la corrida sigue sin sus tools. Alternativas que documenta cada proveedor:
   - Token o API key en cabecera: GitHub (PAT), Linear (API key), Stripe (restricted key), Supabase (PAT), MotherDuck (token), Datadog (token o `DD_API_KEY` + `DD_APPLICATION_KEY`), Zapier (token de conexión), n8n (token personal), Atlassian (API token).
   - Servidor local con token: Sentry (`@sentry/mcp-server` con `SENTRY_ACCESS_TOKEN`), Notion (`notion-mcp-server`, sin mantenimiento activo).
   - Solo OAuth según su doc, sin vía no interactiva: Notion remoto, HubSpot, Slack, Figma, Google Workspace, COROS, WhatsApp Business Tools. Para estos hay que completar el flujo OAuth en una aplicación propia y pasar el access token en `headers`, o dejarlos para un cliente interactivo.
6. **Forma exacta de un MCP remoto en el SDK** (https://code.claude.com/docs/en/agent-sdk/mcp):

```python
mcp_servers={
    "github": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
        "headers": {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
    }
},
allowed_tools=["mcp__github__list_issues"],
```

   En TypeScript es el mismo objeto dentro de `mcpServers`. `"type": "sse"` para servidores SSE; en código se usa `"http"` y no `"streamable-http"`. Los servidores stdio llevan `command`, `args` y `env`. Prefiere nombres exactos en `allowed_tools` antes que el comodín `mcp__<servidor>__*`.
7. **Comprueba el `init`.** El estado de cada servidor sale en `mcp_servers`: `connected`, `pending`, `failed`, `needs-auth`. Si un MCP no conecta, el modelo puede resolver con tools nativas y la respuesta parecerá válida. Revísalo en `eventos.jsonl` antes de creer el resultado.
8. **Topes siempre**, y súbelos solo cuando el transcript muestre progreso real.

Fuera de las ocho categorías quedó verificado COROS (datos deportivos, solo lectura): `https://mcp.coros.com/mcp`, OAuth. Fuente: https://github.com/coroslab/coros-mcp
