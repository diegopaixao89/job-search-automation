"""Perfis de busca sanitizados a partir dos curriculos Infra e Dev.

Este arquivo contem somente competencias profissionais. Os PDFs originais e
dados pessoais nao sao necessarios para a automacao local ou no GitHub Actions.
"""

TERMOS_BUSCA = [
    "analista de automacao",
    "analista de integracoes",
    "analista de suporte N2",
    "analista de infraestrutura",
    "analista de operacoes de TI",
    "analista de TI",
    "analista IAM",
    "analista de identidade e acessos",
    "analista de service desk",
    "desktop support analyst",
    "field support analyst",
    "tecnico de suporte",
    "administrador Google Workspace",
    "analista de gestao de ativos de TI",
    "application support analyst",
    "IT support analyst",
    "infrastructure analyst",
    "IT operations analyst",
    "python automation junior",
    "desenvolvedor python junior",
    "backend python junior",
    "devops junior",
    "junior systems administrator",
]


BLOQUEIOS_TITULO_COMUNS = (
    # Senioridade acima do nivel demonstrado nos curriculos.
    "senior", "sr", "lead", "staff", "principal", "architect", "arquiteto",
    "manager", "gerente", "coordinator", "coordenador", "head", "level 3",
    "nivel 3", "l3", "n3", "iii",
    # Familias de cargo diferentes, embora compartilhem palavras genericas.
    "qa analyst", "qa automation", "automation qa", "analista de qa", "quality assurance", "sdet", "test automation",
    "automacao de testes", "test engineer", "analista de testes",
    "automacao industrial", "industrial automation", "plc", "scada", "robotica",
    "manufatura", "manufacturing", "farmaceutica", "pharmaceutical",
    "customer support", "customer success", "call center", "suporte ao cliente",
    "suporte a saude", "health support",
    "marketing automation", "automacao de marketing",
    "data analyst", "analista de dados", "data scientist", "cientista de dados",
    "data engineer", "engenheiro de dados", "machine learning", "business intelligence",
    "cybersecurity", "soc analyst", "pentest",
    "frontend", "front end", "ui ux", "mobile developer",
    "sap", "sap analyst", "analista sap",
    "c#", ".net", "java developer", "desenvolvedor java", "php developer",
    "desenvolvedor php", "golang developer", "ruby developer",
)


PENALIZACOES_COMUNS = [
    (("senior", "sr", "senior engineer", "level 3", "l3", "n3", "iii"), -18, "titulo"),
    (("lead", "staff", "principal", "architect", "manager", "coordinator", "head"), -30, "titulo"),
    (("qa automation", "test automation", "sdet"), -30, "titulo"),
    (("automacao industrial", "industrial automation", "plc", "scada", "robotica"), -35, "texto"),
    (("marketing automation", "automacao de marketing", "crm automation"), -25, "titulo"),
    (("customer support", "customer success", "call center", "suporte comercial"), -30, "titulo"),
    (("frontend", "front end", "ui ux", "mobile developer"), -25, "titulo"),
    (("data scientist", "data engineer", "machine learning engineer", "bi developer"), -20, "titulo"),
    (("cybersecurity", "soc analyst", "pentest"), -20, "titulo"),
    (("java developer", "dotnet developer", "php developer", "golang developer", "ruby developer"), -18, "titulo"),
    (("c#", ".net", "java", "php", "golang", "ruby"), -18, "titulo"),
    (("native english", "fluent english", "ingles fluente", "ingles nativo"), -10, "texto"),
]


PERFIL_INFRA = {
    "NOME": "Infra e Suporte",
    "TITULO_GRUPOS": [
        (("analista de automacao", "automation analyst", "analista de integracao", "analista de integracoes", "integration analyst", "integrations analyst"), 40),
        (("analista de suporte n2", "analista de suporte", "it support analyst", "level 2 support"), 40),
        (("analista de infraestrutura", "infrastructure analyst", "infra analyst"), 40),
        (("analista de operacoes de ti", "it operations analyst", "it operations"), 38),
        (("analista iam", "iam analyst", "identity and access analyst", "identity access analyst", "analista de identidade e acessos", "gestao de acessos"), 38),
        (("administrador google workspace", "analista google workspace", "google workspace administrator", "google admin"), 38),
        (("analista de service desk", "service desk analyst", "service desk technician", "analista de help desk", "help desk analyst", "tecnico de help desk", "help desk technician", "desktop support analyst", "field support analyst"), 37),
        (("analista de gestao de ativos", "analista de ativos de ti", "it asset analyst", "asset management analyst"), 37),
        (("application support analyst", "systems support analyst", "analista de suporte a sistemas"), 37),
        (("application support engineer", "l2 support engineer", "level 2 support engineer", "support engineer l2"), 37),
        (("analista de ti", "analista de sistemas", "systems analyst"), 37),
        (("tecnico de suporte", "tecnico de infraestrutura", "it support technician", "infrastructure support technician"), 37),
        (("administrador de sistemas junior", "junior systems administrator", "sysadmin junior"), 32),
    ],
    "BLOQUEIOS_TITULO": BLOQUEIOS_TITULO_COMUNS,
    "DESCRICAO_GRUPOS": [
        (("python", "scripting", "automacao de processos", "process automation"), 10),
        (("api rest", "rest api", "apis rest", "integracao de sistemas", "system integration", "webhook"), 10),
        (("iam", "gestao de acessos", "identity and access", "active directory", "ldap"), 10),
        (("google workspace", "google admin", "admin sdk", "gsuite"), 10),
        (("suporte n1", "suporte n2", "n1 n2", "itsm", "service desk", "help desk", "helpdesk", "chamados", "tickets"), 9),
        (("zeev", "bpm", "glpi", "otrs", "totvs"), 8),
        (("powershell", "wpf"), 7),
        (("microsoft 365", "m365"), 6),
        (("ativos de ti", "gestao de ativos", "licencas", "asset management"), 6),
        (("docker", "git", "ci cd", "deployment"), 5),
        (("sql", "sqlite", "fastapi"), 4),
        (("retry", "backoff", "rate limit", "processamento paralelo", "threading"), 4),
        (("dashboard", "relatorio", "reporting"), 4),
    ],
    "DESCRICAO_LIMITE": 40,
    "AJUSTES_TITULO": [
        (("pleno", "pl", "mid level"), 8),
        (("junior", "jr"), 4),
    ],
    "PENALIZACOES_GRUPOS": PENALIZACOES_COMUNS,
    "BONUS_REMOTO": 4,
    "BONUS_HIBRIDO": 3,
    "BONUS_PRESENCIAL": 3,
}


