# previews.md — the ASCII diagram for every option of every step

One diagram per option. Paste the fenced block **without the fence** into the
`preview` field of that option in `AskUserQuestion`. Nothing else goes in
`preview`.

**Rules that keep them readable**

- Max 14 lines × 70 columns. Everything here fits.
- Labels are Spanish (Platzi audience). **If the user writes in English,
  translate the labels on the fly** — keep the same boxes, arrows and layout.
  Glossary for the translation: `tú` → *you*, `archivos` → *files*,
  `piensa` → *thinks*, `turnos` → *turns*, `costo` → *cost*,
  `ayudante` → *helper*, `contexto` → *context*, `barato` → *cheap*.
- Never put an API name in the preview that the step does not actually
  produce. The exact code for each answer lives in `opciones-sdk.md`.
- The preview is the argument. The `description` is one short sentence.

---

## Step 0 · Credencial — "¿Con qué vas a pagar lo que gaste tu agente?"

Asked after the preflight passes (`auth.md`). Description lines: A "Sin crear ninguna key; usa los
créditos del taller", B "Una key de la consola, guardada en .env", C "Tu plan Pro/Max; no usa los
créditos".

### 0A · Login con ant *(Recomendado)*

```
tú ─► ant auth login ─► navegador: platform.claude.com
                         (el MISMO correo de los créditos)
                              │
                              ▼
        ~/.config/anthropic  ← token que se renueva solo
                              │
 agente.py ──► SDK ──► [ claude ] lee ese perfil
                              │
                              ▼
        paga la organización que tiene los créditos
        sin key que copiar, pegar ni filtrar
```

### 0B · API key de la consola

```
platform.claude.com/settings/keys ─► "Create key"
                              │  sk-ant-api03-…  (se ve UNA vez)
                              ▼
     la pegas aquí ─► .env   (en .gitignore, nunca a git)
                              │
 agente.py ──► SDK ──► [ claude ] usa la key
                              │
                              ▼
        paga la organización dueña de la key
        si la key se filtra, cualquiera gasta tus créditos
```

### 0C · Mi suscripción Pro/Max

```
tú ─► claude setup-token ─► navegador: claude.ai
                              │  sk-ant-oat01-…
                              ▼
     la pegas aquí ─► .env   (en .gitignore, nunca a git)
                              │
 agente.py ──► SDK ──► [ claude ] usa tu plan
                              │
                              ▼
        cuenta contra los límites de TU plan
        no usa los créditos · solo para uso personal
```

---

## Step 1 · Lenguaje — "¿En qué lenguaje quieres tu agente?"

### 1A · Python *(Recomendado)*

```
agente.py  ──►  claude-agent-sdk  ──►  [ claude ]
                                        subproceso que
     async for mensaje in query(...)     trae el SDK
            │
            └── imprime: texto · 🔧 tools · 💵 costo

  uv run agente.py          ← un comando, sin compilar
  también corre en un notebook (Jupyter)
```

### 1B · TypeScript

```
agente.ts  ──►  @anthropic-ai/claude-agent-sdk  ──►  [ claude ]

     for await (const m of query({...}))
            │
            └── imprime: texto · 🔧 tools · 💵 costo

  npx tsx agente.ts         ← tipos revisados antes de correr
  encaja en un proyecto Node / Next.js que ya tengas
```

---

## Step 2 · Objetivo — "¿Qué tiene que lograr tu agente?"

### 2A · Responder preguntas sobre mis archivos *(Recomendado)*

```
tú: "¿cuál proyecto perdió margen?"
     │
     ▼
┌───────────┐   Read/Glob/Grep   ┌──────────┐
│  Claude   │ ─────────────────► │   tus    │
│  (piensa) │ ◄───────────────── │ archivos │
└───────────┘   el contenido     └──────────┘
     │  no escribe nada, solo lee
     ▼
"Bodega Norte: 4,8% → -32,8%"     ← 3 turnos, $0.02
```

### 2B · Cambiar archivos o código

```
tú: "arregla el bug"
     │
     ▼
┌───────────┐   Read/Grep    ┌──────────┐
│  Claude   │ ─────────────► │   tus    │
│  (piensa) │ ◄───────────── │ archivos │
└───────────┘   Edit/Write   └──────────┘
     │  repite hasta que los tests pasen
     ▼
"listo, cambié auth.py"           ← 4 turnos, $0.03
```

### 2C · Llamar a mis funciones o APIs

