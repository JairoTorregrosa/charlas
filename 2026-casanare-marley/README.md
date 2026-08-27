# Mi agente personal: la IA que crece contigo

Colombia 5.0 Casanare · Unitrópico, Yopal · 27 de agosto de 2026 · 45 minutos · público general.

Marley es mi asistente personal. Corre 24/7 en un computador del tamaño de un libro en mi casa, en Bogotá, y me escribe solo a las 7 de la mañana. Esta es la guía de la charla: qué es un agente, cómo armé el cuerpo de Marley pieza por pieza y por qué funciona como mi asistente.

## Un agente es un cerebro con cuerpo

El **cerebro** es un modelo de lenguaje (LLM). Se alquila y vive en la nube: recibe texto y adivina el texto que sigue. Solo, detrás de una ventanilla, no ve tu correo ni se acuerda de ti mañana.

El **cuerpo** lo armas tú, pieza por pieza. Marley tiene cinco:

| # | Objeto cotidiano | Lo que hace | La palabra real |
|---|---|---|---|
| 1 | **La conversación** (el chat y el manual) | Siempre le hablo por el mismo chat, como a una persona. Un manual escrito por mí dice cómo responde y dónde se detiene. | Telegram / Discord · system prompt (`SOUL.md`) |
| 2 | **Las manos** (botones y adaptador) | Cada servicio que uso aparece como un botón con permiso: correo, Drive, X. Un adaptador convierte apps como Chrome en botones. | tools · MCP |
| 3 | **Las recetas** | Procedimientos escritos una vez, en español, que saca cuando llega esa tarea. | skills |
| 4 | **El cuaderno** | Quién soy y qué me importa; lo consulta al arrancar. Solo hechos estables. | memoria (`USER.md`, `MEMORY.md`) |
| 5 | **El despertador** | A una hora fija repite una tarea que escribí yo, sin que nadie le escriba ese día. | cron |

Juntos son un agente: el cerebro pide un botón, el cuerpo lo aprieta y le cuenta qué pasó, el cerebro vuelve a pensar. Ese círculo, repetido, es un agente.

## Por qué funciona como mi asistente

- **Me conoce** (cuaderno).
- **Puede actuar, con permiso** (manos).
- **Me escribe antes de que yo abra el chat** (despertador). Yo definí la tarea y la hora; la alarma solo repite.

Y crece: a las 3 de la mañana revisa su propio trabajo, corrige sus recetas y sus alarmas por su cuenta. Lo delicado (código, identidad, claves) queda bloqueado o espera permiso.

## Antes de armar uno

Para casi todo, ChatGPT basta. Un agente vale la pena cuando la tarea se repite y necesita varios servicios. Lo que le mandas al cerebro viaja a la nube; cuesta una suscripción y un computador encendido; lo delicado requiere permiso.

## Arma tu propio Marley

Marley corre sobre **Hermes Agent** (Nous Research, licencia MIT, abierto y gratuito): https://github.com/NousResearch/hermes-agent

Orden sugerido: primero decide qué tarea vale la pena. Después, las piezas: chat → manual → botones → receta → cuaderno → despertador.

## Contenido del kit

- `slides/` — el deck tal como se proyectó (HTML puro; abre `index.html`; `?presenter=1` para notas).
- `Mi-agente-personal-Casanare-2026.pdf` — el PDF 16:9 entregado a los organizadores.

Contacto: [@jai_torregrosa](https://x.com/jai_torregrosa)
