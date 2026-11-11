import json

from jobradar.construir import destino, idioma, procesar
from jobradar.modelo import Oferta


def _oferta(id_, titulo, empresa, descripcion="React Next.js .NET remote USD", puntaje_extra=""):
    return Oferta(
        id=id_,
        fuente="Prueba",
        titulo=titulo,
        empresa=empresa,
        url=f"https://example.com/{id_}",
        descripcion=descripcion + " " + puntaje_extra,
        tags=["react"],
    )


def test_deduplica_la_misma_oferta_en_dos_fuentes():
    ofertas = [
        _oferta("a:1", "Senior .NET Developer", "Acme"),
        _oferta("b:2", "senior net developer", "ACME"),
    ]
    resultado = procesar(ofertas, {})
    assert len(resultado) == 1


def test_descarta_ofertas_sin_url_o_sin_titulo():
    sin_url = _oferta("a:1", "Dev", "Acme")
    sin_url.url = ""
    resultado = procesar([sin_url], {})
    assert resultado == []


def test_descarta_urls_que_no_son_http():
    javascript = _oferta("a:1", "Fullstack React .NET", "Acme")
    javascript.url = "javascript:alert(1)"
    resultado = procesar([javascript], {})
    assert resultado == []


def test_marca_estado_registrado():
    oferta = _oferta("a:1", "Fullstack React .NET", "Acme")
    resultado = procesar([oferta], {"a:1": {"estado": "aplicada"}})
    assert resultado[0]["estado"] == "aplicada"


def test_idioma_detecta_ingles_y_espanol():
    assert idioma(_oferta("a", "Dev", "Acme", "We are looking for an engineer with experience in the team")) == "en"
    assert idioma(_oferta("b", "Dev", "Acme", "Buscamos un desarrollador para el equipo con experiencia")) == "es"


def test_resultado_ordenado_por_puntaje():
    flojo = _oferta("a:1", "Fullstack Developer", "Uno", "React")
    fuerte = _oferta("b:2", "Fullstack Developer", "Dos", "React Next.js TypeScript .NET remote USD argentina")
    resultado = procesar([flojo, fuerte], {})
    assert resultado[0]["puntaje"] >= resultado[-1]["puntaje"]


def test_ordena_aunque_una_empresa_venga_vacia():
    # `empresa` sale de la API: si viene None, ordenar explotaba y no se escribía
    # nada del tablero.
    floja = _oferta("a:1", "Fullstack Developer", None)
    fuerte = _oferta("b:2", "Fullstack Developer", "Dos", "React Next.js TypeScript .NET remote USD argentina")
    resultado = procesar([floja, fuerte], {})

    assert len(resultado) == 2
    assert {f["empresa"] for f in resultado} == {None, "Dos"}


def test_el_minimo_puede_bajar_el_corte():
    # Antes `--minimo` solo podía subir: `--minimo 0` daba lo mismo que el default.
    floja = Oferta(
        id="a:1", fuente="Prueba", titulo="Developer", empresa="Uno", url="https://example.com/1", descripcion=""
    )
    con_default = procesar([floja], {})
    con_cero = procesar([floja], {}, minimo=0)

    assert len(con_default) == 0
    assert len(con_cero) == 1


def test_una_corrida_parcial_no_pisa_el_tablero(tmp_path):
    from jobradar.construir import DOCS, PREVIA

    assert destino(True, None) == PREVIA
    assert destino(False, None) == DOCS
    assert destino(False, None, solo=True) == PREVIA
    assert destino(False, tmp_path, solo=True) == tmp_path


def test_sin_ofertas_la_corrida_falla_pero_sin_publicar_nada(monkeypatch, tmp_path, capsys):
    from jobradar import construir

    monkeypatch.setattr(construir, "recolectar", lambda *a, **k: ([], [], ["remotive: HTTPError"]))
    codigo = construir.main(["--offline", "--docs", str(tmp_path)])

    assert codigo == 1
    assert "no se toca el tablero" in capsys.readouterr().out
    assert not (tmp_path / "index.html").exists()


def test_si_hay_ofertas_pero_ninguna_pasa_el_corte_no_es_un_error(monkeypatch, tmp_path, capsys):
    from jobradar import construir

    floja = _oferta("a:1", "Fullstack Developer", "Uno", "React")
    monkeypatch.setattr(construir, "recolectar", lambda *a, **k: ([floja], ["remotive (1)"], []))
    codigo = construir.main(["--offline", "--docs", str(tmp_path), "--minimo", "99"])

    assert codigo == 0
    assert "no se toca el tablero" in capsys.readouterr().out
    assert not (tmp_path / "index.html").exists()


def test_la_corrida_completa_escribe_el_json_y_el_html(monkeypatch, tmp_path):
    from jobradar import construir

    oferta = _oferta("a:1", "Fullstack Developer", "Acme", "React Next.js .NET remote USD")
    monkeypatch.setattr(construir, "recolectar", lambda *a, **k: ([oferta], ["remotive (1)"], []))
    codigo = construir.main(["--offline", "--docs", str(tmp_path)])

    assert codigo == 0
    datos = json.loads((tmp_path / "data" / "ofertas.json").read_text(encoding="utf-8"))
    assert datos["total"] == 1
    assert "<html" in (tmp_path / "index.html").read_text(encoding="utf-8").lower()


def test_el_modo_privado_no_publica_el_estado_de_cada_oferta(monkeypatch, tmp_path):
    from jobradar import construir

    oferta = _oferta("a:1", "Fullstack Developer", "Acme", "React Next.js .NET remote USD")
    monkeypatch.setattr(construir, "recolectar", lambda *a, **k: ([oferta], ["remotive (1)"], []))
    monkeypatch.setattr(construir.estado, "por_id", lambda: {"a:1": {"estado": "entrevista"}})

    construir.main(["--offline", "--docs", str(tmp_path)])
    con_estado = json.loads((tmp_path / "data" / "ofertas.json").read_text(encoding="utf-8"))["ofertas"][0]
    assert con_estado["estado"] == "entrevista"

    construir.main(["--offline", "--docs", str(tmp_path), "--privado"])
    privado = json.loads((tmp_path / "data" / "ofertas.json").read_text(encoding="utf-8"))["ofertas"][0]
    assert privado["estado"] == ""