```
tú: "¿cuánto vale el SKU 4471 con IVA?"
     │
     ▼
┌───────────┐  buscar_precio(sku)  ┌──────────────────┐
│  Claude   │ ───────────────────► │  TU función      │
│           │ ◄─────────────────── │  (tu código,     │
└───────────┘  {"content":[...]}   │   tu base datos) │
     │                             └──────────────────┘
     ▼   Claude no inventa el dato: lo pide
"178.500 COP"                     ← 2 turnos, $0.01
```

### 2D · Conversar varias vueltas con memoria

```
tú ──► ┌──────────────────────────────────┐
       │  sesión viva                     │
       │  turno 1: "analiza ventas.csv"   │
       │  turno 2: "¿y sin Bodega Norte?" │ ← recuerda el turno 1
       │  turno 3: "hazme el resumen"     │
       └──────────────────────────────────┘
              │
              ▼  el historial no se pierde entre preguntas
       una sola sesión, varios prompts
```

---

## Step 3 · Modelo — "¿Qué tan listo lo necesitas (y cuánto quieres pagar)?"

> Precios en dólares por millón de tokens (verificados 2026-11-02).
> Una corrida típica del taller mueve ~30 mil tokens: centavos.

### 3A · Sonnet 5.5 *(Recomendado)*

```
              entrada    salida     velocidad
  Fable 5.1   $10,00     $50,00     ▓▓▒▒▒
  Opus 5.5     $4,00     $20,00     ▓▓▓▒▒
▶ Sonnet 5.5   $2,00     $10,00     ▓▓▓▓▒   ◄ AQUÍ
  Haiku 5.5    $0,10      $0,50     ▓▓▓▓▓

  El equilibrio: entiende tareas de varios pasos y cuesta
  poco. Es el default de la casa. Si dudas, este.
```

### 3B · Haiku 5.5 — rápido y muy barato

```
              entrada    salida     velocidad
  Fable 5.1   $10,00     $50,00     ▓▓▒▒▒
  Opus 5.5     $4,00     $20,00     ▓▓▓▒▒
  Sonnet 5.5   $2,00     $10,00     ▓▓▓▓▒
▶ Haiku 5.5    $0,10      $0,50     ▓▓▓▓▓   ◄ AQUÍ

  Veinte veces más barato que Sonnet si el prompt cabe en
  100 mil tokens. Bien para buscar, listar, clasificar y
  como ayudante. Para razonar largo, sube a Sonnet.
```

### 3C · Opus 5.5 — razonamiento largo

```
              entrada    salida     velocidad
  Fable 5.1   $10,00     $50,00     ▓▓▒▒▒
▶ Opus 5.5     $4,00     $20,00     ▓▓▓▒▒   ◄ AQUÍ
  Sonnet 5.5   $2,00     $10,00     ▓▓▓▓▒
  Haiku 5.5    $0,10      $0,50     ▓▓▓▓▓

  2× el precio de Sonnet. Vale la pena solo si la tarea
  tiene muchos pasos que dependen unos de otros.
```

### 3D · Fable 5.1 — el más capaz

```
▶ Fable 5.1   $10,00     $50,00     ▓▓▒▒▒   ◄ AQUÍ
  Opus 5.5     $4,00     $20,00     ▓▓▓▒▒
  Sonnet 5.5   $2,00     $10,00     ▓▓▓▓▒
  Haiku 5.5    $0,10      $0,50     ▓▓▓▓▓

  5× Sonnet a la entrada, 5× a la salida. Para problemas
  que de verdad no salen con Sonnet. Empieza por Sonnet y
  sube solo si te quedas corto.
```

### 3-bis · Sub-pregunta de esfuerzo (solo si eligió Opus 5.5 o Fable 5.1)

Pregunta: *"¿Cuánto quieres que piense antes de responder?"* · header `Esfuerzo`

#### 3bis-A · Alto (`high`) *(Recomendado)*

```
  prompt ──► [ piensa ▓▓▓░░ ] ──► actúa ──► responde

  low     ▓░░░░  buscar, listar             rápido/barato
  medium  ▓▓░░░  ediciones de rutina
▶ high    ▓▓▓░░  refactors, depuración      ◄ AQUÍ
  xhigh   ▓▓▓▓░  tareas agénticas largas
  max     ▓▓▓▓▓  problemas multi-paso       lento/caro
```

#### 3bis-B · Muy alto (`xhigh`)

```
  prompt ──► [ piensa ▓▓▓▓░ ] ──► actúa ──► responde

  low     ▓░░░░  buscar, listar             rápido/barato
  medium  ▓▓░░░  ediciones de rutina
  high    ▓▓▓░░  refactors, depuración
▶ xhigh   ▓▓▓▓░  tareas agénticas largas    ◄ AQUÍ
  max     ▓▓▓▓▓  problemas multi-paso       lento/caro
```

