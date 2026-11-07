// credenciales.ts — elige UNA forma de autenticar y apaga las demás.
//
// Generado por la skill agent-sdk-wizard. No lo edites: cambia .env.
//
// Por qué existe: Claude Code (que el SDK lleva adentro) acepta varias
// credenciales a la vez y gana la de mayor prioridad, en silencio:
//     ANTHROPIC_API_KEY  >  CLAUDE_CODE_OAUTH_TOKEN  >  ANTHROPIC_PROFILE  >  tu login de claude.ai
// Si dejas eso al azar, el agente puede gastar tu plan Pro/Max en vez de los
// créditos. Aquí .env dice cuál se usa (AGENTE_AUTH) y las otras se borran
// del proceso del agente. Si falta algo, el agente NO arranca.

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const MODOS = {
  ant: "ANTHROPIC_PROFILE",               // A · login con `ant auth login` (créditos de la org)
  api_key: "ANTHROPIC_API_KEY",           // B · API key de platform.claude.com
  suscripcion: "CLAUDE_CODE_OAUTH_TOKEN", // C · tu plan Pro/Max (`claude setup-token`)
} as const;
type Modo = keyof typeof MODOS;

function leerEnv(ruta: string): Record<string, string> {
  const valores: Record<string, string> = {};
  if (!existsSync(ruta)) return valores;
  for (const cruda of readFileSync(ruta, "utf8").split(/\r?\n/)) {
    const linea = cruda.trim();
    if (!linea || linea.startsWith("#") || !linea.includes("=")) continue;
    const i = linea.indexOf("=");
    valores[linea.slice(0, i).trim()] = linea.slice(i + 1).trim().replace(/^["']|["']$/g, "");
  }
  return valores;
}

function carpetasDeAnt(env: Record<string, string>): string[] {
  // Dónde guarda `ant` sus perfiles. La primera que exista gana.
  // Si .env (o tu shell) nombra una carpeta, SOLO esa cuenta: buscar en otra
  // podría usar otra cuenta con el mismo nombre de perfil.
  const explicita = env.ANTHROPIC_CONFIG_DIR || process.env.ANTHROPIC_CONFIG_DIR;
  if (explicita) return [explicita];
  const c: (string | undefined)[] = [];
  if (process.env.XDG_CONFIG_HOME) c.push(join(process.env.XDG_CONFIG_HOME, "anthropic"));
  c.push(join(homedir(), ".config", "anthropic"));
  if (process.env.APPDATA) c.push(join(process.env.APPDATA, "anthropic")); // Windows
  return c.filter((x): x is string => Boolean(x));
}

function parar(mensaje: string): never {
  console.error(`[auth] ${mensaje}`);
  process.exit(1);
}

/** Deja en el entorno UNA credencial y devuelve el modo. Nunca imprime secretos. */
export function prepararCredenciales(): Modo {
  const aqui = dirname(fileURLToPath(import.meta.url));
  const env = leerEnv(join(aqui, ".env"));
  // Todo sale de .env, nada de tu shell: así no se cuela otra cuenta.
  const modo = (env.AGENTE_AUTH ?? "") as Modo;
  if (!(modo in MODOS)) {
    parar("Falta AGENTE_AUTH en .env (ant | api_key | suscripcion). " +
          "Copia .env.example a .env y llénalo, o corre otra vez el paso 0 del wizard.");
  }

  const variable = MODOS[modo];
  const valor = env[variable] ?? "";
  if (!valor) parar(`AGENTE_AUTH=${modo} pero falta ${variable} en .env.`);

  for (const otra of Object.values(MODOS)) if (otra !== variable) delete process.env[otra];
  process.env[variable] = valor;

  if (modo === "ant") {
    // Un perfil que no existe se ignora EN SILENCIO y paga tu login de claude.ai.
    for (const carpeta of carpetasDeAnt(env)) {
      const archivo = join(carpeta, "credentials", `${valor}.json`);
      if (existsSync(archivo)) {
        const datos = JSON.parse(readFileSync(archivo, "utf8")) as { expires_at?: number; refresh_token?: string };
        // Vencido y sin refresh_token = no se puede renovar: cada llamada fallaría.
        const vencido = typeof datos.expires_at === "number" && datos.expires_at * 1000 < Date.now();
        if (vencido && !datos.refresh_token) {
          parar(`El perfil «${valor}» de ant tiene la sesión vencida y no se puede renovar. ` +
                `Corre \`ant auth login --profile ${valor}\` (o usa otro perfil de \`ant profile list\`).`);
        }
        process.env.ANTHROPIC_CONFIG_DIR = carpeta;
        console.log(`[auth] ant · perfil «${valor}» (paga la organización de ese login)`);
        return modo;
      }
    }
    parar(`No encuentro el perfil «${valor}» de ant. Corre \`ant auth login\` y luego ` +
          "`ant auth status`: copia el nombre del perfil a ANTHROPIC_PROFILE en .env " +
          "(y su «Config dir» a ANTHROPIC_CONFIG_DIR si no es ~/.config/anthropic).");
  }
  console.log(modo === "api_key"
    ? "[auth] API key de .env (paga la organización dueña de la key)"
    : "[auth] suscripción Pro/Max (cuenta contra los límites de tu plan, no usa créditos)");
  return modo;
}
