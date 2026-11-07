# auth.md — step 0: preflight and credentials, Mac and Windows

Read this before step 1. The wizard does not ask a single design question until the machine is
ready and **one** credential is chosen, written to `.env`, and verified. A workshop attendee who
skips this ends up spending their own Pro/Max quota instead of the workshop credits, or gets
`Not logged in` after twenty minutes of design.

Verified on 2026-11-07 (macOS, `ant` 2.7.1, Python SDK 0.2.176 bundling Claude Code 2.1.316).
Windows facts marked *(inferred)* were not run on a Windows machine: the preflight below checks
them for real, so a wrong inference fails loudly at step 0 instead of at the test run.

---

## The state machine

```
INICIO ─► PREFLIGHT ─► ELEGIR_CREDENCIAL ─► (A) ANT ───────┐
             │  falta algo      │           (B) API_KEY ───┼─► ESCRIBIR_ENV ─► VERIFICAR ─► LISTA
             ▼                  │           (C) SUSCRIPCIÓN┘                      │ falla
         INSTALAR ──► PREFLIGHT │                                                 ▼
                                └──────────────────────────────── DIAGNOSTICAR ──► ELEGIR_CREDENCIAL
```

| State | Leaves when | Goes to |
|---|---|---|
| PREFLIGHT | every row of the preflight table passes | ELEGIR_CREDENCIAL |
| PREFLIGHT | a row fails | INSTALAR (give the exact command for their OS, wait, re-run the row) |
| ELEGIR_CREDENCIAL | the user picks A, B or C (one `AskUserQuestion`, header `Credencial`) | that path |
| ESCRIBIR_ENV | the agent folder exists (create it now: name from the goal if known, else `mi-agente`; rename it at generation if needed), its `.gitignore` lists `.env`, and its `.env` holds `AGENTE_AUTH` plus exactly one credential line — written with your file-writing tool (Write), never with `echo`/`printf` in a shell | VERIFICAR |
| VERIFICAR | the path's check passes | LISTA (say which org/account will pay, in one line) |
| VERIFICAR | the check fails | DIAGNOSTICAR (match the message in the table at the end and fix; a rejected key (`401`): ask once to re-copy it from the Console, then offer path A; any other path: after 2 failures offer the next one) |

Never leave a state on a guess. "It probably works" is not a transition.

---

## Preflight (run it, don't ask about it)

Detect the OS first: in Claude Code the platform is in your environment info; otherwise run
`uname -s` (Mac prints `Darwin`) or `$PSVersionTable` (PowerShell). Run each check yourself and
report a one-line checklist. Only the rows for the chosen language matter (step 1 can be asked
now if the user already said it; otherwise check both and only block on what step 1 needs).

| Check | Mac (zsh/bash) | Windows (PowerShell) | Need |
|---|---|---|---|
| Python | `python3 --version` | `py --version` or `python --version` | 3.10+ (workshop asks 3.11+) |
| uv | `uv --version` | `uv --version` | any |
| Node (TS path only) | `node --version` | `node --version` | 20.11+ (18 is end-of-life) |
| git | `git --version` | `git --version` | any |
| ant | `ant --version` | `ant --version` | 2.7+ (path A) |
| network | `curl -sI https://api.anthropic.com \| head -1` | `(Invoke-WebRequest https://api.anthropic.com -Method Head -SkipHttpErrorCheck).StatusCode` | any HTTP status = reachable |
| stray credentials | `env \| grep -E '^(ANTHROPIC_API_KEY\|CLAUDE_CODE_OAUTH_TOKEN\|ANTHROPIC_PROFILE)=' \| cut -d= -f1` | `Get-ChildItem Env: \| ? Name -match '^(ANTHROPIC_API_KEY\|CLAUDE_CODE_OAUTH_TOKEN\|ANTHROPIC_PROFILE)$' \| % Name` | print names only, never values |

Install commands for what is missing:

