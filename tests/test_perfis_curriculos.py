"""Testes do perfil combinado extraido dos curriculos Infra e Dev."""

import pytest

from matcher import calcular_aderencia, calcular_score
from perfis_busca import PERFIS_BUSCA, TERMOS_BUSCA
from vagas import himalayas, infojobs, linkedin, vagas_com


def test_vaga_infra_forte_combina_com_curriculo_infra():
    vaga = {
        "titulo": "Analista de Suporte N2",
        "descricao": "Active Directory, Google Workspace, IAM, GLPI e chamados",
        "modalidade": "Presencial",
    }
    aderencia = calcular_aderencia(vaga)
    assert aderencia["score"] >= 60
    assert aderencia["perfil_match"] == "Infra e Suporte"


def test_vaga_dev_junior_combina_com_curriculo_dev():
    vaga = {
        "titulo": "Junior Python Backend Developer",
        "descricao": "Python, REST API, FastAPI, Docker, Git e CI/CD",
        "modalidade": "Remoto",
    }
    aderencia = calcular_aderencia(vaga)
    assert aderencia["score"] >= 60
    assert aderencia["perfil_match"] == "Automacao e Dev"


def test_vaga_irrelevante_nao_passa_so_por_ser_remota():
    vaga = {
        "titulo": "Sales Manager",
        "descricao": "Remote position for commercial sales",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) == 0


def test_tecnologias_nao_comprovadas_nao_geram_score():
    vaga = {
        "titulo": "Cloud Platform Engineer",
        "descricao": "Kubernetes, Terraform, AWS, Azure, GCP, Prometheus e Grafana",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) == 0


def test_automacao_industrial_e_penalizada():
    vaga = {
        "titulo": "Analista de Automacao Industrial",
        "descricao": "PLC, SCADA e robotica industrial",
        "modalidade": "Presencial",
    }
    assert calcular_score(vaga) < 40


def test_devops_sem_indicacao_junior_nao_passa_so_por_descricao_generica():
    vaga = {
        "titulo": "OCI DevOps Engineer",
        "descricao": "Docker, Git, CI/CD e deployment",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) < 40


def test_suporte_nivel_tres_e_penalizado():
    vaga = {
        "titulo": "IT Support Analyst III",
        "descricao": "",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) < 40


def test_analista_de_sistemas_dotnet_nao_passa_por_titulo_generico():
    vaga = {
        "titulo": "Analista de Sistemas - C# / .NET",
        "descricao": "",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) < 40


def test_score_final_e_o_maior_das_duas_trilhas():
    vaga = {
        "titulo": "Analista de Automacao",
        "descricao": "Python, REST API, Google Workspace e Active Directory",
        "modalidade": "Hibrido",
    }
    aderencia = calcular_aderencia(vaga)
    scores = {
        chave: calcular_score(vaga, perfil)
        for chave, perfil in PERFIS_BUSCA.items()
    }
    assert aderencia["score"] == max(scores.values())
    assert aderencia["scores"] == scores


@pytest.mark.parametrize("titulo", TERMOS_BUSCA)
def test_cada_termo_pesquisado_passaria_no_ranking_so_pelo_titulo(titulo):
    vaga = {"titulo": titulo, "descricao": "", "modalidade": "Remoto"}
    assert calcular_score(vaga) >= 40


@pytest.mark.parametrize(
    "titulo",
    [
        "Tecnico de Suporte e Infraestrutura de TI",
        "Tecnico de Suporte Jr",
        "IT Support Technician",
        "Analista de Integracoes",
        "Analista de Identidade e Acessos",
        "Analista de Service Desk",
        "Desktop Support Analyst",
        "Field Support Analyst",
        "Analista Google Workspace",
        "Analista de Gestao de Ativos de TI",
        "Python Automation Junior",
        "Python Developer Junior",
        "Desenvolvedor Python Junior",
        "Junior Backend Developer (Python)",
        "Desenvolvedor Backend Python Jr",
    ],
)
def test_titulos_diretamente_alinhados_aos_curriculos_passam(titulo):
    vaga = {"titulo": titulo, "descricao": "", "modalidade": "Remoto"}
    assert calcular_score(vaga) >= 40


@pytest.mark.parametrize(
    "titulo",
    [
        "Identity Access Analyst",
        "Junior DevOps",
        "Tecnico de Help Desk",
        "Analista de Help Desk",
        "Service Desk Technician",
        "Python Backend Developer Jr",
        "Junior Backend Python Developer",
        "Desenvolvedor Back-end Python Junior",
        "Application Support Engineer",
        "L2 Support Engineer",
        "Especialista em Automacao Python",
        "Analista IAM - Seguranca da Informacao",
    ],
)
def test_variantes_reais_alinhadas_aos_curriculos_passam(titulo):
    vaga = {"titulo": titulo, "descricao": "", "modalidade": "Remoto"}
    assert calcular_score(vaga) >= 40


@pytest.mark.parametrize(
    "titulo",
    [
        "Senior IT Support Analyst",
        "IT Support Analyst III",
        "QA Automation Analyst",
        "Analista de Automacao Industrial",
        "Analista de Suporte ao Cliente",
        "Analista de Sistemas SAP",
        "Analista de Sistemas C# .NET",
        "Data Analyst - Python Automation",
    ],
)
def test_titulos_de_outra_senioridade_ou_familia_sao_bloqueados(titulo):
    vaga = {
        "titulo": titulo,
        "descricao": "Python REST API Docker Google Workspace Active Directory",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) == 0


@pytest.mark.parametrize(
    "titulo",
    [
        "Technical Writer",
        "Assistente Administrativo",
        "Product Analyst",
        "DevOps Engineer",
        "DevOps Pleno",
        "Python Developer Pleno",
        "Backend Python Developer Pleno",
        "Analista de Automacao - Manufatura Farmaceutica",
        "Analista de Suporte a Saude",
    ],
)
def test_descricao_rica_nao_aprova_familia_de_cargo_incorreta(titulo):
    vaga = {
        "titulo": titulo,
        "descricao": "Python REST API FastAPI Docker Git CI/CD SQL Active Directory Google Workspace PowerShell Zeev",
        "modalidade": "Remoto",
    }
    assert calcular_score(vaga) == 0


def test_coletores_com_listas_proprias_cobrem_os_dois_curriculos():
    linkedin_termos = {termo.lower() for termo, _local, _remoto in linkedin.BUSCAS}
    assert {
        "tecnico de suporte",
        "analista de service desk",
        "analista iam",
        "desktop support analyst",
        "python automation junior",
        "desenvolvedor python junior",
    } <= linkedin_termos

    assert {"tecnico de suporte", "analista de service desk", "analista iam"} <= {
        termo.lower() for termo in infojobs.TERMOS
    }
    assert {"desktop support analyst", "identity access analyst"} <= {
        termo.lower() for termo in himalayas.TERMOS_BUSCA
    }
    assert {"tecnico de suporte", "analista de service desk", "analista iam"} <= {
        termo.lower() for termo, _local in vagas_com.BUSCAS
    }
