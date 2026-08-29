---
name: roast-de-codigo
description: Criterio y formato para un roast de código. Úsalo cuando te pidan "roast", "roastea" o "qué tan malo es este repo".
---

# Roast de código

Un roast es una crítica con humor. Se ríe del código, no de quien lo escribió.
El lector es el dueño del repo: quiere reírse y salir sabiendo qué arreglar primero.

## Qué cuenta como pecado

- Un crash esperando pasar: `unwrap()`, `panic!`, `except: pass`.
- Una mentira: README que no coincide con el código, comentario viejo.
- Una deuda: TODO de hace años, función de 200 líneas.
- Escoge los 3 archivos con más de eso. Ignora archivos generados y lockfiles.

## Formato de `roast.md`

```
# Roast de <usuario/repo>
Nivel de vergüenza global: N/10

## <ruta del archivo> — N/10
1. L<n> `<línea citada>` — <por qué duele, una frase>. <el chiste, una frase>.
2. ...
3. ...
A regañadientes: <una cosa que sí está bien>.
```

- Tres archivos, tres pecados cada uno.
- Cierra con una línea: qué arreglar primero.

## Ejemplos

- Bien: L142 `let cfg = load().unwrap();` — si falta la config, el programa muere sin decir por qué. Un paracaídas que dice "confía".
- Mal: "Este código es horrible y quien lo hizo debería dedicarse a otra cosa." — ataca a la persona y no cita ninguna línea.

## Si falta algo

- Si el repo no tiene archivos de código, escribe un `roast.md` de una línea diciéndolo y para.
