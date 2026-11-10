<!-- ficha:inicio · lo escribe scripts/catalogo.py desde charlas.toml · no lo edites a mano -->
# Crea tu Web con IA

<a href="Crea-tu-Web-con-IA-HAP-Montrose-2026.pdf"><img src="portada.jpg" alt="Portada del deck «Crea tu Web con IA»" width="100%"></a>

<table>
<tr><td>📅 <b>Cuándo</b></td><td>6 de agosto de 2026</td></tr>
<tr><td>📍 <b>Dónde</b></td><td>Espacio Comunitario de HAP · Montrose, Colorado</td></tr>
<tr><td>🎤 <b>Formato</b></td><td>Taller · 90 min</td></tr>
<tr><td>🎟️ <b>Evento</b></td><td><a href="https://hapgj.org/">Hispanic Affairs Project</a></td></tr>
<tr><td>📑 <b>Deck</b></td><td><a href="Crea-tu-Web-con-IA-HAP-Montrose-2026.pdf">16 slides en PDF</a> · <a href="https://github.com/JairoTorregrosa/charlas/raw/main/2026-hapgj/Crea-tu-Web-con-IA-HAP-Montrose-2026.pdf">descargar</a></td></tr>
<tr><td>🛠️ <b>Skill</b></td><td><a href="https://github.com/JairoTorregrosa/crea-tu-web"><code>crea-tu-web</code></a></td></tr>
</table>

<details>
<summary>👀 Las 16 slides de un vistazo</summary>

<a href="Crea-tu-Web-con-IA-HAP-Montrose-2026.pdf"><img src="vistazo.jpg" alt="Las 16 slides del deck en miniatura" width="100%"></a>

</details>

<sub><a href="../README.md">← Todas las charlas</a> · anterior: <a href="../2026-col5-agents/">¿Ya usas ChatGPT? ¿Y si tuvieras un agente?</a> · siguiente: <a href="../2026-agents-bogota/">Construye tu primer agente de AI con Claude</a></sub>
<!-- ficha:fin -->

Tu primera página web con IA, sin escribir código. Taller presencial con el [Hispanic Affairs Project](https://hapgj.org/) en Montrose, Colorado.

## El recorrido de la noche

| # | Paso | Qué haces |
|---|---|---|
| 1 | **Pide tu página** | Pegas el primer prompt en ChatGPT o en Claude. La IA te entrevista, una pregunta a la vez, y te muestra tu página. |
| 2 | **Conecta tu cuenta** | En los ajustes de tu IA conectas GitHub. En [github.com/new](https://github.com/new) creas el repositorio `mi-pagina-web`, con «Add README» activado. |
| 3 | **La IA construye** | Pegas el segundo prompt con los datos de tu negocio. La IA arma la página en español e inglés y deja una propuesta de cambios (un *pull request*). La apruebas en tu repositorio: pestaña «Pull requests», botón verde «Merge pull request», y confirmas. |
| 4 | **Publica** | En [dash.cloudflare.com](https://dash.cloudflare.com/) abres «Workers & Pages», creas un proyecto de «Pages», eliges «Import an existing Git repository», tu `mi-pagina-web` y «Save and Deploy». En 2 o 3 minutos está en internet. |
| 5 | **Directorio en vivo** | Compartes tu enlace. En el taller, cada página entró al directorio de negocios. |

## Los prompts

Cópialos tal cual. Contesta como si le platicaras a un vecino. Si tienes fotos de tu negocio, súbelas al chat.

<details>
<summary><b>Paso 1 en ChatGPT</b></summary>

```text
@Sites Crea la página web de mi negocio. Primero hazme una entrevista corta: pregúntame de a UNA pregunta a la vez el nombre de mi negocio, a qué me dedico, mi teléfono, mi horario, dónde estoy y qué sensación quiero transmitir. Con eso crea una página sencilla y bonita en español, con mi teléfono visible y un botón para contactarme. Muéstramela y, cuando yo te diga, publícala.
```

</details>

<details>
<summary><b>Paso 1 en Claude</b></summary>

```text
Crea la página web de mi negocio en un solo archivo HTML. Primero hazme una entrevista corta: pregúntame de a UNA pregunta a la vez el nombre de mi negocio, a qué me dedico, mi teléfono, mi horario, dónde estoy y qué sensación quiero transmitir. Con eso crea una página sencilla y bonita en español, que se vea bien en el celular, con mi teléfono visible y un botón para contactarme. Muéstramela cuando esté lista.
```

</details>

<details>
<summary><b>Paso 3: tu página profesional</b></summary>

Cambia lo que está entre corchetes por lo tuyo, lo mismo que contestaste en la entrevista.

```text
Crea en mi cuenta de GitHub un repositorio llamado mi-pagina-web (si no existe ya) y construye ahí la página web completa de mi negocio con esta información: [nombre, a qué me dedico, teléfono, horario, ubicación, qué me pregunta la gente, qué sensación quiero transmitir]. La página debe ser bilingüe español e inglés con un botón para cambiar de idioma, español primero, verse perfecta en el celular, y usar estos colores: [tus colores]. No uses fotos de internet: usa ilustraciones sencillas o espacios marcados para mis propias fotos. El sitio debe poderse publicar como sitio estático en Cloudflare Pages: deja las instrucciones de configuración en el README. Cuando termines, crea un pull request (la propuesta de cambios).
```

</details>

<details>
<summary><b>Si la IA te pregunta algo técnico</b></summary>

```text
Elige tú la opción más simple. Es una página estática sencilla.
```

¿Se queda trabajando mucho rato? Escríbele «continúa», una sola vez.

</details>

## Lo que sigue

| Cuándo | Qué |
|---|---|
| Hoy | Manda tu link a 3 personas. |
| Esta semana | Pídele cambios a tu IA. Cada cambio aprobado se publica solo. |
| Este mes | Tu propio dominio. La IA te guía paso a paso. |

## Para seguir en casa: cinco skills

El kit que deja el taller. Cada skill guía a la IA paso a paso. Tú solo respondes preguntas sobre tu negocio.

| # | Skill | Le dices | Qué hace |
|---|---|---|---|
| 1 | `revisa-tu-equipo` | «revisa mi equipo» | Revisa que tu laptop tenga lo necesario y te ayuda a arreglar lo que falte. |
| 2 | `crea-tu-web` | «crea mi página» | Te entrevista sobre tu negocio y crea la página desde cero, bilingüe español e inglés. |
| 3 | `disena-tu-marca` | «diseña mi marca» | Elige colores, tipografía y estilo visual propios, sin plantillas genéricas. |
| 4 | `planea-tu-web` | «planeemos mi página» | Organiza las secciones y el contenido según lo que tu negocio necesita. |
| 5 | `publica-tu-web` | «publica mi página» | La sube a internet con Cloudflare Pages, gratis y sin tarjeta, y genera un QR para compartirla. |

Hay una sexta, `taste-skill`, que la IA consulta sola para que la página no se vea como plantilla.

En Claude Code se instalan con dos comandos:

```
/plugin marketplace add JairoTorregrosa/crea-tu-web
/plugin install crea-tu-web@crea-tu-web
```

Las skills, la instalación para Codex y el flujo completo viven en su propio repo: [JairoTorregrosa/crea-tu-web](https://github.com/JairoTorregrosa/crea-tu-web).

Contacto: [@jai_torregrosa](https://x.com/jai_torregrosa)
