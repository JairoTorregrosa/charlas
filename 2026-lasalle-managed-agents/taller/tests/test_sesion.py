"""Pruebas sin red del loop de eventos. No gastan créditos."""
from types import SimpleNamespace as NS

import pytest

from taller.sesion import conversar


def texto(t):
    return NS(type="agent.message", content=[NS(type="text", text=t)])


def idle(motivo, event_ids=()):
    return NS(type="session.status_idle", stop_reason=NS(type=motivo, event_ids=list(event_ids)))


def custom(id_, name, input_):
    return NS(type="agent.custom_tool_use", id=id_, name=name, input=input_)


def tool(id_, name, input_):
    return NS(type="agent.tool_use", id=id_, name=name, input=input_)


class FakeStream:
    def __init__(self, eventos):
        self.eventos = eventos

    def __enter__(self):
        return iter(self.eventos)  # funciona con listas y con generadores

    def __exit__(self, *exc):
        return False


class FakeClient:
    """Imita client.beta.sessions.events con una lista fija de eventos."""

    def __init__(self, eventos, historial=()):
        self.enviados = []
        events = NS(
            stream=lambda session_id: FakeStream(eventos),
            send=lambda session_id, events: self.enviados.append(list(events)),
            list=lambda session_id: iter(historial),
        )
        self.beta = NS(sessions=NS(events=events))


def test_termina_en_end_turn_y_junta_el_texto():
    client = FakeClient([texto("hola "), texto("mundo"), idle("end_turn")])
    r = conversar(client, "s", "hola", mostrar=False)
    assert r.motivo == "end_turn"
    assert r.texto == "hola mundo"
    assert len(client.enviados) == 1  # solo el mensaje del usuario


def test_responde_custom_tool_una_sola_vez_aunque_se_repita_requires_action():
    client = FakeClient([
        custom("c1", "sumar", {"a": 2, "b": 3}),
        idle("requires_action", ["c1"]),
        idle("requires_action", ["c1"]),  # el servidor vuelve a listarla
        idle("end_turn"),
    ])
    llamadas = []

    def sumar(entrada):
        llamadas.append(entrada)
        return str(entrada["a"] + entrada["b"])

    r = conversar(client, "s", "suma", herramientas={"sumar": sumar}, mostrar=False)
    assert r.motivo == "end_turn"
    assert llamadas == [{"a": 2, "b": 3}]
    respuestas = client.enviados[1:]
    assert respuestas == [[{
        "type": "user.custom_tool_result",
        "custom_tool_use_id": "c1",
        "content": [{"type": "text", "text": "5"}],
        "is_error": False,
    }]]


def test_error_en_la_tool_vuelve_al_agente_marcado_como_error():
    client = FakeClient([custom("c1", "rota", {}), idle("requires_action", ["c1"]), idle("end_turn")])

    def rota(_):
        raise ValueError("sin datos")

    conversar(client, "s", "x", herramientas={"rota": rota}, mostrar=False)
    (respuesta,) = client.enviados[1]
    assert respuesta["is_error"] is True
    assert "ValueError: sin datos" in respuesta["content"][0]["text"]


def test_tool_desconocida_no_inventa_resultado():
    client = FakeClient([custom("c1", "fantasma", {}), idle("requires_action", ["c1"]), idle("end_turn")])
    conversar(client, "s", "x", mostrar=False)
    (respuesta,) = client.enviados[1]
    assert respuesta["is_error"] is True


def test_solo_contesta_las_tools_que_la_sesion_pide():
    client = FakeClient([
        tool("t1", "read", {"file_path": "/x"}),  # always_allow: no espera respuesta
        tool("t2", "bash", {"command": "rm -rf /tmp/x"}),
        idle("requires_action", ["t2"]),
        idle("end_turn"),
    ])
    preguntadas = []

    def aprobar(evento):
        preguntadas.append(evento.id)
        return False

    conversar(client, "s", "x", aprobar=aprobar, mostrar=False)
    assert preguntadas == ["t2"]
    (respuesta,) = client.enviados[1]
    assert respuesta["tool_use_id"] == "t2"
    assert respuesta["result"] == "deny"


def test_sin_aprobador_niega_en_vez_de_aprobar():
    client = FakeClient([tool("t1", "bash", {"command": "ls"}), idle("requires_action", ["t1"]), idle("end_turn")])
    conversar(client, "s", "x", mostrar=False)
    assert client.enviados[1][0]["result"] == "deny"


def test_busca_en_el_historial_si_el_evento_no_llego_por_el_stream():
    perdido = custom("c9", "sumar", {"a": 1, "b": 1})
    client = FakeClient([idle("requires_action", ["c9"]), idle("end_turn")], historial=[perdido])
    conversar(client, "s", "x", herramientas={"sumar": lambda e: "2"}, mostrar=False)
    assert client.enviados[1][0]["custom_tool_use_id"] == "c9"


def test_budget_reached_se_reporta():
    client = FakeClient([idle("budget_reached")])
    assert conversar(client, "s", "x", mostrar=False).motivo == "budget_reached"


def test_stream_que_se_cierra_sin_idle_falla_en_voz_alta():
    client = FakeClient([texto("a medias")])
    with pytest.raises(RuntimeError, match="sigue viva"):
        conversar(client, "s", "x", mostrar=False)


def test_ctrl_c_interrumpe_la_sesion_en_el_servidor():
    class Corta:
        def __iter__(self):
            yield texto("pensando")
            raise KeyboardInterrupt

    client = FakeClient([])
    client.beta.sessions.events.stream = lambda session_id: FakeStream(Corta())
    with pytest.raises(KeyboardInterrupt):
        conversar(client, "s", "x", mostrar=False)
    assert client.enviados[-1] == [{"type": "user.interrupt"}]
