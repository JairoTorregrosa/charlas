"""Los mismos cuatro correos del taller, para pasárselos al agente en el mensaje.

Managed Agents se conecta a servidores MCP **remotos**, por URL. El `gmail_mcp.py`
de `python/` es un proceso local por stdio, así que aquí no sirve: la bandeja
viaja dentro del mensaje.
"""

CORREOS = """c1 · Avianca · ¡Vuela a Cartagena desde $189.900! · 2026-09-15
     Promoción válida hasta agotar existencias. Compra en avianca.com.
c2 · Wingo · Tu vuelo BOG → CTG · 2026-09-13
     Vuelo BOG → CTG el domingo 13 de septiembre de 2026 a las 10:40. Reserva WX7Q2.
c3 · LATAM · Confirmación de reserva · 2026-09-16
     Tu vuelo BOG → MDE sale el jueves 24 de septiembre de 2026 a las 06:15. Reserva ABC123.
c4 · Booking.com · Tu reserva en Medellín · 2026-09-17
     Hotel en El Poblado, del 24 al 26 de septiembre de 2026. Reserva BK-88412."""

MENSAJE = f"""Hoy es sábado 19 de septiembre de 2026. Esta es mi bandeja de correo:

{CORREOS}

Revisa mis correos de la última semana y dime cuándo es mi próximo vuelo."""
