# Hackathon · instrucciones para los equipos

Reto del *Claude Workshop | AI Agents for business analytics competition* (Quick Logística, Bogotá, 22 ago 2026): responder **7 preguntas financieras** sobre los datos reales (pseudonimizados) del CASO FINANCIERO de Quick con un agente. Da igual el stack (Claude Agent SDK, Claude Code, Managed Agents, LangGraph o un loop propio): entregas **respuesta + traza** y un juez automático las puntúa contra un golden dataset.

**Leaderboard y entrega:** <https://quick-golden-bench.vercel.app>

## Pasos
1. Lee [`SUBMIT.md`](SUBMIT.md): formato de `answers/qNN.json`, cómo guardar la traza según tu stack, cómo se puntúa (calidad × coste → valor).
2. Lee [`CONVENTIONS.md`](CONVENTIONS.md): reglas contables del golden (ingreso, costo, margen, línea, facturación real, retroactivo). Si usas otra convención, decláralo.
3. Descarga los datos: [`data/CASO-FINANCIERO.zip`](data/CASO-FINANCIERO.zip) (14 MB; datos reales pseudonimizados de Quick, publicados con su OK; sha256 `93c74fd279349d3419d28f8019c73c8ddbcccbc23848ea2cf1a5f8dbf627139d`). Dentro: `Caso Financiero.docx`, `Preguntas.docx`, `MAYO-JUNIO-JULIO 2026.csv.zip` (descomprímelo también) y `Nomina/0{5,6,7}. …/` con nómina y ausencias por mes. Los enunciados los referencian como `/data/…`: móntalos o ajusta la ruta a tu agente.
4. Entrega con un comando (sin cuenta ni token):
   ```bash
   curl -sO https://quick-golden-bench.vercel.app/submit.py
   python3 submit.py --team mi-equipo --model claude-sonnet-5 --tooling "Claude Agent SDK"
   ```
   Puedes enviar varias veces: cada envío es una fila.

## Las 7 preguntas
| | Pregunta |
|---|---|
| [`q01`](preguntas/q01.md) | ¿Qué línea en los tres meses ha tenido la mejor evolución en rentabilidad y esto a qué se debe? |
| [`q02`](preguntas/q02.md) | ¿Para mejorar la rentabilidad de la línea de Warehouse qué debemos hacer? |
| [`q03`](preguntas/q03.md) | ¿Warehouse va a recuperar su rentabilidad en agosto? |
| [`q04`](preguntas/q04.md) | ¿Cuál fue la facturación real de cada mes? |
| [`q05`](preguntas/q05.md) | ¿Qué parte del gasto de un mes es realmente de ese mes, y qué parte es un ajuste retroactivo de un mes anterior? |
| [`q06`](preguntas/q06.md) | ¿Indícame cuáles fueron las novedades presentadas en el proyecto 594 porque tenemos variación en la rentabilidad entre junio y julio? |
| [`q07`](preguntas/q07.md) | ¿Indícame cuáles fueron las novedades presentadas en el proyecto 600 porque tenemos variación en la rentabilidad entre junio y julio? |

Cada enunciado trae las convenciones obligatorias y el contrato de respuesta (`answer`, `summary`, `method`, `code`, `caveats`, `conventions`). `answer: null` con caveats explícitos vale más que una cifra inventada.

## Cómo se puntúa (resumen)
Por pregunta: cifras vs golden con tolerancia · sustancia según el juez · la traza sostiene la cifra · te auto-verificaste · honestidad. Sin traza, tope 0.5. Ranking principal por **valor** = `calidad × 2 / (2 + coste_usd)`. Detalle en `SUBMIT.md` §4.
