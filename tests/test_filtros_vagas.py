"""Regressoes de modalidade e localizacao da busca de vagas."""

import time

import pytest

from filtros_vagas import (
    detectar_modalidade,
    eh_cidade_rio,
    extrair_localizacao_anuncio,
    vaga_elegivel_geograficamente,
)
from vagas_por_email.buscar_e_enviar import (
    _executar_com_timeout,
    _nao_e_pcd_exclusiva,
    processar,
)
from vagas import himalayas


def _vaga(local, modalidade="Presencial", plataforma="Gupy", **extras):
    vaga = {
        "titulo": "Analista de Infraestrutura",
        "descricao": "Active Directory, Google Workspace e suporte N2",
        "local": local,
        "modalidade": modalidade,
        "modalidade_confiavel": plataforma == "Gupy",
        "local_confiavel": plataforma == "Gupy",
        "url": extras.pop("url", f"https://example.test/{local}"),
        "plataforma": plataforma,
        "pais": extras.pop("pais", "BR"),
    }
    vaga.update(extras)
    return vaga


@pytest.mark.parametrize(
    "local",
    [
        "Rio de Janeiro, RJ",
        "Rio de Janeiro / RJ",
        "Rio de Janeiro (RJ)",
        "Rio de Janeiro, Rio de Janeiro, Brazil",
    ],
)
def test_presencial_na_cidade_do_rio_e_aceita(local):
    assert vaga_elegivel_geograficamente(_vaga(local))


@pytest.mark.parametrize(
    "local",
    [
        "Niteroi, RJ",
        "Niteroi, Rio de Janeiro, Brazil",
        "Duque de Caxias, RJ",
        "Duque de Caxias, Rio de Janeiro",
        "Nova Iguacu, RJ",
        "Petropolis, Rio de Janeiro",
        "Sao Goncalo, RJ",
        "Petropolis, RJ",
        "Volta Redonda, RJ",
        "Macae, RJ",
        "RJ",
        "Brasil",
        "Regiao Metropolitana do Rio de Janeiro",
        "Rio de Janeiro e Regiao",
        "Greater Rio de Janeiro",
        "Sao Paulo, SP",
        "",
        None,
    ],
)
def test_presencial_fora_da_cidade_do_rio_e_rejeitada(local):
    assert not vaga_elegivel_geograficamente(_vaga(local))


def test_hibrida_fora_do_rio_e_rejeitada():
    assert not vaga_elegivel_geograficamente(_vaga("Niteroi, RJ", "Hibrido"))


@pytest.mark.parametrize(
    "local",
    [
        "Barra da Tijuca / RJ",
        "Copacabana - RJ",
        "Botafogo, RJ",
        "Ilha do Governador, RJ",
        "Meier / RJ",
        "Maracana - RJ",
        "Vila Isabel, Rio de Janeiro, Brazil",
        "Centro, Rio de Janeiro, Brazil",
        "Campo Grande, RJ",
    ],
)
def test_bairro_da_capital_e_aceito(local):
    assert vaga_elegivel_geograficamente(_vaga(local))


def test_gupy_nao_confunde_estado_rio_de_janeiro_com_cidade():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="Gupy",
        local_confiavel=False,
    )
    assert not vaga_elegivel_geograficamente(vaga)


@pytest.mark.parametrize("local", ["Worldwide", "LATAM", "Europe", "United States"])
def test_remota_internacional_e_aceita(local):
    vaga = _vaga(
        local,
        modalidade="Remoto",
        plataforma="Remotive",
        pais="WW",
        modalidade_confiavel=True,
        local_confiavel=True,
    )
    assert vaga_elegivel_geograficamente(vaga)


