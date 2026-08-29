# Hook de LiteLLM. El backend de ChatGPT rechaza cualquier mensaje con role=system.
# Claude Code manda dos cosas que terminan así:
#   1. `system` como lista de bloques (LiteLLM lo traduce a role=system; como texto va a `instructions`).
#   2. mensajes con role=system dentro de `messages` (por ejemplo `<total_tokens>...`).
# Aquí aplanamos lo primero y movemos lo segundo al `system`.
from litellm.integrations.custom_logger import CustomLogger


def _texto(contenido):
    if isinstance(contenido, str):
        return contenido
    return "\n\n".join(b.get("text", "") for b in contenido if isinstance(b, dict) and b.get("type") == "text")


class AplanarSystem(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        partes = []
        if data.get("system"):
            partes.append(_texto(data["system"]))
        restantes = []
        for m in data.get("messages", []):
            if m.get("role") == "system":
                partes.append(_texto(m.get("content", "")))
            else:
                restantes.append(m)
        data["messages"] = restantes
        if partes:
            data["system"] = "\n\n".join(p for p in partes if p)
        return data


proxy_handler_instance = AplanarSystem()
