"""Las fuentes no pueden perder una fuente entera por una fila rara."""

import json

import pytest

from jobradar import fuentes


@pytest.fixture
def fixture_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(fuentes, "FIXTURES", tmp_path)
    return tmp_path


def _guardar(carpeta, nombre, datos):
    (carpeta / f"{nombre}.json").write_text(json.dumps(datos), encoding="utf-8")


def test_remotive_sobrevive_a_tags_nulos(fixture_dir):
    _guardar(
        fixture_dir,
        "remotive",
        {
            "jobs": [
                {"id": 1, "title": "Dev", "company_name": "Acme", "url": "https://x/1", "tags": None},
                {"id": 2, "title": "Otro", "company_name": "Beta", "url": "https://x/2", "tags": ["react"]},
            ]
        },
    )

    ofertas = fuentes.remotive(offline=True)

    assert len(ofertas) == 2
    assert ofertas[0].tags == []


def test_remotive_descarta_una_fila_rota_y_sigue_con_las_demas(fixture_dir, capsys):
    _guardar(fixture_dir, "remotive", {"jobs": ["no soy un objeto", {"id": 2, "title": "Dev", "url": "https://x/2"}]})

    ofertas = fuentes.remotive(offline=True)

    assert len(ofertas) == 1
    assert "descartó 1" in capsys.readouterr().err


def test_remoteok_acepta_salarios_como_texto(fixture_dir):
    _guardar(
        fixture_dir,
        "remoteok",
        [
            {"legal": "aviso"},
            {"id": 1, "position": "Dev", "company": "Acme", "salary_min": "60000", "salary_max": "90000"},
            {"id": 2, "position": "Dev 2", "company": "Beta", "salary_min": "abc", "salary_max": None},
        ],
    )

    ofertas = fuentes.remoteok(offline=True)

    assert len(ofertas) == 2
    assert "USD 60.000" in ofertas[0].salario
    assert ofertas[1].salario == ""


def test_getonboard_acepta_salarios_como_texto(fixture_dir):
    _guardar(
        fixture_dir,
        "getonboard",
        {
            "data": [
                {
                    "id": "j1",
                    "attributes": {
                        "title": "Fullstack",
                        "min_salary": "1500",
                        "max_salary": "2000",
                        "countries": ["Chile"],
                        "company": {"data": {"attributes": {"name": "Acme"}}},
                    },
                    "links": {"public_url": "https://x/1"},
                }
            ]
        },
    )

    ofertas = fuentes.getonboard(offline=True)

    assert len(ofertas) == 1
    assert "CLP 1.500" in ofertas[0].salario


def test_un_payload_de_error_no_cuenta_como_fuente_vacia(fixture_dir):
    # Antes, `{"errors": [...]}` devolvía 0 ofertas y la fuente se reportaba "ok":
    # el tablero se achicaba sin que nadie se enterara.
    _guardar(fixture_dir, "remotive", {"errors": ["rate limited"]})

    with pytest.raises(ValueError, match="jobs"):
        fuentes.remotive(offline=True)


def test_un_fixture_que_falta_es_un_error_no_cero_ofertas(fixture_dir):
    with pytest.raises(ValueError, match="fixture"):
        fuentes.getonboard(offline=True)


def test_la_fecha_tolera_valores_raros():
    assert fuentes._fecha(None) == ""
    assert fuentes._fecha("no es una fecha") == ""
    assert fuentes._fecha(10**20) == ""
    assert len(fuentes._fecha(1700000000)) == 10


def test_el_agente_de_usuario_no_lleva_un_mail_personal():
    assert "@" not in fuentes.AGENTE
    assert "github.com" in fuentes.AGENTE
