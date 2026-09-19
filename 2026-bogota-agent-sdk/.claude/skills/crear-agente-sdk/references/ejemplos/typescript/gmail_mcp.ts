// Servidor MCP falso de Gmail: 4 correos en memoria, dos tools.
//
// Va in-process con createSdkMcpServer: las tools corren dentro de este mismo
// proceso de Node, sin lanzar otro programa ni hablar por stdio. Es lo más
// simple que funciona y se ve entero en una pantalla. Un servidor stdio con
// @modelcontextprotocol/sdk haría lo mismo en otro proceso y con más piezas.
import { createSdkMcpServer, tool } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";

type Correo = { id: string; de: string; asunto: string; fecha: string; cuerpo: string };

export const CORREOS: Correo[] = [
  {
    id: "c1",
    de: "promociones@avianca.com",
    asunto: "¡Vuela a Cartagena desde $189.900!",
    fecha: "2026-09-15",
    cuerpo:
      "Promoción de temporada. Tiquetes a Cartagena desde $189.900 comprando antes del 30 de septiembre. Aplican condiciones.",
  },
  {
    id: "c2",
    de: "reservas@wingo.com",
    asunto: "Tu vuelo BOG → CTG",
    fecha: "2026-09-13",
    cuerpo:
      "Vuelo BOG → CTG el domingo 13 de septiembre de 2026 a las 10:40. Reserva WX7Q2. Presenta este correo en el aeropuerto.",
  },
  {
    id: "c3",
    de: "confirmaciones@latam.com",
    asunto: "Confirmación de reserva",
    fecha: "2026-09-16",
    cuerpo:
      "Vuelo BOG → MDE el jueves 24 de septiembre de 2026 a las 06:15. Reserva ABC123. Check-in disponible 48 horas antes.",
  },
  {
    id: "c4",
    de: "noreply@booking.com",
    asunto: "Tu reserva en Medellín",
    fecha: "2026-09-17",
    cuerpo:
      "Hotel en El Poblado, Medellín. Entrada el 24 de septiembre, salida el 26 de septiembre. Reserva BK-88412.",
  },
];

// Quita tildes y baja a minúsculas para que "aerolínea" y "aerolinea" busquen igual.
const normaliza = (t: string) =>
  t.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

const buscar = tool(
  "buscar",
  "Busca correos por palabras en remitente, asunto y cuerpo. Query vacío devuelve todos.",
  {
    query: z.string().describe("Palabras a buscar. Cadena vacía = todos los correos."),
    desde: z.string().describe("Fecha mínima en formato YYYY-MM-DD, por ejemplo 2026-09-12."),
  },
  async ({ query, desde }) => {
    const palabras = normaliza(query).split(/\s+/).filter(Boolean);
    const hallados = CORREOS.filter((c) => c.fecha >= desde).filter(
      (c) =>
        palabras.length === 0 ||
        palabras.some((p) => normaliza(`${c.de} ${c.asunto} ${c.cuerpo}`).includes(p)),
    );
    const texto = hallados.length
      ? hallados.map((c) => `${c.id} | ${c.fecha} | ${c.de} | ${c.asunto}`).join("\n")
      : "Sin resultados. Prueba con query vacío para ver todos los correos.";
    return { content: [{ type: "text" as const, text: texto }] };
  },
);

const leer = tool(
  "leer",
  "Devuelve el correo completo a partir de su id.",
  { id: z.string().describe("Id del correo, por ejemplo c3.") },
  async ({ id }) => {
    const c = CORREOS.find((x) => x.id === id);
    const texto = c
      ? `De: ${c.de}\nFecha: ${c.fecha}\nAsunto: ${c.asunto}\n\n${c.cuerpo}`
      : `No existe el correo ${id}.`;
    return { content: [{ type: "text" as const, text: texto }] };
  },
);

// alwaysLoad: true evita que el agente tenga que llamar ToolSearch antes de usar
// estas tools. En vivo se ve el paso directo a mcp__gmail__buscar.
export const servidorGmail = createSdkMcpServer({
  name: "gmail",
  version: "1.0.0",
  tools: [buscar, leer],
  alwaysLoad: true,
});
