from types import SimpleNamespace as NS

import pytest

from taller import estado


@pytest.fixture(autouse=True)
def archivo_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(estado, "ARCHIVO", tmp_path / ".estado.json")


def test_crea_una_vez_y_reutiliza():
    creados = []

    def crear():
        creados.append(1)
        return NS(id=f"agent_{len(creados)}")

    assert estado.sincronizar("agente:a", {"model": "x"}, crear) == "agent_1"
    assert estado.sincronizar("agente:a", {"model": "x"}, crear) == "agent_1"
    assert len(creados) == 1


def test_si_cambia_la_config_actualiza_el_mismo_recurso():
    actualizados = []
    estado.sincronizar("agente:a", {"model": "x"}, lambda: NS(id="agent_1"))
    rid = estado.sincronizar(
        "agente:a", {"model": "y"}, lambda: NS(id="agent_2"), actualizar=actualizados.append
    )
    assert rid == "agent_1"
    assert actualizados == ["agent_1"]


def test_sin_actualizar_crea_uno_nuevo():
    estado.sincronizar("archivo:x", 10, lambda: NS(id="file_1"))
    assert estado.sincronizar("archivo:x", 11, lambda: NS(id="file_2")) == "file_2"
