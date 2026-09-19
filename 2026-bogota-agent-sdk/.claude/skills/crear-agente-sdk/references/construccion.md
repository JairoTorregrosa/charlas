# Construcción: piezas, archivos y reglas

## Contenido

- Qué pieza usar
- Archivos que se generan
- Reglas que no se negocian
- Dentro del kit del workshop
- Hook sobre tools nativas

## Qué pieza usar

- **Tools nativas** (`Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebSearch`, `WebFetch`): declara en `tools` solo las que el objetivo exige. `tools=[]` deja al agente sin manos.
- **Tool propia**: para datos o acciones de tu código. Una función con nombre, descripción y esquema. Va dentro de un servidor MCP en proceso (`create_sdk_mcp_server` / `createSdkMcpServer`) y se llama `mcp__<servidor>__<tool>`.
- **MCP externo**: tools que hizo otro. Decláralo inline en `mcp_servers`. No lo pongas en `.mcp.json`: con `strict_mcp_config` ese archivo se ignora.
- **Skill**: un procedimiento que el agente debe seguir igual cada vez. `workspace/.claude/skills/<nombre>/SKILL.md`. Exige `setting_sources=["project"]`, `skills=["<nombre>"]` y `"Skill"` dentro de `tools`; sin la tool `Skill` el agente ve la skill y no puede abrirla.
- **Datos de ejemplo**: crea tú los archivos en `workspace/datos/` (8–12 filas, con dos o tres trampas que obliguen al agente a leer de verdad) y dilo en la entrega. El sistema real se conecta después.
- **Subagente**: solo cuando una parte del trabajo llena el contexto de papeles que el principal no necesita (leer veinte archivos para devolver una línea). Detalles en `references/piezas.md`.

## Archivos que se generan

Copia la plantilla del lenguaje elegido y rellena las marcas `TODO`:

- Python: `assets/agente.py` + `assets/observar.py` + `assets/pyproject.toml`
- TypeScript: `assets/agente.ts` + `assets/observar.ts` + `assets/package.json` + `assets/tsconfig.json`
- Skill del agente (si aplica): `assets/SKILL.plantilla.md` → `workspace/.claude/skills/<nombre>/SKILL.md`

Estructura de salida, en una carpeta nueva con el nombre del agente:

```
<nombre-del-agente>/
  agente.py | agente.ts
  observar.py | observar.ts       # la bitácora: cópiala tal cual de assets/
  pyproject.toml | package.json + tsconfig.json
  workspace/.claude/skills/<skill>/SKILL.md
  workspace/datos/                # datos de ejemplo
  workspace/entregas/             # lo que el agente escribe (informes, borradores)
  salidas/<fecha-hora>/           # la bitácora: eventos.jsonl + transcript.md, una carpeta por corrida
```

Dentro del kit del workshop no crees proyecto nuevo: deja el archivo junto a los `0N_*.py` o `0N_*.ts` y reutiliza su `pyproject.toml` o `package.json`.

## Reglas que no se negocian

0. **Observabilidad siempre**: estos agentes son para aprender. Cada corrida guarda TODOS los eventos del SDK, crudos, en `eventos.jsonl` (se escribe evento por evento, así una caída no borra nada) y un `transcript.md` que muestra, llamada por llamada al LLM, qué papeles nuevos entraron al contexto, cuántos tokens leyó y qué respondió. Nunca generes un agente sin la `Bitacora`, nunca filtres eventos antes de guardarlos y nunca la quites para «simplificar».
1. **Topes siempre**: `max_turns` y `max_budget_usd` (`maxTurns`, `maxBudgetUsd`). Empieza en 12 turns y USD 0.25.
2. **Aislamiento siempre**: `strict_mcp_config=True` y `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` en `env`. Sin lo primero, con sesión de suscripción el agente carga los conectores reales de claude.ai (Gmail, Drive) de quien lo corre. En TypeScript `env` reemplaza el entorno entero: esparce `...process.env`.
3. **`setting_sources` explícito**: `[]` si no hay skills; `["project"]` si las hay. Nunca heredes la configuración personal.
4. **Tres listas distintas**: `tools` define qué existe; `allowed_tools` qué corre sin preguntar; `disallowed_tools` qué nunca corre. `allowed_tools` no restringe nada.
5. **Nunca `bypassPermissions`** en un agente generado. Para correr sin humano usa `permission_mode="dontAsk"`: lo que no esté aprobado se niega y el agente busca otra ruta.
6. **Hook cuando la regla depende de los argumentos** (qué archivo, qué id, qué comando). El motivo del `deny` lo lee el LLM: escríbelo como instrucción. Un hook que devuelve `allow` no salta las reglas `deny`.
7. **Modelo**: `claude-sonnet-5` por defecto. Para subagentes, `sonnet` o `haiku` según lo que tengan que razonar.
8. **El system prompt dice qué no adivinar**. El modelo conoce la fecha real y la usa si no le exiges pedirla por tool.
9. **Credenciales por `.env`, siempre**: nunca escribas una API key en el código. Copia `assets/entorno.py` o `assets/entorno.ts` junto al agente e impórtalo en la primera línea: lee `ANTHROPIC_API_KEY` de `.env` (raíz del kit o carpeta del agente) e imprime qué autenticación quedó. Copia también `assets/.env.example` y dile a la persona que la key se crea en platform.claude.com/settings/keys (la suscripción de claude.ai no trae key). Verifica que `.env` esté en `.gitignore`. Sin key, el SDK usa la sesión de Claude Code.
10. **Notebooks**: `await` directo; `asyncio.run` falla dentro de Jupyter.


## Dentro del kit del workshop

Deja el agente junto a los `0N_*.py` o `0N_*.ts` como `NN_<nombre>.py|ts` y reutiliza su `pyproject.toml` o `package.json`, su `observar` y su `entorno`. Comparte el `workspace/` del kit: pon los datos en `workspace/datos/` y la skill nueva en `workspace/.claude/skills/<nombre>/`. En el ARRANQUE van a aparecer skills de otros ejercicios y las del repo padre (`setting_sources=["project"]` sube hasta la raíz del repo): es normal. `skills=[...]` es lo único que decide cuáles puede invocar el agente.

## Hook sobre tools nativas

Las tools nativas de archivos reciben `file_path` absoluto (`Read`, `Write`, `Edit`); `Bash` recibe `command`; `WebFetch` recibe `url`. Un hook que limita dónde escribe el agente:

```python
ENTREGAS = str(AQUI / "workspace" / "entregas")

async def solo_en_entregas(entrada, tool_use_id, contexto):
    ruta = entrada["tool_input"].get("file_path", "")
    if ruta.startswith(ENTREGAS):
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": f"Solo puedes escribir dentro de {ENTREGAS}. Usa esa carpeta."}}

hooks={"PreToolUse": [HookMatcher(matcher="Write", hooks=[solo_en_entregas])]}
```
```ts
const ENTREGAS = join(import.meta.dirname, "workspace", "entregas");
const soloEnEntregas: HookCallback = async (entrada) => {
  if (entrada.hook_event_name !== "PreToolUse") return {};
  const ruta = String((entrada.tool_input as { file_path?: string }).file_path ?? "");
  if (ruta.startsWith(ENTREGAS)) return {};
  return { hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny",
    permissionDecisionReason: `Solo puedes escribir dentro de ${ENTREGAS}. Usa esa carpeta.` } };
};
hooks: { PreToolUse: [{ matcher: "Write", hooks: [soloEnEntregas] }] }
```
