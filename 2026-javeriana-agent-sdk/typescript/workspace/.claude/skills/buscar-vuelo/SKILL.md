---
name: buscar-vuelo
description: Encuentra el próximo vuelo del usuario a partir de sus correos. Úsala cuando pregunten por su próximo vuelo, por su itinerario, por una reserva de avión o por cuándo viajan.
---

# Buscar el próximo vuelo en el correo

Sigue estos cinco pasos en orden.

1. **Pide la fecha de hoy.** Llama a la tool `hoy`. No la deduzcas ni la calcules por tu cuenta.
2. **Busca los correos de la última semana.** Llama a `buscar` con `desde` igual a la fecha de hoy menos 7 días, en formato `YYYY-MM-DD`. Si una búsqueda con palabras no devuelve nada, repítela con `query` vacío.
3. **Ignora lo que no es un vuelo confirmado.** Descarta promociones, ofertas, encuestas de satisfacción y reservas de hotel. Un asunto con precios o con "¡Vuela a…!" es publicidad.
4. **Lee el correo completo.** Llama a `leer` con el id de cada candidato. La fecha, la hora y el código de reserva están en el cuerpo, no en el asunto.
5. **Responde el vuelo futuro más cercano.** Compara cada fecha de vuelo con la fecha de hoy y descarta los que ya pasaron. Di en una o dos líneas: ruta, día, hora y código de reserva. Si no hay ninguno futuro, dilo.
