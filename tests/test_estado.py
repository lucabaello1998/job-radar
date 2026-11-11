import json

import pytest

from jobradar import estado


@pytest.fixture
def registro(tmp_path, monkeypatch):
    ruta = tmp_path / "postulaciones.jsonl"
    monkeypatch.setattr(estado, "RUTA", ruta)
    return ruta


def test_agregar_y_leer(registro):
    estado.agregar("remotive:1", "aplicada", empresa="Acme", titulo="Dev")
    estado.agregar("remotive:1", "entrevista", empresa="Acme", titulo="Dev")

    filas = estado.leer()
    assert len(filas) == 2
    assert estado.por_id()["remotive:1"]["estado"] == "entrevista"
    assert estado.resumen()["entrevista"] == 1
    assert estado.resumen()["aplicada"] == 0


def test_estado_invalido(registro):
    with pytest.raises(ValueError, match="estado inválido"):
        estado.agregar("x", "inventado")


def test_linea_corrupta_se_ignora(registro):
    registro.write_text('{"id":"a","estado":"aplicada"}\nno es json\n', encoding="utf-8")
    assert len(estado.leer()) == 1
    assert json.loads(registro.read_text(encoding="utf-8").splitlines()[0])["id"] == "a"


def test_archivo_sin_salto_final_no_se_come_la_linea_nueva(registro):
    # Pasa cuando se edita el JSONL a mano: sin el salto, el append pega las dos
    # filas y se pierden las dos.
    registro.write_text('{"id":"a","estado":"aplicada"}', encoding="utf-8")

    estado.agregar("b", "entrevista")

    filas = estado.leer()
    assert [f["id"] for f in filas] == ["a", "b"]


def test_acepta_bom_al_principio(registro):
    # Notepad guarda UTF-8 con BOM: la primera línea no puede desaparecer.
    registro.write_bytes("\ufeff".encode() + b'{"id":"a","estado":"oferta"}\n')

    assert estado.leer()[0]["id"] == "a"
    assert estado.resumen()["oferta"] == 1


def test_ignora_filas_que_no_son_objetos(registro, capsys):
    registro.write_text('[1,2]\n{"id":"a","estado":"aplicada"}\n', encoding="utf-8")

    assert len(estado.leer()) == 1
    assert "ilegible" in capsys.readouterr().err


def test_resumen_no_explota_con_un_estado_desconocido(registro):
    registro.write_text('{"id":"a","estado":"inventado"}\n', encoding="utf-8")

    assert sum(estado.resumen().values()) == 0


def test_la_cli_hace_algo(registro, capsys):
    # Sin `if __name__ == "__main__"`, `python -m jobradar.estado list` salía en
    # silencio: el README documenta justo ese comando.
    assert estado.main(["add", "x:1", "aplicada", "--empresa", "Acme"]) == 0
    assert "registrado" in capsys.readouterr().out

    assert estado.main(["list"]) == 0
    assert "aplicada" in capsys.readouterr().out

    assert estado.main(["resumen"]) == 0
    assert "aplicada" in capsys.readouterr().out
