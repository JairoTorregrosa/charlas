"""gmail_mcp.py — un servidor MCP de mentiras con la bandeja de correo.

Corre como proceso aparte por stdio, igual que un MCP de verdad. Dos tools:
buscar(query, desde) y leer(id). Cuatro correos y tres trampas: una promoción,
un vuelo que ya pasó y una reserva de hotel que no es un vuelo.

Se arranca solo: lo lanza el SDK. Para probarlo a mano:
    uv run python gmail_mcp.py     (se queda esperando JSON-RPC por stdin)
"""

from mcp.server.mcpserver import MCPServer

CORREOS = {
    "c1": {"de": "Avianca", "asunto": "¡Vuela a Cartagena desde $189.900!", "fecha": "2026-09-15",
           "cuerpo": "Promoción válida hasta agotar existencias. Compra en avianca.com."},
    "c2": {"de": "Wingo", "asunto": "Tu vuelo BOG → CTG", "fecha": "2026-09-13",
           "cuerpo": "Vuelo BOG → CTG el domingo 13 de septiembre de 2026 a las 10:40. Reserva WX7Q2."},
    "c3": {"de": "LATAM", "asunto": "Confirmación de reserva", "fecha": "2026-09-16",
           "cuerpo": "Tu vuelo BOG → MDE sale el jueves 24 de septiembre de 2026 a las 06:15. Reserva ABC123."},
    "c4": {"de": "Booking.com", "asunto": "Tu reserva en Medellín", "fecha": "2026-09-17",
           "cuerpo": "Hotel en El Poblado, del 24 al 26 de septiembre de 2026. Reserva BK-88412."},
}

mcp = MCPServer("gmail")


@mcp.tool()
def buscar(query: str, desde: str) -> str:
    """Busca correos recibidos desde una fecha (AAAA-MM-DD). Devuelve id, remitente, asunto y fecha."""
    filas = [f"{i} · {c['de']} · {c['asunto']} · {c['fecha']}"
             for i, c in CORREOS.items() if c["fecha"] >= desde]
    return "\n".join(filas) or "Sin correos."


@mcp.tool()
def leer(id: str) -> str:
    """Devuelve el correo completo con ese id."""
    c = CORREOS.get(id)
    if not c:
        raise ValueError(f"No existe el correo {id}")
    return f"De: {c['de']}\nAsunto: {c['asunto']}\nFecha: {c['fecha']}\n\n{c['cuerpo']}"


if __name__ == "__main__":
    mcp.run()
