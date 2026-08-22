# RUNBOOK · demos de "Construye tu primer agente de AI con Claude" (22 ago 2026)

Regla: cada demo ≤5 min. Si falla, no se debuggea en vivo: captura en `../assets/fallback/`.

## Antes de empezar (Jairo)
- `export ANTHROPIC_API_KEY=...` (D3).
- `export MANAGED_ENV_ID=env_...` (tu environment; verlo en Console → Managed Agents → Environments).
- Smoke test: `python -c "import anthropic; print(anthropic.__version__)"` (se espera ≥1.0). Plan B si el Python del sistema no lo tiene: `uv run --with "anthropic>=1.0" python managed.py`.
- Console abierta en Managed Agents → Sessions, con una sesión nueva del agente `General Assistant` y `contabilidad.csv` ya subido (D1).
- `claude` logueado; terminal abierta en `slides/demo/` (D2).
- Deck servido: `python3 -m http.server 3030 --directory slides` → `http://localhost:3030/` (presenter: `?presenter=1` en la pantalla local).

## D1 · min ~8 · "Mira cada vuelta del loop" (Console, sin código)
1. Console → Managed Agents → Sessions → sesión preparada.
2. Enviar: `¿Cómo cambió el margen por proyecto de junio a julio, y por qué? El archivo está en /mnt/session/uploads/contabilidad.csv. Ingresos: cuentas 4. Costos: cuentas 6 y 7.`
3. Abrir la pestaña Events/Tools. Narrar: pidió bash → leyó el CSV → calculó → volvió a pedir → respondió.
4. Plan A alternativo: sesión con el agente `Analista financiero (demo)` (system prompt de `managed.py`) y el prompt corto de la slide: `¿Cómo cambió el margen por proyecto de junio a julio, y por qué?`. El prompt largo del paso 2 es para `General Assistant`, que no tiene reglas.
5. Fallback: click 1 = `../assets/fallback/d1-console.png` · click 2 = `../assets/fallback/d1-console-2.png`.

## D3 · min ~27 · "Las tres palancas, corriendo" (API)
```
python managed.py
```
- Muestra: agente creado (system prompt + toolset) → sesión con la pregunta → respuesta.
- Nota: `managed.py` sube `contabilidad.csv` con `files.upload` y lo monta en la sesión en `/mnt/session/uploads/contabilidad.csv` (`sessions.create(resources=[...])`). Ensayado con éxito: la respuesta da la tabla de margen por proyecto. Plan B: la sesión de D1 en Console.
- Fallback: click 1 = `../assets/fallback/d3-managed.png` · click 2 = `../assets/gif/d3-managed.gif` · click 3 = `../assets/fallback/d3-managed-2.png`.

## D2 · min ~32 · "Claude Code analiza el mismo CSV"
```
cd slides/demo && claude
```
Prompt (el corto de la slide; `CLAUDE.md` aporta las reglas, así que basta): `¿Cómo cambió el margen por proyecto de junio a julio, y por qué? Muestra el código.`
- `slides/demo/CLAUDE.md` es la palanca "contexto del proyecto": reglas contables, CSV (';', decimal con coma; ingresos en cuentas 4, costos en 6 y 7), `uv run --with pandas` (pandas no está en el Python del sistema) y formato de respuesta (tabla → causa → código). Señalarlo en la slide 18.
- Ensayado con `claude --dangerously-skip-permissions` (la captura y el GIF muestran "bypass permissions on"). En vivo: `claude` a secas; si pide permiso para Bash, aceptar y señalarlo (slide 16: "pide permiso").
- Ensayado 2 veces (vhs): ~2 min; Claude Code usa `uv run --with pandas` y responde con tabla + código.
- Señalar las tool calls (Read, Bash) y la respuesta con cifra, código y causa.
- Fallback: click 1 = `../assets/fallback/d2-claude-code.png` · click 2 = `../assets/gif/d2-claude-code.gif`.

## Referencia · el loop en ~100 líneas (no corre en vivo)
```
export ANTHROPIC_API_KEY=...
python agent.py "¿Cómo cambió el margen por proyecto de junio a julio, y por qué?"
```
Se muestra como código en la slide 5 y va al repo público.

## Datos
`contabilidad.csv` es sintético. El generador y la historia plantada están en `../../proceso/demo-meta/` (fuera de `slides/` y del cwd de la demo, para que Claude Code no lea la respuesta).
