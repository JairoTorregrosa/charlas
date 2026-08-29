# docs/: cheat sheets del Agent SDK

Siete hojas, para tener al lado mientras escribes un agente. Python primero.

| Archivo | Cuándo abrirlo |
|---|---|
| `event_model.md` | "¿Qué me está llegando en el `async for`?" Las 7 clases, sus subtipos, bloques y el orden |
| `options.md` | "¿Cómo se llama esa opción y qué default tiene?" `ClaudeAgentOptions`, las que importan, con su trampa |
| `tools.md` | "¿Qué campo tiene el input de `Read`?" Las tools nativas, las tres listas que se confunden, la sintaxis de reglas |
| `workspace.md` | "¿Dónde pongo el skill / el ayudante / el MCP?" Lo que el agente carga de su carpeta y el formato de cada archivo |
| `permisos_hooks.md` | "¿Por qué corrió (o no) esa tool?" Los seis porteros en orden, la forma de un hook, `can_use_tool` |
| `errores.md` | "Se rompió." Síntoma → causa → arreglo, en el orden en que pasan en una sala |
| `proveedores.md` | "¿Y si no tengo suscripción de Claude?" El mismo agente con OpenRouter, OpenCode Zen o la suscripción de ChatGPT vía LiteLLM |

Verificado contra `claude-agent-sdk` 0.2.148 y Claude Code 2.1.251 (2026-08-29). Si algo aquí contradice el `init` de tu corrida, gana el `init`.
