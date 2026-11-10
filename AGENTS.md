# Agent instructions

## Code Review Rules

Review as the person who runs this software, not as a style checker. A
finding names an input, a state or a sequence of actions that produces a
wrong result, lost data or a broken flow for that person, and says what
they see when it happens. Without that, there is no finding.

### A confident wrong answer is the worst outcome

A visible failure is better than a quiet lie. Flag anything that turns a
missing or malformed input into a plausible-looking result: a fallback
that invents a value, a partial result presented as complete, an error
swallowed into a default, a retry that hides the first failure.

Safe path: fail loudly, return nothing, or mark the result as degraded
where the user will see it.

### Data that crosses a boundary is not ours

Input from a network, a file, a user, a model or another process can be
absent, malformed or hostile. Flag a read that does not cover those
cases, and any secret, token or personal datum that reaches a log, a URL,
an error message or a third party.

Safe path: validate at the boundary, keep secrets out of anything that
is stored or shared, and declare what could not be verified.

### What not to report

CI owns formatting, lint and tests. Do not spend a comment on
formatting, naming, comment wording, test names, doc phrasing, or a
refactor that changes nothing the user sees. Do not report an input the
system cannot receive, or a defect someone has to construct on purpose
to trigger.

One finding that costs a user beats five that cost a reviewer their
attention. When nothing meets that bar, say so and approve.

## Añadir o cambiar una charla

`charlas.toml` es la única fuente del catálogo. El bloque `indice` del README raíz, el
bloque `ficha` de cada kit, `portada.jpg` y `vistazo.jpg` los escribe
`scripts/catalogo.py`. No se editan a mano.

1. Carpeta `AAAA-<lugar>-<tema>/` con el deck en PDF.
2. Su `[[charla]]` en `charlas.toml`. La fecha, el lugar y `evento_url` salen de una
   fuente que abriste (el deck, Luma, el sitio del evento), no de memoria.
3. `uv run scripts/catalogo.py`, y sube todo lo que escriba.

`uv run scripts/catalogo.py --check` corre en cada PR y falla si falta un paso.
`uv run scripts/catalogo.py --enlaces` pide cada URL externa del catálogo.

No renombres carpetas de kits ni PDF. Los decks ya proyectados y sus QR imprimen esas
rutas, y no se pueden volver a exportar.
