"""Contratos minimos das fontes cuja disponibilidade ja mudou no passado."""

from filtros_vagas import vaga_elegivel_geograficamente
from vagas import gupy, indeed


def test_gupy_usa_endpoint_atual_e_preserva_cidade_descricao_e_remoto(monkeypatch):
    chamadas = []

    class Resposta:
        status_code = 200

        @staticmethod
        def json():
            return {
                "data": [
                    {
                        "name": "Analista de Infraestrutura",
                        "description": "<p>Google&nbsp;Workspace Active&nbsp;Directory APIs&nbsp;REST suporte&nbsp;N2</p>",
                        "careerPageName": "Empresa Rio",
                        "publishedDate": "2026-08-11",
                        "isRemoteWork": False,
                        "workplaceType": "on-site",
                        "city": "Rio de Janeiro",
                        "state": "Rio de Janeiro",
                        "country": "Brazil",
                        "jobUrl": "https://example.test/gupy-rio",
                    },
                    {
                        "name": "Analista de Suporte N2",
                        "description": "Suporte N2",
                        "careerPageName": "Empresa Niteroi",
                        "publishedDate": "2026-08-11",
                        "isRemoteWork": False,
                        "workplaceType": "on-site",
                        "city": "Niteroi",
                        "state": "Rio de Janeiro",
                        "country": "Brazil",
                        "jobUrl": "https://example.test/gupy-niteroi",
                    },
                    {
                        "name": "Junior Python Developer",
                        "description": "Python REST API Docker",
                        "careerPageName": "Empresa Global",
                        "publishedDate": "2026-08-11",
                        "isRemoteWork": True,
                        "workplaceType": "remote",
                        "city": "London",
                        "state": "England",
                        "country": "United Kingdom",
                        "jobUrl": "https://example.test/gupy-remote",
                    },
                ],
                "pagination": {"total": 3},
            }

    def get(url, **kwargs):
        chamadas.append((url, kwargs["params"]))
        return Resposta()

    monkeypatch.setattr(gupy.requests, "get", get)
    vagas = gupy.buscar(["infra"], limite_por_termo=3)

    assert chamadas == [(gupy.API_URL, {"jobName": "infra", "limit": 3, "offset": 0})]
    assert vagas[0]["descricao"] == "Google Workspace Active Directory APIs REST suporte N2"
    elegiveis = {vaga["url"] for vaga in vagas if vaga_elegivel_geograficamente(vaga)}
    assert elegiveis == {
        "https://example.test/gupy-rio",
        "https://example.test/gupy-remote",
    }


def test_gupy_interrompe_no_primeiro_status_invalido(monkeypatch):
    chamadas = 0

    class Resposta:
        status_code = 404

    def get(*args, **kwargs):
        nonlocal chamadas
        chamadas += 1
        return Resposta()

    monkeypatch.setattr(gupy.requests, "get", get)
    assert gupy.buscar(["infra", "python"]) == []
    assert chamadas == 1


def test_indeed_fica_desativado_por_padrao(monkeypatch):
    monkeypatch.delenv("ENABLE_INDEED", raising=False)
    monkeypatch.setattr(
        indeed.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("nao deve acessar rede")),
    )
    assert indeed.buscar(["python"], ["Rio de Janeiro"]) == []


def test_indeed_autorizado_interrompe_apos_bloqueio(monkeypatch):
    chamadas = 0

    class Resposta:
        status_code = 403

    def get(*args, **kwargs):
        nonlocal chamadas
        chamadas += 1
        return Resposta()

    monkeypatch.setenv("ENABLE_INDEED", "true")
    monkeypatch.setattr(indeed.requests, "get", get)
    assert indeed.buscar(["python", "infra"], ["Rio de Janeiro", "remoto"]) == []
    assert chamadas == 1
