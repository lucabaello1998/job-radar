import json

from jobradar import estado


def test_agregar_y_leer(tmp_path, monkeypatch):
    ruta = tmp_path / "postulaciones.jsonl"
    monkeypatch.setattr(estado, "RUTA", ruta)

    estado.agregar("remotive:1", "aplicada", empresa="Acme", titulo="Dev")
    estado.agregar("remotive:1", "entrevista", empresa="Acme", titulo="Dev")

    filas = estado.leer()
    assert len(filas) == 2
    assert estado.por_id()["remotive:1"]["estado"] == "entrevista"
    assert estado.resumen()["entrevista"] == 1
    assert estado.resumen()["aplicada"] == 0


def test_estado_invalido(tmp_path, monkeypatch):
    monkeypatch.setattr(estado, "RUTA", tmp_path / "p.jsonl")
    try:
        estado.agregar("x", "inventado")
    except ValueError as error:
        assert "estado inválido" in str(error)
    else:
        raise AssertionError("debía rechazar el estado")


def test_linea_corrupta_se_ignora(tmp_path, monkeypatch):
    ruta = tmp_path / "p.jsonl"
    ruta.write_text('{"id":"a","estado":"aplicada"}\nno es json\n', encoding="utf-8")
    monkeypatch.setattr(estado, "RUTA", ruta)
    assert len(estado.leer()) == 1
    assert json.loads((ruta).read_text(encoding="utf-8").splitlines()[0])["id"] == "a"
