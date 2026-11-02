from jobradar.modelo import Oferta, limpiar_html, slug


def test_limpiar_html_saca_etiquetas_y_entidades():
    crudo = "<p>Hello <b>world</b>&nbsp;&amp; more</p>\n<div>second</div>"
    assert limpiar_html(crudo) == "Hello world & more second"


def test_limpiar_html_vacio():
    assert limpiar_html(None) == ""
    assert limpiar_html("") == ""


def test_limpiar_html_recorta():
    assert len(limpiar_html("<p>" + "x" * 500 + "</p>", limite=100)) == 100


def test_slug_estable_y_seguro():
    assert slug("Acme Corp — Senior .NET Developer") == "acme-corp-senior-net-developer"
    assert slug("!!!") == "oferta"


def test_clave_ignora_mayusculas_y_puntuacion():
    a = Oferta(id="1", fuente="x", titulo="Senior .NET Dev", empresa="ACME", url="u")
    b = Oferta(id="2", fuente="y", titulo="senior net dev", empresa="acme", url="u")
    assert a.clave == b.clave
