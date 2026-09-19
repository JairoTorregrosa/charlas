# Diagramas ASCII para el wizard

Úsalos en el campo `preview` de AskUserQuestion y en las explicaciones. Adáptalos al agente concreto: cambia los nombres de las tools y del objetivo. Máximo ~16 líneas y ~60 columnas por preview.

## El loop (para explicar qué se va a construir)

```
 pedido ──▶ ┌─────────── HARNESS (Agent SDK) ───────────┐
            │  contexto: system prompt + todo lo dicho   │
            │        │                                   │
            │        ▼            tool call              │
            │     ┌─────┐ ──────▶ hook ──▶ tools         │
            │     │ LLM │ ◀────── tool result            │
            │     └─────┘   (repite hasta terminar)      │
            └────────│──────────────────────────────────┘
                     ▼
                 resultado  +  salidas/<fecha>/transcript.md
```

## Paso «cómo corre»

```
UNA VEZ Y SALE                 CONVERSACIÓN
pedido ─▶ loop ─▶ archivo      tú ─▶ loop ─▶ respuesta
cron · CI · webhook · script    ▲                │
nadie responde en el medio      └── resume ◀─────┘
```

## Paso «de dónde salen los datos»

```
TOOL PROPIA              MCP EXTERNO                ARCHIVOS LOCALES
tu función, tu código    servidor de otro           workspace/datos/*
┌────────┐               ┌────────┐  ┌─────────┐    ┌────────┐
│ agente │─▶ hoy()       │ agente │─▶│ GitHub  │    │ agente │─▶ Read
└────────┘               └────────┘  │ Linear… │    └────────┘   Glob
corre en tu proceso      └─────────┘                Grep
sin credenciales         token u OAuth              lo más simple
```

## Paso «procedimiento»

```
SIN SKILL                          CON SKILL
el LLM improvisa los pasos         workspace/.claude/skills/<n>/SKILL.md
cada corrida puede variar          1. pide la fecha
                                   2. busca
                                   3. ignora lo que no aplica
                                   4. lee completo
                                   5. responde en este formato
                                   entra al contexto solo cuando se pide
```

## Paso «guardrails»

```
¿Quién decide cuándo corre?
  el LLM lo pide  (puede pasar o no) ─▶ tool · MCP · skill · subagente
  el harness obliga (pasa siempre)   ─▶ permisos · hook · topes

tools            qué existe          ["Read","Skill"]
allowed_tools    qué corre solo      ["Read","mcp__propias__x"]
disallowed_tools qué nunca corre     ["Bash","Write"]
hook PreToolUse  mira los ARGUMENTOS  leer(id="c4") ─▶ deny + motivo
topes            max_turns=12 · max_budget_usd=0.25
```

## Paso «subagente, sí o no»

```
SIN SUBAGENTE                       CON SUBAGENTE
contexto principal                  contexto principal
  buscar ▸ 40 resultados              Agent("revisa los correos")
  leer   ▸ correo 1                   ◀── 1 resumen
  leer   ▸ correo 2                 contexto del subagente (aparte)
  …todo se queda ahí                  buscar, leer, leer…
más barato en total                 más tokens en total, pico más bajo
```

## Arquitecturas por familia (para el brainstorm)

```
ASISTENTE PERSONAL                  VENTAS / PROSPECCIÓN
agenda.json ─┐                      leads.csv ─▶ priorizar ─▶ borrador
correos/*.md ─┼▶ agente ─▶ hoy.md   (nunca envía: deja borradores)
tareas.md ───┘   + crear_borrador

CÓDIGO Y QA                         DATOS
cambio.diff ─▶ Read/Grep ─▶ tests   ventas.csv ─▶ consultar() ─▶ alerta.md
            ─▶ revision.md          (solo lectura)

FINANZAS                            MARKETING
movimientos.csv ─▶ categorizar      guia_de_marca.md ─▶ posts.md
(no mueve dinero, no asesora)       (no publica)

INVESTIGACIÓN                       DOCUMENTOS / ATENCIÓN
fuentes.md ─▶ WebFetch(lista        contrato.md + norma.md ─▶ hallazgos.md
blanca) ─▶ digest.md                tickets/*.md ─▶ respuesta_borrador.md
```