| Missing | Mac | Windows (PowerShell) |
|---|---|---|
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (or `brew install uv`) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` (or `winget install astral-sh.uv`) |
| Python | `uv python install 3.12` (uv brings its own Python) | `uv python install 3.12` |
| Node | `brew install node` | `winget install OpenJS.NodeJS.LTS` |
| git | `xcode-select --install` (or `brew install git`) | `winget install Git.Git` |
| ant | `brew install anthropics/tap/ant` | `winget install Anthropic.Ant` (manifest in microsoft/winget-pkgs, 2.7.1 on 2026-11-06). Fallback: download `ant_<ver>_windows_amd64.zip` (or `_arm64`) from github.com/anthropics/anthropic-cli/releases, unzip, put `ant.exe` on `PATH` |

**Windows: after any `winget install`, the user must open a NEW terminal** (and restart Claude
Code if it runs there) before the command is on `PATH`. Say this every time; it is the most
common "I installed it and it says not found".

---

## The three credentials (recommended first)

Ask with one `AskUserQuestion`, header `Credencial`, previews from `previews.md` § Step 0.

### A · `ant` CLI login (Recomendado — no key to create, uses the workshop credits)

`ant` is Anthropic's official CLI for the Claude Platform. `ant auth login` opens the browser,
the user signs in to platform.claude.com, and `ant` stores an OAuth token plus a refresh token
in a **profile**. The Agent SDK (through the Claude Code it bundles) reads that profile: no API
key ever exists, and the token refreshes itself (access token lasts ~8 h).

1. `ant auth login` — tell the user: *sign in with the SAME email you used to claim the workshop
   credits, and if it asks for an organization, choose the one that received the credits.*
   Headless/remote machine: `ant auth login --no-browser` prints the URL instead.
2. `ant auth status | grep -E 'Logged in|Active profile|Config dir'` (Windows:
   `ant auth status | Select-String 'Logged in|Active profile|Config dir'`) — the filter keeps
   the start of the token out of the chat; read back to the user the line `Logged in to <org> as <email>` and the
   active profile name (`Active profile: <name>`, usually `default`). Ask in one line: *"¿Esta es
   la organización donde reclamaste los créditos?"* If not: `ant auth logout`, then log in again.
3. `ant --profile <name> models list --format json` (the profile you will write to `.env`, not
   just the active one) must exit 0. That is a free, real call with the token: it proves the
   login works for that profile. (Use `--transform` or just check the exit code; do not dump
   the list.)
4. Note the config dir `ant auth status` prints (`Config dir: …`). Mac/Linux:
   `~/.config/anthropic`. Windows: whatever it prints *(inferred: under `%APPDATA%` or
   `%USERPROFILE%\.config`)*. The generated `credenciales.py/.ts` searches the usual places and
   pins the one it finds; if `ant` printed something else, write it to `.env` as
   `ANTHROPIC_CONFIG_DIR=<that path>`.
5. `.env` (the profile name from step 2, not necessarily `default`):
   ```
   AGENTE_AUTH=ant
   ANTHROPIC_PROFILE=<profile name from ant auth status>
   ```

Why the profile name is written explicitly: an **explicit** `ANTHROPIC_PROFILE` beats a
claude.ai login that Claude Code may already have on the machine. Without it, a Pro/Max login
wins and the agent silently bills the user's subscription instead of the credits (verified, see
precedence below). A profile name that does not exist is ignored **silently** and falls through
to the claude.ai login — that is why `credenciales.*` refuses to start when the profile file is
missing.

Bonus to tell the user: Claude Code itself (the app running this wizard) also accepts that
`ant` login when it has no claude.ai login of its own, so on a fresh machine `ant auth login`
covers both.

### B · API key from the Console

1. Send them to **platform.claude.com/settings/keys** → *Create key* → name it after the agent →
   copy it (it starts with `sk-ant-api03-` and is shown once). Same rule: the org that has the
   credits.
2. They paste it in the chat. You write it to `.env` yourself — never echo it back, never print
   it in a command's output, never put it in any other file, never commit it:
   ```
   AGENTE_AUTH=api_key
   ANTHROPIC_API_KEY=<the key>
   ```
   Make sure `.gitignore` has `.env` **before** writing the key.
3. Verify for free (lists models, costs nothing). Read the key from `.env`, never type it into
   the command line:
   - Mac: `set -a; . ./.env; set +a; curl -s -o /dev/null -w '%{http_code}\n' https://api.anthropic.com/v1/models -H "x-api-key: $ANTHROPIC_API_KEY" -H 'anthropic-version: 2023-06-01'` → `200`
   - Windows: `$k = (Select-String -Path .env -Pattern '^ANTHROPIC_API_KEY=(.+)$').Matches[0].Groups[1].Value; (Invoke-WebRequest https://api.anthropic.com/v1/models -Headers @{'x-api-key'=$k;'anthropic-version'='2023-06-01'} -SkipHttpErrorCheck).StatusCode` → `200`
   - `401` = wrong or revoked key. `403`/billing error = org without credits.
