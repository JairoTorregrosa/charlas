# Agentes en la nube con Claude Managed Agents

Workshop de Claude Community Bogotá en la Universidad de La Salle (Maestría en Analítica e Inteligencia de Negocios), sábado 24 de octubre de 2026.
Ponente: Jairo Torregrosa.

Cómo pasar un caso de uso que ya corre en Claude Code, en el portátil, a un agente remoto que no depende de nadie ni de un PC prendido: Agent, Environment, Session, eventos y Deployment.

**Slides (PDF, 30 páginas):** [descargar](https://github.com/JairoTorregrosa/charlas/raw/main/2026-lasalle-managed-agents/Agentes-en-la-nube-Claude-Managed-Agents-LaSalle-2026.pdf)

## Construye tu propio agente

Lo único que hace falta es la skill `managed-agents-wizard` en Claude Code:

```
npx skills add JairoTorregrosa/jaiskills --skill managed-agents-wizard -g
claude
> /managed-agents-wizard
```

La skill parte de una idea, propone Agent, Environment, credenciales y forma de arranque, aplica con el CLI `ant` y corre una Session de prueba con budget. Las trazas se ven en [platform.claude.com](https://platform.claude.com) › Sessions.

## Comunidad

Claude Colombia: [claudecolombia.com](https://claudecolombia.com) · [comunidad de WhatsApp](https://chat.whatsapp.com/BVelw8cvSMEFKq9wjkY2a9)