#### 3bis-C · Medio (`medium`)

```
  prompt ──► [ piensa ▓▓░░░ ] ──► actúa ──► responde

  low     ▓░░░░  buscar, listar             rápido/barato
▶ medium  ▓▓░░░  ediciones de rutina        ◄ AQUÍ
  high    ▓▓▓░░  refactors, depuración
  xhigh   ▓▓▓▓░  tareas agénticas largas
  max     ▓▓▓▓▓  problemas multi-paso       lento/caro
```

---

## Step 4 · Instrucción — "¿Qué personalidad y reglas fijas tiene tu agente?"

### 4A · Mínimo + mis reglas *(Recomendado)*

```
┌──────────────────────────────┐
│ (nada de fábrica)            │ ← el SDK arranca casi en blanco
├──────────────────────────────┤
│ "Eres un analista de datos.  │ ← TÚ escribes esto
│  Respondes en español, en    │
│  máximo 5 viñetas. Nunca     │
│  inventas cifras."           │
└──────────────────────────────┘
   Contexto liviano y previsible: el agente hace lo que
   dice tu párrafo, nada más.
```

### 4B · Preset de Claude Code + mis reglas

```
┌──────────────────────────────┐
│ preset "claude_code"         │ ← Anthropic lo mantiene:
│  (cómo usar Read/Edit/Bash,  │   miles de palabras sobre
│   cómo buscar en un repo)    │   cómo trabajar con código
├──────────────────────────────┤
│ + tus reglas al final        │ ← TÚ escribes esto
│   "Nunca toques /secrets"    │
└──────────────────────────────┘
   Más contexto (y más costo por turno), pero el agente ya
   sabe moverse en un proyecto de código.
```

### 4C · Solo el preset de Claude Code

```
┌──────────────────────────────┐
│ preset "claude_code"         │ ← tal cual, sin agregarle nada
│  (cómo usar Read/Edit/Bash,  │
│   cómo buscar en un repo)    │
└──────────────────────────────┘

   Un Claude Code sin personalizar, manejado desde tu
   programa. Útil para reproducir lo que hace la terminal.
```

### 4D · Mío completo desde cero

```
┌──────────────────────────────┐
│ TODO lo escribes tú:         │
│  - quién es el agente        │
│  - qué método sigue          │
│  - qué nunca hace            │
│  - cómo se ve su respuesta   │
└──────────────────────────────┘
   Control total. También toda la responsabilidad: si no
   le dices cómo usar una tool, no la va a usar bien.
```

### 4-bis · Sub-pregunta de reglas (después de 4A, 4B o 4D)

Pregunta: *"¿Qué reglas fijas le pones?"* · header `Reglas`
Las tres plantillas de abajo, más "Otra" para escribirlas a mano.

#### 4bis-A · Analista de datos *(Recomendado)*

```
"Eres un analista de datos. Trabajas solo con los
 archivos del directorio. Reglas:
  - Nunca inventes una cifra: si no está, dilo.
  - Verifica cada número por un segundo camino.
  - Responde en español, máximo 5 viñetas.
  - Cierra con UNA frase de conclusión."
```

#### 4bis-B · Asistente de código

```
"Eres un asistente de código. Reglas:
  - Lee antes de escribir. Nunca edites a ciegas.
  - Un cambio a la vez, con su razón.
  - Corre los tests después de cada cambio.
  - Si algo falla dos veces, para y explica."
```

#### 4bis-C · Operador cuidadoso

```
"Eres un operador cuidadoso. Reglas:
  - Antes de una acción irreversible, pide confirmación.
  - Nunca borres archivos; muévelos a ./papelera/.
  - Explica qué vas a hacer ANTES de hacerlo.
  - Si la instrucción es ambigua, pregunta."
```

---

## Step 5 · Herramientas — "¿Qué puede hacer tu agente en el mundo?"

### 5A · Solo leer *(Recomendado)*

```
┌──────────┐         ┌──────────────────┐
│  Claude  │ ──Read──► leer un archivo  │
│          │ ──Glob──► listar por patrón│  tus archivos
│          │ ──Grep──► buscar texto     │
└──────────┘         └──────────────────┘
      ✗ no puede escribir
      ✗ no puede correr comandos

   Lo más seguro que existe: si se equivoca, no rompe nada.
   Empieza aquí y sube cuando lo necesites.
```

### 5B · Leer y escribir archivos

