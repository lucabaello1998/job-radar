"""El tablero es HTML generado: nada de lo que viene de la API se interpola crudo."""

from jobradar import tablero


def _oferta(**cambios):
    fila = {
        "id": 'x"><img src=x onerror=alert(1)>',
        "fuente": "Prueba",
        "titulo": "Fullstack",
        "empresa": "Acme",
        "url": "https://example.com/1",
        "ubicacion": "Remoto",
        "salario": "",
        "publicado": "2026-11-11",
        "descripcion": "React .NET",
        "tags": ["react"],
        "puntaje": 80,
        "motivos": ["+4 .NET"],
        "idioma": "es",
        "estado": "",
    }
    fila.update(cambios)
    return fila


def test_escapa_el_id_en_el_atributo():
    # El id sale de la API remota: si trae comillas, rompe el atributo y puede
    # inyectar un handler.
    html = tablero.render([_oferta()], {}, ["remotive"], [])

    assert 'data-i="x"><img' not in html
    assert "&quot;" in html


def test_escribe_de_una_sola_vez(tmp_path):
    destino = tmp_path / "index.html"
    tablero.escribir([_oferta()], {}, [], [], destino)

    assert destino.exists()
    assert not (tmp_path / "index.html.tmp").exists()
