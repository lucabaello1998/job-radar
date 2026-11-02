from jobradar.construir import idioma, procesar
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
