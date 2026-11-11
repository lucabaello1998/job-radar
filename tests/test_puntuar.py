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


def test_los_puestos_de_venta_y_soporte_no_son_de_desarrollo():
    # "Engineer" solo no alcanza: el README prometía descartarlos.
    for titulo in ("Sales Engineer", "Customer Support Engineer", "Solutions Support Specialist"):
        assert es_rol_tech(_oferta(titulo=titulo)) is False, titulo


def test_pide_la_decada_solo_cuando_lo_pide():
    con_requisito = puntuar(_oferta(descripcion="React .NET remote. 10+ years of experience required."))
    con_rango = puntuar(_oferta(descripcion="React .NET remote. Requires 5-10 years of experience."))
    historia = puntuar(_oferta(descripcion="React .NET remote. We have served clients for 20 years."))

    assert any("10+ años" in m for m in con_requisito.motivos)
    assert not any("10+ años" in m for m in con_rango.motivos)
    assert not any("10+ años" in m for m in historia.motivos)


def test_una_oferta_remota_explicita_no_se_penaliza_por_hibrida():
    remota = puntuar(_oferta(descripcion="React .NET. Fully remote, not hybrid, no on-site work."))
    hibrida = puntuar(_oferta(descripcion="React .NET. Hybrid, three days on-site."))

    assert not any("Híbrido" in m or "Presencial" in m for m in remota.motivos)
    assert remota.puntaje > hibrida.puntaje


def test_reconoce_us_only_con_guion():
    con_guion = puntuar(_oferta(descripcion="React .NET. US-only candidates."))
    sin_restriccion = puntuar(_oferta(descripcion="React .NET."))

    assert any("Solo EE.UU." in m for m in con_guion.motivos)
    assert con_guion.puntaje < sin_restriccion.puntaje


def test_puntaje_nunca_sale_de_rango():
    oferta = puntuar(_oferta(descripcion="React Next.js TypeScript .NET USD remote " * 40 + "unpaid equity only"))
    assert 0 <= oferta.puntaje <= 100


def test_cada_punto_tiene_motivo():
    oferta = puntuar(_oferta(descripcion="React and .NET"))
    assert oferta.puntaje > 0
    assert len(oferta.motivos) >= 2
