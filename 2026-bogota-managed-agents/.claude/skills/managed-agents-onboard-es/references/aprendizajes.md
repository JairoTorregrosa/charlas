# Aprendizajes y trampas (probados en oct 2026)

## CLI y `ant apply`
- `ant apply .` recorre todo el directorio y crea lo que parezca un recurso. Nombra los archivos.
- `$F` sin comillas con una lista multilínea falla con "file name too long". Usa un array: `F=(...); ant apply "${F[@]}"`.
- En YAML, una descripción con `: ` adentro debe ir entre comillas (`description: "Report. Language: Spanish."`).
- El tipo del recurso sale del nombre del archivo: `agent.md`, `environment.yaml`, `vault.yaml` (con `type: vault`), `memory_store-<x>.yaml`, `deployment-<x>.yaml`, `skills/<x>/SKILL.md`.
- Dentro de un archivo, otros recursos se nombran por ruta relativa (`agent: ./agent.md`, `resources: [./memory_store-x.yaml]`). Los `vault_ids` van por ID.
- Error "Can't access this organization": el perfil de `ant` apunta a otra org. `ant auth login --profile <x>`.

## Versiones y Deployments
- Un Deployment fija la versión del agente con la que se creó.
- Si el Deployment está en un archivo que maneja `ant apply`, aplicar el `agent.md` también lo re-fija.
- Si lo creaste con el SDK o con `ant beta:deployments create`, actualízalo a mano: `ant beta:deployments update --deployment-id X --agent '{type: agent, id: agent_..., version: N}'`.
- Pausa los Deployments recién creados. `run` funciona en pausa y sirve de prueba.
- Nadie mira una sesión programada: una llamada en `ask` espera para siempre. Usa `auto`/`always_allow` en las tools que la corrida necesita, o un webhook `session.status_idled` que responda.

## Presupuesto
- Montos en centavos: `"2000"` = USD 20.
- Al llegar al tope, la sesión queda `idle` con `budget_reached`. No termina: sigue sola si subes el presupuesto (`ant beta:sessions update --session-id S --budget '{type: limit, max_list_cost: {amount: "13000", currency: USD}}'`).
- Una auditoría completa con Opus y workflows dinámicos puede pasar de USD 100. Mide la primera corrida antes de fijar el tope semanal.

## Permisos
- `auto` deja que el servidor juzgue cada llamada. Puede **negar** una escritura legítima (nos negó `create_pull_request` en un PR que borraba datos). Si la escritura es esencial y sin supervisión, ponla en `always_allow` con una regla clara en el prompt, o acepta que quede para una persona.
- Lecturas en `always_allow` evitan pausas inútiles.

## Outcomes
- La rúbrica la escribes tú, aunque la persona no tenga una. Criterios verificables, no "un buen reporte".
- Una rúbrica demasiado estricta falla aunque el trabajo esté bien (pedía enlace hasta para las edades calculadas). Ajusta la rúbrica tras las primeras corridas.
- El evaluador no tiene web tools.

## Archivos y memoria
- Los archivos de `/mnt/session/outputs/` aparecen en `files.list` unos segundos después de que la sesión queda `idle`. Espera ~15 s.
- `files.list(scope_id=session)` también devuelve copias de los archivos que montaste. Fíltralos si solo quieres resultados.
- El memory store se monta en `/mnt/memory/<nombre-del-store>/`. Escribe esa ruta en el prompt.
- Para sembrar memoria: `ant beta:memory-stores:memories create --memory-store-id M --path /topics.md --content "..."`.

## Subagentes
- Guía de Anthropic (2026): un solo loop con skills, salvo que midas que el contexto se llena, que haya trabajo en paralelo con contexto nuevo, o que el agente se confunda de tools. Al quitar un subagente, vuelve a correr las pruebas varias veces: una tarea que pasaba puede empezar a fallar.
- Nuestro caso: el brief de 3 repos funcionó igual sin su worker Haiku y costó menos. El radar de papers sí lo necesita (8 papers completos en paralelo).

## GitHub
- URL del MCP: `https://api.githubcopilot.com/mcp/x/all` (o `/mcp/x/<toolset>`, y `/readonly`).
- Montar un repo (`github_repository`) no abre PRs: hace falta el MCP.
- El PAT fine-grained no tiene permiso de Checks. Lee el estado del CI con `actions_list` / `actions_get` / `get_job_logs`.
- Disparar una sesión desde GitHub: una Action con `curl` a `POST /v1/sessions` (ver `plantillas.md`).
