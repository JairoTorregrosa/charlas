# Cuando la corrida falla

| Síntoma | Causa | Arreglo |
|---|---|---|
| En el `init` aparecen Gmail, Drive u otros conectores que no declaraste | sesión de suscripción sin aislamiento | `strict_mcp_config=True` / `strictMcpConfig: true` |
| Declaraste un `.mcp.json` y el servidor no carga | `strict_mcp_config` ignora ese archivo | declara el servidor inline en `mcp_servers` |
| El agente ve la skill y resuelve a mano sin abrirla | falta la tool `Skill` | `tools` incluye `"Skill"`, `skills=[...]`, `setting_sources=["project"]` y `cwd` apunta a la carpeta que contiene `.claude/` |
| Responde con la fecha real sin llamar tu tool | el modelo conoce la fecha | system prompt: «no adivines fechas» y descripción de la tool: «pídela siempre» |
| El subagente reporta permiso denegado | los permisos no se heredan | agrega sus tools al `allowed_tools` global |
| El principal contesta antes que el subagente | background por defecto | `background=False` en la definición |
| El agente se queda esperando una aprobación | modo de permisos por defecto en un script | `permission_mode="dontAsk"` |
| TypeScript: el CLI no encuentra `PATH` ni credenciales | `env` reemplaza el entorno | `env: { ...process.env, ... }` |
| Excepción al final con `error_max_turns` o de presupuesto | tocó un tope | es el guardrail funcionando; sube el tope solo si el transcript muestra progreso |
| `asyncio.run() cannot be called from a running event loop` | estás en un notebook | `await main()` |
| Pide ToolSearch antes de usar tu tool (TS) | carga diferida de tools MCP | `alwaysLoad: true` en `createSdkMcpServer` |
| `npm install` trae una versión anterior a la publicada | cooldown `min-release-age` en `~/.npmrc` | es esperado; respeta el `package-lock.json` |
| 401 o «invalid API key» | sin sesión de Claude Code y sin `ANTHROPIC_API_KEY` | `claude` y `/login`, o exporta la key de Console (la suscripción de claude.ai no da API key) |
| En el ARRANQUE aparecen skills de otras carpetas del mismo repo | `setting_sources=["project"]` sube hasta la raíz del repo | es normal; `skills=[...]` decide cuáles se pueden invocar |
| `[auth] sin API key en .env` y querías usar tu key | falta `.env` o está vacío | `cp .env.example .env` y pega la key de platform.claude.com/settings/keys |
| `would be spawned with zero tools` al delegar | las tools nativas del subagente no están en el `tools` del principal | agrégalas ahí también |
| Dentro de un subagente, `Read` responde «The user doesn't want to take this action right now» | observado el 19-sep-2026 con tools nativas de archivos en subagentes | mueve esa lectura al principal, o dale al subagente una tool propia/MCP que lea |
| En el `init` salen skills como `deep-research` o agentes como `Explore` que no declaraste | vienen de fábrica con el CLI empaquetado; `setting_sources` no los quita | `skills=[...]` limita lo invocable; no declares `Task` si no defines `agents` |
| El agente escribió su entrega en un lugar inesperado | `Write` es relativo al `cwd` (`workspace/`); la bitácora va aparte | entregas en `workspace/entregas/`, bitácora en `salidas/<fecha-hora>/` |
