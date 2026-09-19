# Las seis piezas y cómo elegir entre ellas

El LLM decide. Todo lo demás vive en el harness.

| Pieza | Qué es | Quién la arranca | A dónde van sus tokens |
|---|---|---|---|
| **Harness** | El runtime alrededor del LLM: el loop, las tools, el manejo del contexto, los permisos. «Claude Code is the harness; Claude is the model inside it.» El Agent SDK es ese harness como librería. | Siempre está corriendo | Es el dueño del contexto |
| **Tool** | Una acción que el LLM puede pedir. Tiene nombre y esquema; su resultado vuelve al loop. | El LLM | Esquema y resultado entran al contexto principal |
| **MCP** | Un protocolo abierto para recibir tools de servidores externos. Es la forma de conectar tools; para el LLM siguen siendo tools. | El LLM, a través de las tools que expone | Cada esquema cuesta contexto |
| **Skill** | Un `SKILL.md` con un procedimiento, más scripts y recursos opcionales. Solo la descripción está siempre en contexto; el cuerpo entra cuando se pide. | El LLM cuando la ve relevante | El cuerpo entra al contexto principal (en el transcript se ve como un user message) |
| **Subagente** | Otra instancia del LLM con su propio contexto, system prompt, tools y permisos. Hace una tarea delegada y devuelve un resumen. | El LLM, con un tool call | Contexto aparte; solo vuelve el resumen |
| **Hook** | Código tuyo que corre en un punto fijo del ciclo: antes de una tool, después, al arrancar, al parar. | **El harness, de forma determinista. El LLM no lo decide.** | Ninguno, salvo que el hook inyecte salida |

## Dos preguntas que las separan

```
¿Quién decide cuándo corre?
  el LLM (probabilístico)      → tool, tool de MCP, skill, subagente
  el harness (determinista)    → hook, regla de permisos, topes

¿Dónde vive el trabajo?
  contexto principal           → tool result, cuerpo de la skill
  contexto aislado             → subagente
  fuera del LLM                → hook, proceso del servidor MCP
```

## Cuál usar

- Darle al LLM un procedimiento → **skill**.
- Darle acceso a un sistema externo → **MCP** (o una tool propia si el sistema es tu código).
- Sacar trabajo voluminoso del contexto principal → **subagente**. Gasta más tokens en total y baja el pico de contexto. Rinde cuando la tarea es un procedimiento con entrada y salida claras.
- Obligar un comportamiento → **hook** o **permisos**. Una instrucción en el system prompt es una petición; un hook es una garantía.

Cuando compares corridas, anota la versión del harness (tu código, tus skills, tus tools) junto a la del modelo: cambiar cualquiera de los dos cambia el resultado.

Fuentes: glosario de Claude Code (code.claude.com/docs/en/glossary), Hooks reference (code.claude.com/docs/en/hooks), Create custom subagents (code.claude.com/docs/en/sub-agents).