def test_himalayas_mantem_remota_restrita_a_regiao_internacional(monkeypatch):
    class Resposta:
        status_code = 200

        @staticmethod
        def json():
            return {
                "jobs": [{
                    "guid": "https://example.test/himalayas-latam",
                    "title": "IT Support Analyst",
                    "description": "Application support and API integration",
                    "locationRestrictions": ["LATAM"],
                    "companyName": "Example",
                    "pubDate": "2026-08-10",
                }]
            }

    monkeypatch.setattr(himalayas.requests, "get", lambda *args, **kwargs: Resposta())
    vagas = himalayas.buscar(limite_por_termo=1)

    assert len(vagas) == 1
    assert vagas[0]["local"] == "LATAM"
    assert vagas[0]["modalidade"] == "Remoto"


def test_suporte_remoto_na_descricao_nao_muda_regime():
    assert detectar_modalidade("Atendimento presencial com suporte remoto via AnyDesk") == "Presencial"


def test_presencial_explicito_prevalece_sobre_contexto_remoto():
    texto = "Vaga presencial em Sao Paulo. Suporte a usuarios em trabalho remoto."
    assert detectar_modalidade(texto) == "Presencial"


def test_home_office_eventual_nao_muda_regime():
    assert detectar_modalidade("Trabalho no escritorio, com home office eventual") == "Presencial"


@pytest.mark.parametrize(
    "texto",
    [
        "Home office 2x por semana",
        "Dois dias presenciais e tres em home office",
        "Possibilidade de home office uma vez por semana",
    ],
)
def test_escala_parcial_de_home_office_e_hibrida(texto):
    assert detectar_modalidade(texto) == "Hibrido"


@pytest.mark.parametrize(
    "texto",
    [
        "Remoto",
        "Remote",
        "Analista de Infraestrutura - Remoto",
        "Remote IT Support Analyst",
        "IT Support Analyst (Remote - Brazil)",
        "Brazil - Remote: IT Support Analyst",
        "L2 Support Engineer, Alpha (Remote) - 60k",
        "Vaga 100% remota",
        "Remote position",
        "Work from anywhere",
        "Modelo home office",
    ],
)
def test_sinais_fortes_identificam_remoto(texto):
    assert detectar_modalidade(texto) == "Remoto"


def test_vagas_com_ignora_local_da_consulta_quando_anuncio_e_de_sp():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="Vagas.com",
        local_confiavel=False,
        descricao="Analista de TI\nSao Paulo / SP\nOntem",
        url="https://www.vagas.com.br/vagas/v1/analista-de-ti",
    )
    assert not vaga_elegivel_geograficamente(vaga)


def test_vagas_com_aceita_rio_confirmado_no_anuncio():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="Vagas.com",
        local_confiavel=False,
        descricao="Analista de TI\nRio de Janeiro / RJ\nOntem",
        url="https://www.vagas.com.br/vagas/v2/analista-de-ti",
    )
    assert vaga_elegivel_geograficamente(vaga)
    assert eh_cidade_rio(vaga["local_confirmado"])


def test_infojobs_usa_cidade_da_url_e_rejeita_sao_paulo():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="InfoJobs",
        local_confiavel=False,
        descricao="Analista de suporte",
        url="https://www.infojobs.com.br/vaga-de-analista-suporte-em-sao-paulo__123.aspx",
    )
    assert not vaga_elegivel_geograficamente(vaga)


def test_infojobs_prioriza_niteroi_do_card_sobre_estado_da_url():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="InfoJobs",
        local_confiavel=False,
        descricao="Estagio em Automacao - Niteroi - RJ - Presencial",
        url="https://www.infojobs.com.br/vaga-de-estagio-em-rio-janeiro__123.aspx",
    )
    assert not vaga_elegivel_geograficamente(vaga)


def test_infojobs_aceita_cidade_do_rio_confirmada_no_card():
    vaga = _vaga(
        "Rio de Janeiro",
        plataforma="InfoJobs",
        local_confiavel=False,
        descricao="Analista de Infraestrutura - Rio de Janeiro - RJ - Presencial",
        url="https://www.infojobs.com.br/vaga-de-analista-em-rio-janeiro__124.aspx",
    )
    assert vaga_elegivel_geograficamente(vaga)


