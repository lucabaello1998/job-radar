from jobradar.modelo import Oferta
from jobradar.puntuar import UMBRAL_PUBLICABLE, es_rol_tech, puntuar


def _oferta(titulo="Fullstack Developer", descripcion="", tags=None, ubicacion="Worldwide"):
    return Oferta(
        id="x:1",
        fuente="X",
        titulo=titulo,
        empresa="Acme",
        url="https://example.com",
        ubicacion=ubicacion,
        descripcion=descripcion,
        tags=tags or [],
    )


def test_encaje_alto_con_stack_objetivo():
    oferta = puntuar(_oferta(descripcion="React, Next.js, TypeScript and .NET. Remote, paid in USD."))
    assert oferta.puntaje >= 60
    assert any(".NET" in m for m in oferta.motivos)
    assert any("Remoto" in m for m in oferta.motivos)


def test_oferta_de_otro_stack_queda_bajo_el_umbral():
    oferta = puntuar(
        _oferta(titulo="Salesforce Administrator", descripcion="Salesforce, ServiceNow, SAP ABAP, on-site.")
    )
    assert oferta.puntaje < UMBRAL_PUBLICABLE


def test_solo_estados_unidos_penaliza():
    con_restriccion = puntuar(_oferta(descripcion="React .NET remote. US only, must be located in the US."))
    sin_restriccion = puntuar(_oferta(descripcion="React .NET remote."))
    assert con_restriccion.puntaje < sin_restriccion.puntaje


def test_pasantia_queda_bajo_el_umbral():
    oferta = puntuar(_oferta(titulo="Software Engineering Intern", descripcion="React internship, unpaid."))
    assert oferta.puntaje < UMBRAL_PUBLICABLE


def test_es_rol_tech_distingue_roles_de_desarrollo():
    assert es_rol_tech(_oferta(titulo="Asesor comercial")) is False
    assert es_rol_tech(_oferta(titulo="Senior Fullstack Engineer")) is True


def test_puntaje_nunca_sale_de_rango():
    oferta = puntuar(_oferta(descripcion="React Next.js TypeScript .NET USD remote " * 40 + "unpaid equity only"))
    assert 0 <= oferta.puntaje <= 100


def test_cada_punto_tiene_motivo():
    oferta = puntuar(_oferta(descripcion="React and .NET"))
    assert oferta.puntaje > 0
    assert len(oferta.motivos) >= 2
