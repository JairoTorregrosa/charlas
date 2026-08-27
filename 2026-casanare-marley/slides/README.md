# Deck — «Mi agente personal: la IA que crece contigo»

Jairo Torregrosa · Colombia 5.0 Casanare · Unitrópico, Yopal · 27 de agosto de 2026, 9:30 a.m.

HTML puro (skill `charla-slides`). Sin framework, sin build, sin red. Pensado para la
pantalla LED 16:9 del evento (pitch 3.9): 1920x1080, títulos ≥ 64 px, cuerpo ≥ 34 px,
líneas ≥ 3 px, contraste ≥ 4.5:1 en todo lo que se lee.

## Cómo abrirlo

```bash
# plan A: servidor local (lo mismo que ve deck-capture)
python3 -m http.server 3030 --directory slides
open http://localhost:3030/

# plan B: doble click. Funciona por file:// (nav.js NO es un módulo ES)
open slides/index.html
```

**Plan C si falla todo:** el PDF 16:9 (`deck-capture/scripts/export-pdf.sh`, una página
por slide) abierto en Preview a pantalla completa. Las fuentes van embebidas.

## Teclas

| Tecla | Qué hace |
|---|---|
| `→` `espacio` `PageDown` | siguiente reveal, o siguiente slide |
| `←` `PageUp` | atrás |
| `Home` / `End` | primera / última |
| `g` y luego un número | ir a esa slide |
| `?` | muestra u oculta la ayuda de teclas |
| click en cualquier parte | avanza |

`index.html#slide-11-receta` abre directo en esa slide.

`?motion=0` **no revela los pasos**: solo apaga transiciones, así que las slides con
`data-step` (4, 8, 10, 12, 14, 16, 23) salen a medias. Para ver o exportar todo revelado,
usa **`?steps=all`** (`http://localhost:3030/?steps=all`). Es también la forma de presentar
sin animaciones: en ese modo la flecha izquierda cambia de slide en vez de deshacer pasos, y
el velo «¿Y si…?» deja de tapar la slide y se coloca debajo del par Antes/Después.

## Vista de orador

`http://localhost:3030/?presenter=1` (o `slides/index.html?presenter=1`): slide actual a
la izquierda; a la derecha el título de la siguiente, el cronómetro y las notas de
`<aside class="notes">`. **Se abre solo en la pantalla del Mac, nunca en la proyectada.**

## Estructura

```
slides/
├── index.html          las 24 slides, una <section class="slide" id="slide-NN-slug">
├── styles/
│   ├── tokens.css      paleta CETUS + escala tipográfica (procedencia en el comentario)
│   └── deck.css        layouts, chrome, reveals, fuentes @font-face
├── scripts/nav.js      navegador vanilla (sin type="module": abre por file://)
├── assets/
│   ├── fonts/          Libre Caslon Display/Text self-hosted (woff2, sin Google Fonts)
│   ├── plancha/        la lámina del robot: estado-{0..5,full,recorrido}.png, loop.png, obj-*.png
│   ├── brand/          logo Cetus y sello de impresor (copias de brand/assets/); nada de esto
│   │                   se usa hoy en el deck
│   ├── style-anchor/   referencias de estilo de la marca
│   └── ...             ilustraciones y capturas del deck
└── README.md
```

Layouts en `deck.css`: `cover`, `figure`, `figure-labels`, `split`, `big-quote`, `cta`,
`close`. El título vive siempre en la misma posición (arriba a la izquierda); solo
`cover`, `big-quote` y `close` centran el cuerpo.

Reveals: cualquier elemento con `data-step="N"` aparece en el click N (`nav.js` le pone
`is-visible`). Las preguntas «¿Y si…?» son un velo a pantalla completa (`.andif`).

## Placeholders pendientes (P1/P2)

Todo lo que falta está marcado con `data-asset-pending`. Para listarlos:

```bash
grep -n 'data-asset-pending' slides/index.html
```

Ninguno de esos recuadros punteados puede quedar en el deck final.

## Verificación antes de presentar

```bash
bash ~/.claude/skills/deck-capture/scripts/capture-deck.sh  slides /tmp/deck --size 1920x1080
python3 ~/.claude/skills/deck-capture/scripts/contact-sheet.py /tmp/deck /tmp/deck/sheet.png
bash ~/.claude/skills/deck-capture/scripts/console-check.sh  slides
bash ~/.claude/skills/deck-capture/scripts/export-pdf.sh     slides \
     ../entrega/Jairo-Torregrosa-Mi-agente-personal-Casanare-2026.pdf --size 1920x1080 --steps all
```

`--steps all` es obligatorio en el PDF que se entrega: sin él, las páginas 4, 16 y 23
salen con el título y el cuerpo vacío, y las 8, 10, 12 y 14 salen tapadas por el velo
«¿Y si…?». El PDF que se manda a los organizadores vive en
`../entrega/Jairo-Torregrosa-Mi-agente-personal-Casanare-2026.pdf` (24 páginas, 1440x810 pt).

## Lo que va al USB

Solo lo que el deck referencia. Medido: **4.6 MB** de los 26 MB de la carpeta. El resto es
material de trabajo (referencias de estilo, prompts, scripts de generación, el montaje de
prueba, las piezas y los assets de marca de iteraciones descartadas):

```bash
rsync -a --exclude 'style-anchor' --exclude 'prompts' --exclude '*.py' \
      --exclude '_montage-test.html' --exclude 'pieza-*' --exclude 'cuerpo-base*' \
      --exclude 'marley-*' --exclude 'anatomia.css' --exclude '*.md' \
      --exclude 'logo-cetus.png' --exclude 'logo-cetus-dark.png' --exclude 'sello-impresor*' \
      --exclude 'obj-manos.png' --exclude 'obj-conversacion*' --exclude 'estado-0-noche.png' --exclude 'estado-2.png' --exclude 'obj-cuaderno.png' --exclude 'obj-despertador.png' --exclude 'obj-recetas.png' --exclude 'recorrido.svg' --exclude 'loop.svg' \
      slides/ /Volumes/USB/slides/
```

(quitar `--exclude '*.md'` si se quiere llevar también este README). Comprobado abriendo
`file:///Volumes/USB/slides/index.html`: 24 slides, todas las imágenes y las fuentes.
