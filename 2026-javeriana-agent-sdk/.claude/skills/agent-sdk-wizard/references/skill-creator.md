# skill-creator.md — write the agent's skill well (step 6)

Read this when step 6 = "una skill nueva", or whenever the agent's job is a repeatable
procedure with domain rules (classify expenses, review a diff, write the morning summary). A
skill is the agent's manual: the wizard writes it, the agent loads it only when it applies.
This is a condensed, self-contained version of Anthropic's skill-authoring guidance; you do not
need any other skill installed.

## Facts already verified (2026-11-07)

- A skill is a folder with `SKILL.md` (YAML frontmatter `name` + `description`, then Markdown
  body) and optional files. Three levels load progressively: (1) name + description, always in
  context; (2) the body, when the model decides the skill applies; (3) files the body points at,
  read or executed only when needed. Source:
  platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- `description`: third person, says **what** it does **and when** to use it with concrete
  trigger words; max 1024 characters; `name`: lowercase letters, digits, hyphens, ≤ 64. Same
  source.
- Body under ~500 lines; split detail into reference files **one level deep** from SKILL.md
  (no chains of references); a long reference gets a table of contents. Same source.
- Agent SDK: skills are files only (no programmatic API). The SDK discovers
  `<cwd>/.claude/skills/<name>/SKILL.md` (and parents up to the repo root) when
  `setting_sources` includes `"project"`; `skills=["<name>"]` restricts invocation to the listed
  names and adds the `Skill` tool automatically; if you also pass an explicit `tools` list,
  include `"Skill"`. Confirm loading in the `init` message's `skills` array. Source:
  code.claude.com/docs/en/agent-sdk/skills

## Do this

1. **Name** the skill after the procedure, gerund or verb-noun, Spanish, no accents:
   `clasificar-gastos`, `revisar-diff`, `resumen-del-dia`.
2. **Description** (the one line that decides whether it ever runs):
   `<Qué hace, en tercera persona>. Úsala cuando <disparadores concretos: palabras del usuario,
   tipos de archivo, situaciones>.` Example: *"Clasifica los movimientos de un extracto bancario
   en categorías y cuadra los totales contra el saldo. Úsala cuando pidan revisar gastos,
   extractos, suscripciones o un CSV de movimientos."*
3. **Body**, from `templates/skill.md.tmpl`:
   - one sentence of purpose;
   - `## Procedimiento`: numbered steps, each with the exact tool or script; include the
     verification step (re-read output, check totals) — a feedback loop beats a longer prompt;
   - `## Reglas`: the domain rules the model cannot know, each with its why;
   - `## Formato de entrega`: a template of the output (the template pattern is the most
     reliable way to get consistent results);
   - `## Recursos`: one bullet per extra file, saying **when** to read it.
4. **references/** when there is real detail (a category table, a style guide, an API's field
   list, a checklist longer than ~30 lines): `references/<tema>.md`, linked from the body with
   "lee `references/categorias.md` cuando …". Create at least one when
   the user's domain has rules or reference data; do not create empty ones.
5. **scripts/** when a step is deterministic (sum, parse, validate): a small Python script the
   body runs with `python3 ${CLAUDE_SKILL_DIR}/scripts/<x>.py <args>` and whose output the agent
   uses. Code computes; the model decides. Test the script once yourself. If the agent has no
   `Bash` (most guardrails remove it), put that deterministic logic in a custom tool
   (`@tool` / `tool()`, step 5) instead of `scripts/`, and have the procedure call the tool.
6. **Degrees of freedom**: fragile, exact procedures → precise steps and scripts; judgment calls
   → principles and examples.
7. Wire it in the agent (`setting_sources=["project"]`, `skills=["<name>"]`, `cwd` at or below
   the folder that holds `.claude/skills/`), and in the stream reader confirm the `init` message
   lists the skill. The test prompt must trigger it: the transcript should show
   `🔧 Skill(<name>)` before the work.

## Rules

- No placeholders left (`{{…}}`), no bullets pointing at files that do not exist — the agent
  will waste turns looking for them.
- No time-sensitive facts in the body ("hasta diciembre usa la v1"); put dated facts in a
  reference with the date.
- One term per concept throughout (do not alternate "movimiento", "transacción", "registro").
- Keep the frontmatter to `name` and `description` unless a field is needed. In the SDK,
  `allowed-tools` in the frontmatter **pre-approves** tools while the skill runs; it does not
  restrict anything.
- After the first real run, read the transcript with the user: if the skill was not invoked,
  the description is the first suspect; if it was invoked but the result is off, the procedure
  is.