PERFIL_DEV = {
    "NOME": "Automacao e Dev",
    "TITULO_GRUPOS": [
        (("analista de automacao", "automation analyst", "analista de integracao", "analista de integracoes", "integration analyst", "integrations analyst"), 40),
        (("desenvolvedor de automacao python", "python automation developer", "python automation junior", "junior python automation engineer", "automation engineer junior", "especialista em automacao python"), 38),
        (("backend python junior", "python backend junior", "junior python backend", "junior python developer", "python developer junior", "desenvolvedor python junior", "junior backend developer python", "junior backend python developer", "python backend developer jr", "python backend developer junior", "desenvolvedor backend python jr", "desenvolvedor backend python junior", "desenvolvedor back end python junior"), 36),
        (("devops junior", "junior devops", "junior devops engineer", "devops jr"), 34),
        (("administrador de sistemas junior", "junior systems administrator", "sysadmin junior"), 30),
        (("application support analyst", "systems support analyst"), 28),
        (("application support engineer", "l2 support engineer", "level 2 support engineer", "support engineer l2"), 36),
        (("python developer", "backend python", "back end python"), 26),
    ],
    "BLOQUEIOS_TITULO": BLOQUEIOS_TITULO_COMUNS + (
        "python developer pleno", "python developer pl", "backend python pleno",
        "backend python developer pleno", "desenvolvedor python pleno",
        "desenvolvedor backend python pleno",
    ),
    "DESCRICAO_GRUPOS": [
        (("python", "scripting", "automacao de processos", "process automation"), 12),
        (("api rest", "rest api", "apis rest", "integration", "webhook"), 10),
        (("docker", "container"), 8),
        (("git", "ci cd", "continuous integration", "deployment", "pipeline"), 7),
        (("fastapi", "backend", "back end", "sql", "sqlite"), 6),
        (("processamento paralelo", "threading", "retry", "backoff", "rate limit"), 5),
        (("google workspace", "active directory", "microsoft 365", "m365"), 6),
        (("powershell", "google apps script"), 5),
        (("zeev", "bpm", "glpi", "otrs", "totvs"), 4),
        (("llm", "gemini", "claude", "codex", "ia assistida"), 2),
    ],
    "DESCRICAO_LIMITE": 40,
    "AJUSTES_TITULO": [
        (("junior", "jr"), 8),
        (("pleno", "mid level"), -8),
    ],
    "PENALIZACOES_GRUPOS": PENALIZACOES_COMUNS,
    "BONUS_REMOTO": 4,
    "BONUS_HIBRIDO": 3,
    "BONUS_PRESENCIAL": 3,
}


PERFIS_BUSCA = {
    "infra": PERFIL_INFRA,
    "dev": PERFIL_DEV,
}


def _achatar_grupos(perfis: dict, chave: str) -> dict[str, int]:
    """Gera o formato legado usado pelo analisador de um unico CV."""
    resultado: dict[str, int] = {}
    for perfil in perfis.values():
        for termos, peso, *_ in perfil.get(chave, []):
            for termo in termos:
                resultado[termo] = max(resultado.get(termo, peso), peso)
    return resultado


TITULO_PESOS_COMPAT = _achatar_grupos(PERFIS_BUSCA, "TITULO_GRUPOS")
DESCRICAO_PESOS_COMPAT = _achatar_grupos(PERFIS_BUSCA, "DESCRICAO_GRUPOS")
PENALIZACOES_COMPAT = {
    termo: peso
    for termos, peso, _campo in PENALIZACOES_COMUNS
    for termo in termos
}
