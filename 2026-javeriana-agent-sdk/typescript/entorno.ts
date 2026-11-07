// entorno.ts — deja lista la autenticación antes de que arranque el SDK.
//
// Tres caminos, en este orden de preferencia para el taller:
//   1. ant auth login            (recomendado) usa tu sesión de platform.claude.com y los créditos del taller
//   2. ANTHROPIC_API_KEY         una key de platform.claude.com/settings/keys en .env
//   3. CLAUDE_CODE_OAUTH_TOKEN   tu suscripción Pro/Max (claude setup-token), solo uso personal
// Si hay una key o un token en el entorno, ganan sobre la sesión de ant.
//
//   import "./entorno.ts";   // primera línea de cada script
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
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

function perfilAnt(): string | undefined {
  // Perfil activo de `ant auth login`. Mac/Linux: ~/.config/anthropic · Windows: %APPDATA%\anthropic
  const dirs = [process.env.ANTHROPIC_CONFIG_DIR, join(homedir(), ".config", "anthropic"),
    process.env.APPDATA ? join(process.env.APPDATA, "anthropic") : undefined];
  for (const d of dirs) {
    if (!d) continue;
    const activo = join(d, "active_config");
    const nombre = existsSync(activo) ? readFileSync(activo, "utf8").trim() : "default";
    if (existsSync(join(d, "credentials", `${nombre}.json`))) return nombre;
  }
  return undefined;
}

export const CON_KEY = Boolean(process.env.ANTHROPIC_API_KEY);
const PERFIL = perfilAnt();
// Explícito, para que gane sobre un login de claude.ai (Pro/Max) en Claude Code:
// sin esto, quien tenga Claude Code logueado gasta su plan y no los créditos.
if (!CON_KEY && !process.env.CLAUDE_CODE_OAUTH_TOKEN && PERFIL && !process.env.ANTHROPIC_PROFILE) {
  process.env.ANTHROPIC_PROFILE = PERFIL;
}
const AUTH = CON_KEY
  ? "API key de .env (platform.claude.com)"
  : process.env.CLAUDE_CODE_OAUTH_TOKEN
    ? "token de tu suscripción (claude setup-token)"
    : PERFIL
      ? `sesión de ant, perfil «${process.env.ANTHROPIC_PROFILE}» · créditos de platform.claude.com`
      : "sin key ni sesión de ant: si falla con «Not logged in», corre  ant auth login";
console.log(`[auth] ${AUTH}\n`);
