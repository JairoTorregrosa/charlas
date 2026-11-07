# errores.md — message → cause → fix

Read this when the test run of the generated agent fails. **Fix it before saying done.** Handing
back a broken agent with an explanation is not finishing the job.

Ordered by how often a first-time run hits them.

---

## Authentication and setup

| Message / symptom | Cause | Fix |
|---|---|---|
| `Invalid API key` / `Not logged in` | No valid credential reached the bundled Claude Code. The SDK does not read `.env` by itself — the generated `credenciales.py/.ts` does, and only if it runs before `query()` | Check the first output line is `[auth] …`; then follow the DIAGNOSTICAR table in `auth.md` (it covers `ant`, API key and Pro/Max token, with Mac and Windows commands) |
| `[auth] …` and the program exits | `credenciales` refused to start: `.env` missing, `AGENTE_AUTH` wrong, or the `ant` profile file not found | The message says which; `auth.md` § DIAGNOSTICAR |
| `Credit balance is too low` | The Console organization is out of credits, **or** an `ANTHROPIC_API_KEY` in the environment is diverting requests away from a Pro/Max subscription | Top up, or unset the variable if they meant to use the subscription |
| `You've hit your session limit · resets 3:45pm` | Plan quota exhausted. Session and weekly limits are **shared across models** — switching model does not help | Wait for the reset, or use an API key |
| `npm ERR! code ETARGET` / `No matching version found` for the SDK | The machine has an npm release-age cooldown (`min-release-age` / `before`) newer than the pinned version | The template pins a range (`^0.3.300`); if it still fails, pin the newest version older than the cooldown (`npm view @anthropic-ai/claude-agent-sdk time`) |
| `error: externally-managed-environment` on `pip install` | System Python on Debian/Ubuntu/Homebrew | `uv` (what the template uses), or `python3 -m venv .venv` |
| `Claude Code not found at: <path>` (`CLINotFoundError`, Python) | The SDK launches `claude` as a subprocess and did not find it | The SDK normally bundles it. If `cli_path` was set, check the file exists. Verify `claude --version` works **in the same environment** — an IDE or service manager has a different `PATH` |
| `Native CLI binary for <platform>-<arch> not found` (TS) | The per-platform package was skipped, almost always `npm ci --omit=optional` | Reinstall without skipping optional dependencies |
| `Refusing to execute batch script 'C:\…\claude.cmd'` (Windows) | Deliberate hardening: Windows runs `.bat`/`.cmd` through `cmd.exe`, which re-parses the command line | Point at a `claude.exe`, or install natively: `irm https://claude.ai/install.ps1 \| iex` |

## The agent runs but does nothing

| Symptom | Cause | Fix |
|---|---|---|
| The agent answers that it could not do it, without any error | `permission_mode="default"` with no `can_use_tool`: **anything not pre-approved is denied silently** | Add the tool to `allowed_tools`, or switch to `acceptEdits`, or implement `can_use_tool` |
| It ignores `can_use_tool` for one specific tool | That tool is in `allowed_tools` **by bare name**, so it is auto-approved before the callback runs | Use a scoped rule (`Bash(ls *)`) or a `PreToolUse` hook, which runs before everything |
| Warning `CLAUDE_SDK_CAN_USE_TOOL_SHADOWED` / `CanUseToolShadowedWarning` | Same cause. Note `skills="all"` adds a bare `Skill` entry and triggers it too | Same fix |
| Your Python hook does nothing at all, no error | A snake_case key in the hook's return value. They are `TypedDict`s: `permission_decision` is **silently ignored** | camelCase: `hookSpecificOutput`, `permissionDecision`, `permissionDecisionReason` |
| A `Stop` hook with a `matcher` does not filter | **`Stop` ignores matchers entirely** | Register it without one: `HookMatcher(hooks=[cb])` |
| A `Stop` hook blocks forever | Missing the `stop_hook_active` guard, and the agent cannot satisfy the check | Add the guard as the first line, and make sure it has the tool it needs to comply |
| It reads a `CLAUDE.md` nobody put there | Omitting `setting_sources` loads `user` + `project` + `local` | `setting_sources=[]` to isolate |
| The skill is never invoked | `setting_sources` does not include `"project"`, or `cwd` is below the `.claude/skills/` folder | `setting_sources=["project"]` and `cwd` at or above the folder |
| It never calls your own tool | The tool is not in `allowed_tools` under its full name | The name is `mcp__<dict key>__<tool name>` — the **dict key** of `mcp_servers`, not the server's `name=` field |

