# Deck · "Construye tu primer agente de AI con Claude" (Claude Community Bogotá, 22 ago 2026)

HTML puro, paleta Anthropic (`styles/tokens.css`), animación con motion.dev vendorizado (`scripts/motion.js`, funciona offline). Las fuentes Anthropic Sans/Serif no se redistribuyen: el deck cae a la pila de sistema (`Inter`/`system-ui`, `Georgia`).

## Ver y presentar
```
python3 -m http.server 3030 --directory slides
open http://localhost:3030/                  # público
open "http://localhost:3030/?presenter=1"    # notas + timer + siguiente slide, solo en la pantalla local
open "http://localhost:3030/?motion=0"       # sin animaciones
```
Abrir `index.html` con doble click también funciona (`file://`).
Teclas: → / ← / espacio · `g N` salto · `?` ayuda. Reveals por click: 4 (tres tarjetas), 8 (loop), 6 / 14 / 17 (capturas de fallback: click 1 = captura, click 2 = GIF o segunda captura).

## Estructura
23 slides: Acto 1 (1–9) qué es un agente · Acto 2 (10–15) tres palancas + demo · Acto 3 (16–22) dónde corre · cierre (23).

## Demos
`demo/RUNBOOK.md` (comandos exactos). `demo/contabilidad.csv` sintético (proyecto 2210 sube ~10 pp, 1045 baja ~22 pp, 3322 plano). `demo/CLAUDE.md` = palanca "contexto del proyecto" para Claude Code. `demo/managed.py` sube el CSV y lo monta en una sesión de Managed Agents. `demo/agent.py` = el loop en ~100 líneas sobre la Messages API.

Si una demo falla, no se debuggea en vivo: en la slide de la demo, un click muestra la captura real y otro el GIF (`assets/fallback/`, `assets/gif/`).

## Diagramas
SVG inline en `index.html` (fuente: `assets/svg/*.svg`).