```
┌──────────┐         ┌──────────────────┐
│  Claude  │ ──Read──► leer             │
│          │ ──Glob──► listar           │  tus archivos
│          │ ──Grep──► buscar           │
│          │ ─Write──► crear archivo    │  ⚠ cambia disco
│          │ ──Edit──► cambiar líneas   │  ⚠ cambia disco
└──────────┘         └──────────────────┘
      ✗ no puede correr comandos

   Puede dejar un reporte escrito o arreglar tu código.
```

### 5C · Todo, incluida la terminal

```
┌──────────┐         ┌──────────────────┐
│  Claude  │ ──Read──► leer             │
│          │ ──Edit──► cambiar          │  tus archivos
│          │ ─Write──► crear            │
│          │ ──Bash──► CUALQUIER comando│  ⚠⚠ toda la máquina
└──────────┘         └──────────────────┘
       npm test · git commit · python script.py · curl

   El más capaz y el más peligroso. Úsalo en una carpeta
   aislada, y en el paso 8 ponle un freno.
```

### 5D · Mis propias funciones

```
┌──────────┐ "buscar_cliente(cliente_id)" ┌───────────────┐
│  Claude  │ ───────────────────────────► │  @tool en TU  │
│          │ ◄─────────────────────────── │  código       │
└──────────┘   {"content":[{"text":...}]} └───────────────┘
                                            tu API, tu BD,
   nombre real de la tool:                   tu Excel
   mcp__mi_servidor__buscar_cliente

   Claude no ejecuta tu función: la PIDE por su nombre y
   tu programa la corre. El dato es real, no inventado.
```

### 5-bis · Sub-pregunta MCP externo (solo después de 5D)

Pregunta: *"¿Además quieres conectar un servidor que ya existe?"* · header `MCP`

#### 5bis-A · No, solo mis funciones *(Recomendado)*

```
┌──────────┐
│  Claude  │ ──► tus funciones (mismo proceso, cero red)
└──────────┘

   Nada que instalar, nada que se caiga. Empieza así.
```

#### 5bis-B · Sí, un servidor MCP externo

```
┌──────────┐ ──► tus funciones (mismo proceso)
│  Claude  │
└──────────┘ ──► ┌──────────────────────────┐
                 │ servidor MCP externo     │
                 │  GitHub · Postgres ·     │  otro programa,
                 │  Slack · Sentry          │  ya escrito
                 └──────────────────────────┘
   Se arranca con un comando (`npx …`) o se conecta por URL.
   Necesita credenciales y que el servidor exista.
```

---

## Step 6 · Skills — "¿Necesita saber un procedimiento tuyo?"

### 6A · No por ahora *(Recomendado)*

```
contexto del agente (lo que "ve" en cada turno)
┌──────────────────────────────────────────┐
│ system prompt (paso 4)                   │
│ lista de tools (paso 5)                  │
└──────────────────────────────────────────┘
   Liviano y barato. Si tu procedimiento cabe en un
   párrafo, ya está en el system prompt: no necesitas más.
```

### 6B · Sí, una skill nueva

```
contexto del agente (lo que "ve" en cada turno)
┌──────────────────────────────────────────┐
│ system prompt (paso 4)                   │
│ lista de skills:                         │ ← solo nombre +
│   "facturar: cómo hacer una factura      │   descripción
│    colombiana con IVA y retención"       │   (barato)
│                                          │
│ [cuando la necesita] ──► SKILL.md entero │ ← se carga solo
└──────────────────────────────────────────┘   si aplica

   Un procedimiento largo que solo pesa cuando se usa.
```

### 6C · Sí, ya tengo skills en este proyecto

```
  tu proyecto/
   └── .claude/skills/
        ├── facturar/SKILL.md      ┐
        ├── conciliar/SKILL.md     ├─► el agente las
        └── reporte-mensual/…      ┘   descubre solas
                    │
                    ▼
   El agente lee esa carpeta al arrancar y usa la que
   corresponda. Tú no listas nada a mano.
```

---

## Step 7 · Subagentes — "¿La tarea es tan grande que conviene repartirla?"

### 7A · No, un solo agente *(Recomendado)*

```
       ┌──────────────┐
  tú ─►│   agente     │─► resultado
       │  (uno solo)  │
       └──────────────┘
        todo pasa por su contexto

   Más simple de entender y de depurar. Casi siempre
   alcanza. Reparte solo cuando el contexto se llene.
```

### 7B · Sí, un ayudante especializado

```
       ┌──────────────┐
  tú ─►│  principal   │─► resultado
       └──────┬───────┘
              │ "revisa esto"
              ▼
       ┌──────────────┐
       │  revisor     │  contexto en blanco, solo lectura,
       │  (solo lee)  │  modelo barato
       └──────────────┘
              │ devuelve 5 líneas, no 40 archivos
              ▲──────────────┘
```