4. Tell them: if they ever `export ANTHROPIC_API_KEY` in their shell profile, it wins over every
   other method (precedence row 1). `credenciales.*` removes stray credential variables for the
   agent's own process, but other tools on their machine will still see it.

### C · Claude subscription (Pro/Max) with `claude setup-token`

Only when A and B are not possible, or the user explicitly wants to use their own plan. It does
**not** use the workshop credits; usage counts against their plan limits; it is for personal
use, not for a product other people call.

1. In their own terminal (it needs a real TTY; inside Claude Code tell them to type
   `! claude setup-token`): `claude setup-token` → browser → copy the token
   (`sk-ant-oat01-…`, long-lived).
2. They paste it; you write:
   ```
   AGENTE_AUTH=suscripcion
   CLAUDE_CODE_OAUTH_TOKEN=<the token>
   ```
3. No free check exists for this token: the test run (a 1-turn call capped by `max_budget_usd`)
   is the verification.

---

## Precedence — who pays when several credentials exist

Verified 2026-11-07 with `claude auth status --json` under each combination, and real 1-turn
calls for the rows marked ✓call (bundled Claude Code 2.1.316):

| # | Credential present | Wins over | Evidence |
|---|---|---|---|
| 1 | `ANTHROPIC_API_KEY` in the environment | everything below | `authMethod: api_key` even with an OAuth token and a profile set |
| 2 | `CLAUDE_CODE_OAUTH_TOKEN` | 3–5 | a dummy token with a valid profile → `401 OAuth access token is invalid` ✓call |
| 3 | `ANTHROPIC_PROFILE=<existing profile>` (explicit) | 4–5 | `authMethod: oauth_token` with a claude.ai Max login present ✓call |
| 4 | claude.ai login of Claude Code (`/login`, Pro/Max) | 5 | `authMethod: claude.ai` |
| 5 | the active `ant` profile, implicit (no variable) | — | works only with no claude.ai login ✓call; with `ANTHROPIC_CONFIG_DIR` pointed at an empty dir → `Not logged in · Please run /login` ✓call |

Traps: `ANTHROPIC_PROFILE=<name that does not exist>` is ignored silently → row 4 or 5 pays.
A profile whose token expired and has no `refresh_token` (old logins) fails every call:
`credenciales` refuses both cases before the first call.

`credenciales.py` / `credenciales.ts` (generated next to the agent) turn this into a single
state: they read `AGENTE_AUTH` from `.env`, set only that credential, **remove the other two
variables from the agent's process**, check the profile file exists for path A, print one
`[auth] …` line without secrets, and stop with a clear message when anything is missing.

---

## DIAGNOSTICAR — message → fix

| Message | Cause | Fix |
|---|---|---|
| `ant: command not found` / `no se reconoce` | not installed, or Windows terminal opened before `winget` | install row above; on Windows open a new terminal |
| `[auth] No encuentro el perfil … de ant` | `ant auth login` not run, different profile name, or a config dir outside the searched places | `ant auth status`; copy the profile name to `.env`; set `ANTHROPIC_CONFIG_DIR` to the `Config dir` it prints |
| `Not logged in · Please run /login` | no credential reached Claude Code | re-run VERIFICAR for the chosen path; on Windows path A, set `ANTHROPIC_CONFIG_DIR` explicitly |
| `401 … invalid x-api-key` / `authentication_error` | key typo, revoked, or a stray `ANTHROPIC_API_KEY` in the shell overriding | re-paste; check stray variables (preflight last row) |
| `Credit balance is too low` | the org that pays has no credits: logged in to the wrong org, or the credits were claimed on another account | `ant auth status` shows the org; log out and log in with the account that claimed them |
| `OAuth token has expired` with `ant` | refresh failed (offline for days, or logged out elsewhere) | `ant auth login` again |
| `You've hit your session limit` | path C: plan quota exhausted | wait, or switch to A/B |
| The run works but the Console shows no spend | a claude.ai login is paying (no explicit `ANTHROPIC_PROFILE`) | path A with the profile name in `.env` |