## The loop ends early

| Symptom | Cause | Fix |
|---|---|---|
| `result.subtype == "error_max_turns"` | Hit `max_turns` | Raise it, or accept the cut and read the `result` |
| `result.subtype == "error_max_budget_usd"` | Hit `max_budget_usd`. Subagent spend counts | Raise it, or narrow the task |
| `Budget limit reached` when launching a subagent | Same. Requires Claude Code v2.1.217+ for the cut to apply | Same |
| `num_turns` in the result is higher than `max_turns` and still `success` | Observed 2026-11-07 (19 and 26 turns with `max_turns=15`): `num_turns` counts more than the loop iterations the cap limits. Not investigated further | Treat `max_budget_usd` as the reliable brake; read the transcript, not the counter |
| `🔧 ToolSearch(…)` appears without being in `allowed_tools` | Claude Code defers some tool definitions (often custom tools) and loads them on demand | Harmless; it costs one turn. Mention it to the user so it does not look like a leak |
| `subtype == "success"` but the last API request failed | Real behaviour, documented: **read `terminal_reason` before `subtype`** | Check `terminal_reason` and `is_error` too |

## Crashes

| Message | Cause | Fix |
|---|---|---|
| `TypeError` building `AgentDefinition` | You passed `max_turns=…`. `AgentDefinition` is camelCase **even in Python** | `maxTurns=…`, `disallowedTools=…`, `permissionMode=…` |
| `query() takes 0 positional arguments` (Python) | `query("hola")`. The signature is keyword-only | `query(prompt="hola", options=…)` |
| `Not connected. Call connect() first.` | A `ClaudeSDKClient` method called before connecting | `async with ClaudeSDKClient(options=…) as c:` |
| `Command failed with exit code 1` + `Error output: Check stderr output for details` | `ProcessError`. That `Error output` line is **fixed text, not the real stderr** | Pass a `stderr=` callback in the options and log what it gives you |
| `Claude Code returned an error result: <report>` | The CLI reported an error result. Python raises `ResultError` (SDK ≥ 0.2.140) with `.data` | Debug from the text after the colon. Catch `ResultError` **before** `ProcessError` |
| `SyntaxError` on `await` inside `%%time` / `%%timeit` in a notebook | Those magics do not support top-level `await` | Use `duration_ms` from the `ResultMessage`, which is the honest number anyway |
| `RuntimeError: This event loop is already running` in a notebook | `asyncio.run()` inside a kernel that already has a loop | `await` at the top level of the cell. Do **not** add `nest_asyncio` |
| `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` running `node agente.ts` | Node's type stripping does not support `enum`, `namespace`, parameter properties, decorators | Do not use them, or run through `npx tsx` (what the template does) |
| In TS, `catch (e) { if (e instanceof …) }` never matches | Except `AbortError`, the TS SDK exposes no error classes — everything arrives as a plain `Error` | Match against the message text |

## Cost does not add up

| Symptom | Cause |
|---|---|
| `total_cost_usd` differs from the Console | It is a **client-side estimate**. Use the Usage and Cost API for anything that looks like accounting |
| Subagent cost seems missing | `usage` counts the main loop only. `model_usage` / `modelUsage` counts the whole tree |

---

## Debugging move that beats all of the above

Pass a `stderr` callback. The CLI's real error text goes nowhere else:

```python
opciones = ClaudeAgentOptions(
    stderr=lambda linea: print(f"[cli] {linea}", end=""),
)
```
```typescript
const opciones: Options = {
  stderr: (linea) => process.stderr.write(`[cli] ${linea}`),
};
```
