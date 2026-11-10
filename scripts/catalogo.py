# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdfium2>=4.30", "pillow>=10"]
# ///
"""El catálogo de charlas sale de un solo archivo, charlas.toml.

  uv run scripts/catalogo.py             escribe el índice, la ficha de cada kit y las imágenes que falten
  uv run scripts/catalogo.py --check     no escribe nada; falla si algo quedó a medias (lo corre CI)
  uv run scripts/catalogo.py --imagenes  vuelve a renderizar todas las portadas y vistazos
  uv run scripts/catalogo.py --enlaces   pide cada URL del catálogo y lista las que no responden
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import posixpath
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pypdfium2
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
MANIFIESTO = RAIZ / "charlas.toml"
INDICE = RAIZ / "README.md"
ES_KIT = re.compile(r"^\d{4}-")
COMANDO = "uv run scripts/catalogo.py"
# Varios sitios responden 403 a todo lo que no parezca un navegador.
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

ANCHO_PORTADA = 1200
COLUMNAS_VISTAZO, ANCHO_MINIATURA, MARGEN = 6, 300, 6
FONDO_VISTAZO = (250, 247, 240)
# Cambia cuando cambie la forma de renderizar: invalida las imágenes ya guardadas.
RECETA = "v1"

CAMPOS = {"kit", "titulo", "gancho", "fecha", "formato", "evento", "evento_url",
          "lugar", "ciudad", "deck", "portada", "demo", "skills"}


class Problemas(list):
    """Lo que está mal y cómo se arregla. Se juntan todos antes de fallar."""

    def salir_si_hay(self) -> None:
        if self:
            print(f"\n{len(self)} problema(s) en el catálogo:\n", file=sys.stderr)
            for p in self:
                print(f"  ✗ {p}", file=sys.stderr)
            sys.exit(1)


@dataclass(frozen=True)
class Fecha:
    anio: int
    mes: int
    dia: int | None  # None cuando solo consta el mes

    @classmethod
    def leer(cls, texto: str) -> Fecha:
        m = re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", texto)
        if not m or not 1 <= int(m[2]) <= 12 or (m[3] and not 1 <= int(m[3]) <= 31):
            raise ValueError(f'fecha "{texto}": se espera "AAAA-MM-DD" o "AAAA-MM"')
        return cls(int(m[1]), int(m[2]), int(m[3]) if m[3] else None)

    @property
    def orden(self) -> tuple[int, int, int]:
        return (self.anio, self.mes, self.dia or 0)

    @property
    def larga(self) -> str:
        mes = MESES[self.mes - 1]
        return f"{self.dia} de {mes} de {self.anio}" if self.dia else f"{mes.capitalize()} de {self.anio}"

    @property
    def corta(self) -> str:
        mes = MESES[self.mes - 1][:3]
        return f"{self.dia} {mes} {self.anio}" if self.dia else f"{mes} {self.anio}"


@dataclass(frozen=True)
class Enlace:
    """Algo para abrir: vive en el kit (ruta) o fuera del repo (url)."""

    nombre: str
    destino: str
    externo: bool

    @classmethod
    def leer(cls, dato: dict, donde: str, extra: frozenset[str] = frozenset()) -> Enlace:
        claves = set(dato)
        if "nombre" not in claves or len(claves & {"ruta", "url"}) != 1 or claves - {"nombre", "ruta", "url"} - extra:
            raise ValueError(f"{donde}: cada entrada lleva nombre y una sola de ruta o url")
        externo = "url" in dato
        destino = dato["url"] if externo else dato["ruta"]
        if externo and not destino.startswith("https://"):
            raise ValueError(f"{donde}: la url debe empezar por https://")
        return cls(dato["nombre"], destino, externo)

    def desde(self, base: str) -> str:
        """El href visto desde la raíz (base='kit/') o desde el propio kit (base='')."""
        return self.destino if self.externo else urllib.parse.quote(posixpath.normpath(f"{base}{self.destino}"))


@dataclass(frozen=True)
class Skill:
    enlace: Enlace
    que: str
    usar: str


@dataclass(frozen=True)
class Charla:
    kit: str
    titulo: str
    gancho: str
    fecha: Fecha
    formato: str
    evento: str
    evento_url: str
    lugar: str
    ciudad: str
    deck: str
    portada: int
    demo: tuple[Enlace, ...]
    skills: tuple[Skill, ...]

    @property
    def carpeta(self) -> Path:
        return RAIZ / self.kit

    @property
    def pdf(self) -> Path:
        return self.carpeta / self.deck

    @property
    def donde(self) -> str:
        return self.lugar if self.ciudad in self.lugar else f"{self.lugar} · {self.ciudad}"

    @property
    def fuente_evento(self) -> str:
        return "Luma" if urllib.parse.urlparse(self.evento_url).hostname == "luma.com" else "Evento"


@dataclass(frozen=True)
class Catalogo:
    repo: str
    rama: str
    ciudades: dict[str, dict]
    charlas: tuple[Charla, ...]  # de la más antigua a la más reciente
    declarados: frozenset[str]  # los kits que nombra el manifiesto, también los que no se pudieron leer

    def descarga(self, c: Charla) -> str:
        return f"https://github.com/{self.repo}/raw/{self.rama}/{c.kit}/{urllib.parse.quote(c.deck)}"


def leer_catalogo(problemas: Problemas) -> Catalogo:
    datos = tomllib.loads(MANIFIESTO.read_text(encoding="utf-8"))
    ciudades = datos.get("ciudades", {})
    charlas = []
    for i, d in enumerate(datos.get("charla", []), 1):
        donde = f'charlas.toml, charla {i} ({d.get("kit", "sin kit")})'
        if faltan := CAMPOS - set(d):
            problemas.append(f"{donde}: faltan {sorted(faltan)}. Una lista vacía se escribe [], no se omite.")
            continue
        if sobran := set(d) - CAMPOS:
            problemas.append(f"{donde}: campos que nadie lee {sorted(sobran)}.")
            continue
        try:
            charlas.append(Charla(
                kit=d["kit"], titulo=d["titulo"], gancho=d["gancho"], fecha=Fecha.leer(d["fecha"]),
                formato=d["formato"], evento=d["evento"], evento_url=d["evento_url"],
                lugar=d["lugar"], ciudad=d["ciudad"], deck=d["deck"], portada=d["portada"],
                demo=tuple(Enlace.leer(e, f"{donde}, demo") for e in d["demo"]),
                skills=tuple(
                    Skill(Enlace.leer(s, f"{donde}, skills", frozenset({"que", "usar"})), s["que"], s["usar"])
                    for s in d["skills"]
                ),
            ))
        except (ValueError, KeyError) as e:
            problemas.append(f"{donde}: {e}")
    charlas.sort(key=lambda c: (c.fecha.orden, c.kit))
    declarados = frozenset(d["kit"] for d in datos.get("charla", []) if "kit" in d)
    return Catalogo(datos.get("repo", ""), datos.get("rama", ""), ciudades, tuple(charlas), declarados)


def revisar_datos(cat: Catalogo, problemas: Problemas) -> None:
    """Lo que se puede saber sin abrir un PDF ni generar nada."""
    if not cat.repo or not cat.rama:
        problemas.append("charlas.toml: faltan repo y rama, con los que se arma el enlace de descarga.")
    en_disco = {p.name for p in RAIZ.iterdir() if p.is_dir() and ES_KIT.match(p.name)}
    en_toml = [c.kit for c in cat.charlas]
    for kit in sorted(en_disco - cat.declarados):
        problemas.append(f"{kit}/ existe pero no está en charlas.toml: añade su [[charla]] y corre `{COMANDO}`.")
    for kit in sorted({k for k in en_toml if en_toml.count(k) > 1}):
        problemas.append(f"{kit} aparece más de una vez en charlas.toml.")
    for c in cat.charlas:
        if c.kit not in en_disco:
            problemas.append(f"{c.kit}: está en charlas.toml pero no hay carpeta con ese nombre.")
            continue
        if not c.kit.startswith(f"{c.fecha.anio}-"):
            problemas.append(f"{c.kit}: la carpeta empieza por otro año que su fecha ({c.fecha.anio}).")
        if c.ciudad not in cat.ciudades:
            problemas.append(f'{c.kit}: la ciudad "{c.ciudad}" no está en [ciudades] (hace falta para el mapa).')
        if not c.evento_url.startswith("https://"):
            problemas.append(f"{c.kit}: evento_url debe ser una URL https (Luma, sitio oficial o nota de prensa).")
        if not c.pdf.is_file():
            problemas.append(f"{c.kit}: no está el deck {c.deck}.")
        if not c.demo and not c.skills:
            problemas.append(f"{c.kit}: ni demo ni skill. Toda charla deja algo para practicar; enlázalo aunque viva fuera.")
        for e in (*c.demo, *(s.enlace for s in c.skills)):
            if not e.externo and not (c.carpeta / e.destino).exists():
                problemas.append(f"{c.kit}: la ruta {e.destino} no existe.")
        for s in c.skills:
            if s.enlace.externo:
                continue
            skill_md = c.carpeta / s.enlace.destino / "SKILL.md"
            nombre = re.search(r"^name:\s*(\S+)", skill_md.read_text(encoding="utf-8"), re.M) if skill_md.is_file() else None
            if not nombre or nombre[1] != s.enlace.nombre:
                problemas.append(f"{c.kit}: {s.enlace.destino}/SKILL.md debe existir y declarar name: {s.enlace.nombre}.")


# ---------- imágenes ----------

def sello(pdf: Path, detalle: str) -> str:
    """Identifica de qué deck y con qué receta salió una imagen; va en el comentario del JPEG."""
    return f"{RECETA}:{hashlib.sha256(pdf.read_bytes()).hexdigest()[:16]}:{detalle}"


def sello_guardado(imagen: Path) -> str | None:
    if not imagen.is_file():
        return None
    with Image.open(imagen) as im:
        comentario = im.info.get("comment", b"")
    return comentario.decode("utf-8", "replace") if isinstance(comentario, bytes) else str(comentario)


def pagina(doc: pypdfium2.PdfDocument, numero: int, ancho: int) -> Image.Image:
    p = doc[numero - 1]
    return p.render(scale=ancho / p.get_width()).to_pil().convert("RGB")


def guardar(im: Image.Image, destino: Path, marca: str, calidad: int) -> None:
    im.save(destino, "JPEG", quality=calidad, optimize=True, progressive=True, comment=marca.encode())


def imagenes(c: Charla, doc: pypdfium2.PdfDocument, forzar: bool, escribir: bool, problemas: Problemas) -> None:
    if not 1 <= c.portada <= len(doc):
        problemas.append(f"{c.kit}: portada = {c.portada}, pero el deck tiene {len(doc)} páginas.")
        return
    pendientes = {
        "portada.jpg": sello(c.pdf, f"portada={c.portada}"),
        "vistazo.jpg": sello(c.pdf, f"vistazo={COLUMNAS_VISTAZO}x{ANCHO_MINIATURA}"),
    }
    for nombre, marca in pendientes.items():
        destino = c.carpeta / nombre
        if not forzar and sello_guardado(destino) == marca:
            continue
        if not escribir:
            problemas.append(f"{c.kit}/{nombre} falta o no corresponde al deck actual: corre `{COMANDO}`.")
            continue
        if nombre == "portada.jpg":
            guardar(pagina(doc, c.portada, ANCHO_PORTADA), destino, marca, 84)
        else:
            guardar(vistazo(doc), destino, marca, 78)
        print(f"  imagen  {c.kit}/{nombre}")


def vistazo(doc: pypdfium2.PdfDocument) -> Image.Image:
    """Todas las slides en una sola hoja de contactos."""
    minis = [pagina(doc, n, ANCHO_MINIATURA) for n in range(1, len(doc) + 1)]
    alto = max(m.height for m in minis)
    filas = -(-len(minis) // COLUMNAS_VISTAZO)
    hoja = Image.new("RGB", (
        COLUMNAS_VISTAZO * ANCHO_MINIATURA + (COLUMNAS_VISTAZO + 1) * MARGEN,
        filas * alto + (filas + 1) * MARGEN,
    ), FONDO_VISTAZO)
    for i, m in enumerate(minis):
        x = MARGEN + (i % COLUMNAS_VISTAZO) * (ANCHO_MINIATURA + MARGEN)
        y = MARGEN + (i // COLUMNAS_VISTAZO) * (alto + MARGEN)
        hoja.paste(m, (x, y))
    return hoja


# ---------- texto generado ----------

def esc(texto: str) -> str:
    return html.escape(texto, quote=True)


def lista_demo(c: Charla, base: str) -> str:
    return " · ".join(f'<a href="{esc(d.desde(base))}">{esc(d.nombre)}</a>' for d in c.demo)


def lista_skills(c: Charla, base: str) -> str:
    return " · ".join(f'<a href="{esc(s.enlace.desde(base))}"><code>{esc(s.enlace.nombre)}</code></a>' for s in c.skills)


def tarjeta(c: Charla) -> str:
    kit = f"{c.kit}/"
    accesos = [f'<a href="{kit}{urllib.parse.quote(c.deck)}">📑 Deck</a>']
    if c.demo:
        accesos.append(f'<a href="{esc(c.demo[0].desde(kit))}">🧪 Demo</a>')
    if c.skills:
        accesos.append(f'<a href="{esc(c.skills[0].enlace.desde(kit))}">🛠️ Skill</a>')
    accesos.append(f'<a href="{esc(c.evento_url)}">🎟️ {c.fuente_evento}</a>')
    return "\n".join([
        '<td width="50%" valign="top">',
        f'<a href="{kit}"><img src="{kit}portada.jpg" alt="Portada de «{esc(c.titulo)}»" width="100%"></a><br>',
        f'<b><a href="{kit}">{esc(c.titulo)}</a></b><br>',
        f"<sub>{c.fecha.corta} · {esc(c.donde)} · {esc(c.formato)}</sub><br>",
        f"{esc(c.gancho)}<br>",
        " · ".join(accesos),
        "</td>",
    ])


def mapa(cat: Catalogo) -> str:
    puntos = []
    for ciudad, dato in cat.ciudades.items():
        aqui = [c for c in cat.charlas if c.ciudad == ciudad]
        if not aqui:
            continue
        puntos.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [dato["lon"], dato["lat"]]},
            "properties": {
                "ciudad": f'{ciudad}, {dato["pais"]}',
                "charlas": len(aqui),
                **{c.fecha.corta: c.titulo for c in aqui},
            },
        })
    return json.dumps({"type": "FeatureCollection", "features": puntos}, ensure_ascii=False, indent=1)


def indice(cat: Catalogo, paginas: dict[str, int]) -> str:
    recientes = list(reversed(cat.charlas))
    filas_tarjetas = []
    for i in range(0, len(recientes), 2):
        par = [tarjeta(c) for c in recientes[i:i + 2]]
        if len(par) == 1:
            par.append('<td width="50%"></td>')
        filas_tarjetas.append("<tr>\n" + "\n".join(par) + "\n</tr>")

    bitacora = ["| # | Cuándo | Charla | Evento | Dónde | Formato |", "|--:|---|---|---|---|---|"]
    for n, c in enumerate(cat.charlas, 1):
        bitacora.append(
            f"| {n} | {c.fecha.corta} | [{c.titulo}]({c.kit}/) | [{c.evento}]({c.evento_url}) | {c.donde} | {c.formato} |"
        )

    skills = ["| Skill | Qué hace | De la charla | Cómo se usa |", "|---|---|---|---|"]
    for c in recientes:
        for s in c.skills:
            usar = f"`{s.usar}`" + ("" if s.enlace.externo else f" con Claude Code abierto en [`{c.kit}/`]({c.kit}/)")
            skills.append(f"| [`{s.enlace.nombre}`]({s.enlace.desde(c.kit + '/')}) | {s.que} | [{c.fecha.corta}]({c.kit}/) | {usar} |")

    n_skills = sum(len(c.skills) for c in cat.charlas)
    resumen = (
        f"<b>{len(cat.charlas)}</b> charlas · <b>{sum(paginas.values())}</b> slides · "
        f"<b>{len({c.ciudad for c in cat.charlas})}</b> ciudades · <b>{n_skills}</b> skills"
    )
    return "\n".join([
        f'<p align="center">{resumen}</p>',
        "",
        "## Constelaciones",
        "",
        "<table>",
        *filas_tarjetas,
        "</table>",
        "",
        "## Bitácora",
        "",
        *bitacora,
        "",
        "## Mapa",
        "",
        "```geojson",
        mapa(cat),
        "```",
        "",
        "## Skills",
        "",
        *skills,
    ])


def ficha(cat: Catalogo, c: Charla, paginas: int) -> str:
    i = cat.charlas.index(c)
    deck = urllib.parse.quote(c.deck)
    filas = [
        ("📅", "Cuándo", esc(c.fecha.larga)),
        ("📍", "Dónde", esc(c.donde)),
        ("🎤", "Formato", esc(c.formato)),
        ("🎟️", "Evento", f'<a href="{esc(c.evento_url)}">{esc(c.evento)}</a>' + (" · Luma" if c.fuente_evento == "Luma" else "")),
        ("📑", "Deck", f'<a href="{deck}">{paginas} slides en PDF</a> · <a href="{cat.descarga(c)}">descargar</a>'),
    ]
    if c.demo:
        filas.append(("🧪", "Demo", lista_demo(c, "")))
    if c.skills:
        filas.append(("🛠️", "Skill", lista_skills(c, "")))
    pasos = ['<a href="../README.md">← Todas las charlas</a>']
    if i > 0:
        pasos.append(f'anterior: <a href="../{cat.charlas[i - 1].kit}/">{esc(cat.charlas[i - 1].titulo)}</a>')
    if i < len(cat.charlas) - 1:
        pasos.append(f'siguiente: <a href="../{cat.charlas[i + 1].kit}/">{esc(cat.charlas[i + 1].titulo)}</a>')
    return "\n".join([
        f"# {c.titulo}",
        "",
        f'<a href="{deck}"><img src="portada.jpg" alt="Portada del deck «{esc(c.titulo)}»" width="100%"></a>',
        "",
        "<table>",
        *(f"<tr><td>{icono} <b>{nombre}</b></td><td>{valor}</td></tr>" for icono, nombre, valor in filas),
        "</table>",
        "",
        "<details>",
        f"<summary>👀 Las {paginas} slides de un vistazo</summary>",
        "",
        f'<a href="{deck}"><img src="vistazo.jpg" alt="Las {paginas} slides del deck en miniatura" width="100%"></a>',
        "",
        "</details>",
        "",
        "<sub>" + " · ".join(pasos) + "</sub>",
    ])


def con_bloque(texto: str, nombre: str, contenido: str) -> str | None:
    """El texto con el bloque <!-- nombre:inicio --> … <!-- nombre:fin --> reemplazado; None si no lo tiene."""
    patron = re.compile(rf"(<!-- {nombre}:inicio[^>]*-->\n)(?:.*?\n)?(<!-- {nombre}:fin -->)", re.S)
    if not patron.search(texto):
        return None
    return patron.sub(lambda m: f"{m[1]}{contenido}\n{m[2]}", texto, count=1)


def bloque_nuevo(nombre: str, contenido: str) -> str:
    return f"<!-- {nombre}:inicio · lo escribe scripts/catalogo.py desde charlas.toml · no lo edites a mano -->\n{contenido}\n<!-- {nombre}:fin -->\n"


def poner(archivo: Path, nuevo: str, escribir: bool, problemas: Problemas) -> None:
    actual = archivo.read_text(encoding="utf-8") if archivo.is_file() else None
    if actual == nuevo:
        return
    relativo = archivo.relative_to(RAIZ)
    if escribir:
        archivo.write_text(nuevo, encoding="utf-8")
        print(f"  texto   {relativo}")
    else:
        problemas.append(f"{relativo} no coincide con charlas.toml: corre `{COMANDO}` y sube el resultado.")


def enlaces_rotos(archivo: Path, problemas: Problemas) -> None:
    """Los enlaces relativos de un README tienen que apuntar a algo que exista."""
    if not archivo.is_file():
        return
    texto = re.sub(r"```.*?```", "", archivo.read_text(encoding="utf-8"), flags=re.S)
    destinos = re.findall(r"\]\(([^)\s]+)\)", texto) + re.findall(r'(?:href|src)="([^"]+)"', texto)
    for destino in sorted(set(destinos)):
        if re.match(r"[a-z][a-z0-9+.-]*:|#", destino):
            continue
        ruta = urllib.parse.unquote(destino.split("#")[0])
        if not (archivo.parent / ruta).exists():
            problemas.append(f"{archivo.relative_to(RAIZ)}: el enlace {destino} no lleva a ningún lado.")


def urls_del_catalogo(cat: Catalogo) -> dict[str, set[str]]:
    """Cada URL externa y dónde aparece: el manifiesto, el índice y el README de cada kit."""
    urls: dict[str, set[str]] = {}
    for c in cat.charlas:
        for u in (c.evento_url, *(x.destino for x in (*c.demo, *(s.enlace for s in c.skills)) if x.externo)):
            urls.setdefault(u, set()).add("charlas.toml")
    for archivo in (INDICE, *(c.carpeta / "README.md" for c in cat.charlas)):
        if archivo.is_file():
            for u in re.findall(r"https://[^\s<>\")\]`]+", archivo.read_text(encoding="utf-8")):
                urls.setdefault(u.rstrip(".,;:»"), set()).add(str(archivo.relative_to(RAIZ)))
    return urls


def probar_enlaces(cat: Catalogo) -> int:
    """200 responde; 401 y 403 existen pero piden login o rechazan scripts; lo demás está caído."""
    caidas = 0
    for url, sitios in sorted(urls_del_catalogo(cat).items()):
        peticion = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR})
        try:
            with urllib.request.urlopen(peticion, timeout=25) as r:
                estado = str(r.status)
        except urllib.error.HTTPError as err:
            estado = str(err.code)
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            estado = f"sin respuesta ({err})"
        marca = {"200": "✓", "401": "🔒", "403": "🔒"}.get(estado, "✗")
        caidas += marca == "✗"
        print(f'  {marca} {estado:>4}  {url}   [{", ".join(sorted(sitios))}]')
    print(f"\n{caidas} URL caída(s)." if caidas else "\nNinguna URL caída. 🔒 = pide login o rechaza scripts; ábrela a mano si dudas.")
    return 1 if caidas else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--check", action="store_true", help="no escribe; falla si algo está desactualizado")
    modo.add_argument("--imagenes", action="store_true", help="vuelve a renderizar todas las imágenes")
    modo.add_argument("--enlaces", action="store_true", help="pide cada URL externa del catálogo")
    args = parser.parse_args()
    escribir = not args.check

    problemas = Problemas()
    cat = leer_catalogo(problemas)
    revisar_datos(cat, problemas)
    problemas.salir_si_hay()

    if args.enlaces:
        sys.exit(probar_enlaces(cat))

    paginas: dict[str, int] = {}
    for c in cat.charlas:
        doc = pypdfium2.PdfDocument(c.pdf)
        paginas[c.kit] = len(doc)
        imagenes(c, doc, args.imagenes, escribir, problemas)
        doc.close()
    problemas.salir_si_hay()

    raiz = INDICE.read_text(encoding="utf-8")
    nueva_raiz = con_bloque(raiz, "indice", indice(cat, paginas))
    if nueva_raiz is None:
        problemas.append("README.md no tiene el bloque <!-- indice:inicio --> … <!-- indice:fin -->.")
    else:
        poner(INDICE, nueva_raiz, escribir, problemas)

    for c in cat.charlas:
        readme = c.carpeta / "README.md"
        contenido = ficha(cat, c, paginas[c.kit])
        actual = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        poner(readme, con_bloque(actual, "ficha", contenido) or bloque_nuevo("ficha", contenido) + ("\n" + actual if actual else ""), escribir, problemas)

    for archivo in (INDICE, *(c.carpeta / "README.md" for c in cat.charlas)):
        enlaces_rotos(archivo, problemas)
    problemas.salir_si_hay()
    print(f"Catálogo al día: {len(cat.charlas)} charlas, {sum(paginas.values())} slides.")


if __name__ == "__main__":
    main()