def test_local_rotulado_prevalece_sobre_outra_cidade_mencionada():
    texto = "Local: Sao Paulo / SP; atendimento tambem no Rio de Janeiro / RJ"
    assert extrair_localizacao_anuncio(texto) == "Sao Paulo / SP"


def test_duas_localidades_sem_campo_confiavel_sao_ambiguas():
    texto = "Sao Paulo / SP ou Rio de Janeiro / RJ, conforme o projeto"
    assert extrair_localizacao_anuncio(texto) == ""


@pytest.mark.parametrize(
    "texto",
    [
        "Rio de Janeiro / RJ Python CI/CD",
        "Rio de Janeiro / RJ React / JS",
        "Rio de Janeiro / RJ UI/UX",
    ],
)
def test_tecnologias_nao_sao_confundidas_com_segunda_cidade(texto):
    assert extrair_localizacao_anuncio(texto) == "Rio de Janeiro, RJ"


def test_mencao_inclusiva_a_pcd_nao_e_excluida():
    vaga = _vaga("Rio de Janeiro, RJ", descricao="Vaga aberta a todos, incluindo PCD")
    assert _nao_e_pcd_exclusiva(vaga)


@pytest.mark.parametrize(
    "titulo,descricao",
    [
        ("Analista de Suporte - PCD ou ampla concorrencia", ""),
        ("Analista de Suporte - PCD e nao PCD", ""),
        ("Analista de Suporte (PCD)", "Tambem aberta para profissionais sem deficiencia"),
        ("Analista de Suporte", "Candidatos com ou sem deficiencia podem participar"),
    ],
)
def test_variantes_inclusivas_de_pcd_nao_sao_excluidas(titulo, descricao):
    assert _nao_e_pcd_exclusiva({"titulo": titulo, "descricao": descricao})


@pytest.mark.parametrize(
    "titulo,descricao",
    [
        ("Analista de Suporte - PCD", ""),
        ("Analista de Suporte", "Vaga exclusiva para pessoas com deficiencia"),
        ("Analista de Suporte", "Oportunidade destinada apenas a PCD"),
        ("Analista de Suporte", "Vaga afirmativa para PCD"),
        ("Analista de Suporte", "Oportunidade preferencial para pessoas com deficiencia"),
    ],
)
def test_vaga_pcd_exclusiva_e_excluida(titulo, descricao):
    assert not _nao_e_pcd_exclusiva({"titulo": titulo, "descricao": descricao})


def test_timeout_de_fonte_retorna_sem_esperar_thread_terminar():
    inicio = time.perf_counter()
    with pytest.raises(TimeoutError):
        _executar_com_timeout(lambda: time.sleep(0.3), 0.01)
    assert time.perf_counter() - inicio < 0.2


def test_pipeline_nao_deixa_home_office_parcial_furar_filtro_da_cidade():
    vaga = _vaga(
        "Sao Paulo, SP",
        plataforma="LinkedIn",
        modalidade="",
        modalidade_confiavel=False,
        local_confiavel=True,
        descricao="Suporte N2. Home office 2x por semana.",
    )
    assert processar([vaga], score_minimo=40) == []


def test_pipeline_mantem_apenas_rio_e_remoto_internacional():
    rio = _vaga("Rio de Janeiro, RJ", url="https://example.test/rio")
    remoto = {
        "titulo": "Junior Python Backend Developer",
        "descricao": "Python, REST API, Docker e CI/CD",
        "local": "Worldwide",
        "local_confiavel": True,
        "modalidade": "Remoto",
        "modalidade_confiavel": True,
        "url": "https://example.test/remote",
        "plataforma": "Remotive",
        "pais": "WW",
    }
    niteroi = _vaga("Niteroi, RJ", url="https://example.test/niteroi")
    sp = _vaga("Sao Paulo, SP", "Hibrido", url="https://example.test/sp")

    resultado = processar([rio, remoto, niteroi, sp], score_minimo=40)

    assert [vaga["url"] for vaga in resultado] == [
        "https://example.test/remote",
        "https://example.test/rio",
    ]