### 7C · Sí, varios en paralelo

```
          ┌──────────┐
          │principal │  contexto limpio: solo ve resúmenes
          └────┬─────┘
     ┌─────────┼─────────┐
     ▼         ▼         ▼
 ┌──────┐  ┌──────┐  ┌──────┐
 │ ay. 1│  │ ay. 2│  │ ay. 3│   cada uno lee SU parte
 └──┬───┘  └──┬───┘  └──┬───┘   y devuelve 5 líneas
    └─────────┴─────────┘
   Más rápido en tareas anchas. Cuesta más: cada ayudante
   paga sus propios tokens.
```

---

## Step 8 · Permisos — "¿Quién autoriza cada acción del agente?"

### 8A · Aprueba solo lo que listé *(Recomendado)*

```
Claude quiere: Read("ventas.csv")
      │
      ▼
 ¿está en mi lista de tools aprobadas?
      ├── sí ──► corre
      └── no ──► se DENIEGA en silencio

   Lista: Read, Glob, Grep   ← lo del paso 5, nada más

   Predecible y sin interrupciones. Si el agente "no hace
   nada", casi siempre es que pidió algo fuera de la lista.
```

### 8B · Que edite archivos sin preguntar

```
Claude quiere: Edit("auth.py")
      │
      ▼
 ¿es una edición de archivo o un mkdir/mv/cp?
      ├── sí ──► corre SIN preguntar     ⚠ cambia tu disco
      └── no ──► pasa por las reglas normales

   Cómodo para prototipar en una carpeta aislada.
   Trabaja sobre una copia o con git limpio.
```

### 8C · Que me pregunte a mí (humano en el loop)

```
Claude quiere: Bash("rm -rf build/")
      │
      ▼
 hooks ─► reglas deny ─► reglas ask ─► modo ─► TU función
                                              ┌───────────┐
   la terminal se detiene y te pregunta ─────►│ ✅ permitir│
                                              │ ❌ denegar │
                                              │  + motivo  │
                                              └───────────┘
   El motivo que escribas lo LEE el modelo y busca otra
   vía. Es una conversación, no un portazo.
```

### 8D · Sin frenos (solo en sandbox)

```
  ⚠⚠⚠  Claude corre TODO lo que decida, sin preguntar  ⚠⚠⚠

Claude quiere: Bash("rm -rf ~/")
      │
      ▼
   corre.                    no hay confirmación,
                             no hay deshacer.

   Solo dentro de un contenedor o una VM desechable.
   Nunca en tu máquina de trabajo, nunca con tus datos.
```

---

## Step 9 · Hooks — "¿Quieres un vigilante automático, código tuyo, en el ciclo?"

### 9A · No por ahora *(Recomendado)*

```
  Claude pide una tool
        │
        ▼
  ┌─────────────────┐
  │ permisos (paso 8)│ ──► corre o se deniega
  └─────────────────┘

   Los permisos del paso 8 ya te cubren. Los hooks son
   para cuando necesitas TU lógica dentro del ciclo.
```

### 9B · Bloquear comandos peligrosos

```
  Claude pide Bash("rm -rf /")
        │
        ▼
  ┌──────────────────────────┐
  │ hook PreToolUse (tuyo)   │ corre en TU proceso,
  │ if "rm -rf" in comando:  │ no gasta contexto
  │    → deny + razón        │
  └──────────────────────────┘
        │
        ▼  "denegado: mueve a ./papelera/ en su lugar"
   Claude lee la razón y busca otra vía. Y el hook manda
   incluso si el modo de permisos aprobaba todo.
```

### 9C · Guardar un registro de todo lo que hace

```
  Claude usa una tool
        │
        ├──► corre normal (el hook no frena nada)
        │
        └──► ┌────────────────────────┐
             │ hook PostToolUse (tuyo)│
             │ escribe una línea JSON │──► auditoria.jsonl
             └────────────────────────┘

   Después:  cat auditoria.jsonl | jq
   Qué hizo, cuándo, con qué argumentos. Sin frenar nada.
```

### 9D · Verificar el trabajo al final

```
  Claude dice "listo"
        │
        ▼
  ┌──────────────────────────┐
  │ hook Stop (tuyo)         │
  │ ¿existe out/reporte.md?  │
  │   no → "block" + motivo  │──► el turno NO termina:
  │   sí → pasa              │    Claude sigue trabajando
  └──────────────────────────┘
        │ sí
        ▼   result

   Es un `if`, no un modelo. El agente no puede decir
   "listo" sin haber dejado el entregable.
```
