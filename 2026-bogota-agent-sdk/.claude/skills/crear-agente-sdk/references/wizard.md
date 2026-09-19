# El wizard, paso a paso

Conduce la creación como un wizard. En cada paso usa la tool **AskUserQuestion**: una pregunta, de dos a cuatro opciones, la recomendada primero con «(Recomendado)», y un `preview` con un diagrama ASCII que muestre cómo queda el agente con esa opción. Los diagramas base están en `references/diagramas.md`: adáptalos con los nombres reales del agente de la persona. Antes de cada pregunta escribe una o dos líneas que expliquen qué se decide y por qué importa; después de cada respuesta confirma en una línea lo que quedó.

Salta los pasos que el pedido ya responde. Si la persona dice «decide tú» o estás corriendo sin humano (`claude -p`), elige la opción recomendada en todos y sigue. Si AskUserQuestion no está disponible, haz la misma pregunta en texto con las opciones numeradas y el diagrama en un bloque de código.

| Paso | Pregunta | Opciones típicas | Diagrama |
|---|---|---|---|
| 0 · Idea | ¿Qué agente quieres? Solo si llega sin idea o con una vaga («de ventas», «automatizar mi trabajo») | Opción 1: el «primer agente recomendado» de la familia más cercana en `references/ideas.md`. Opciones 2–3: variantes que tú derivas de las mismas piezas de esa familia (otra pregunta sobre los mismos datos, una más pequeña, una algo más ambiciosa) | Arquitecturas por familia |
| 1 · Objetivo | ¿Cuál de estas frases describe lo que debe resolver? | 2–3 redacciones del objetivo en una frase, de la más pequeña a la más ambiciosa. Recomienda la pequeña | El loop, con su pedido y su resultado |
| 2 · Lenguaje | ¿Python o TypeScript? No preguntes si la carpeta ya tiene `pyproject.toml` o `package.json` | Python (uv) · TypeScript (Node o bun) | — (usa `preview` con las 8 primeras líneas del agente en cada lenguaje) |
| 3 · Cómo corre | ¿Una vez y sale, o conversación? | Una vez y sale (Recomendado) · Conversación con `resume` | «cómo corre» |
| 4 · Datos y acciones | ¿De dónde salen los datos? (multiSelect) | Archivos locales de ejemplo (Recomendado) · Tool propia · MCP externo · Web | «de dónde salen los datos» |
| 5 · Procedimiento | ¿El agente debe seguir siempre los mismos pasos? | Sí, con una skill (Recomendado) · No, que decida | «procedimiento» |
| 6 · Guardrails | ¿Qué no debe hacer nunca? (multiSelect) | Solo lectura (Recomendado) · Acciones hacia afuera solo como borrador · Bloquear por argumentos con un hook · Lista blanca de dominios | «guardrails» |
| 7 · Subagente | Solo si el trabajo llena el contexto de material que el principal no necesita | Sin subagente (Recomendado) · Con subagente | «subagente, sí o no» |

Cierra el wizard con un **plano** antes de escribir código: un diagrama ASCII del agente final con sus tools, su skill y sus guardrails reales, y la lista de archivos que vas a crear. Pide confirmación con una última AskUserQuestion: «Construirlo así (Recomendado)» · «Cambiar algo».

Si el objetivo se resuelve con pasos fijos y conocidos, dilo en el paso 1: eso es un script o un workflow, y un agente sale más caro y menos predecible. Sigue solo si la persona confirma.

## Usa los diagramas también para explicar

Cuando la persona pregunte «¿qué es un hook?», «¿tool o MCP?», «¿por qué una skill?», responde con el diagrama correspondiente de `references/diagramas.md` y la tabla de `references/conceptos.md`, y aterrízalo en su agente. Al entregar, vuelve a dibujar el plano con lo que de verdad quedó.

