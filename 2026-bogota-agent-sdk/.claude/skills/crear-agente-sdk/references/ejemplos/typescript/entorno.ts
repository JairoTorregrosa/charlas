// entorno.ts — carga la API key desde .env antes de que arranque el SDK.
//
// Busca `.env` en la raíz del kit y en esta carpeta. Con ANTHROPIC_API_KEY el agente corre
// contra tu cuenta de Console (así va en producción). Sin key, el SDK usa la sesión de
// Claude Code de tu máquina.
//
//   import "./entorno.ts";   // primera línea de cada script
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

for (const ruta of [join(import.meta.dirname, "..", ".env"), join(import.meta.dirname, ".env")]) {
  if (!existsSync(ruta)) continue;
  for (const cruda of readFileSync(ruta, "utf8").split("\n")) {
    const linea = cruda.trim();
    if (!linea || linea.startsWith("#") || !linea.includes("=")) continue;
    const i = linea.indexOf("=");
    const clave = linea.slice(0, i).trim();
    const valor = linea.slice(i + 1).trim().replace(/^["']|["']$/g, "");
    if (valor && !process.env[clave]) process.env[clave] = valor;
  }
}

export const CON_KEY = Boolean(process.env.ANTHROPIC_API_KEY);
console.log(`[auth] ${CON_KEY ? "API key de .env (Console)" : "sin API key en .env: uso la sesión de Claude Code"}\n`);
