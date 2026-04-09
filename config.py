# config.py — perfil profissional + configuracoes da automacao

EMAIL_DESTINO    = "diegopaixao89@gmail.com"
EMAIL_REMETENTE  = "diegopaixao89@gmail.com"

CIDADE = "Rio de Janeiro"
ESTADO = "RJ"

LOCAIS_BUSCA = [
    "Rio de Janeiro",
    "Niteroi",
    "Grande Rio",
    "Regiao Metropolitana do Rio",
]

# Termos enviados para as plataformas de busca
TERMOS_BUSCA = [
    "python automacao",
    "suporte infraestrutura",
    "analista infraestrutura TI",
    "devops junior",
    "backend python",
    "analista TI",
    "automacao processos",
    "suporte tecnico N2",
    "administrador sistemas",
    "analista suporte",
    "python developer",
    "integracao sistemas",
    "tecnico TI",
    "engenheiro devops",
    "sre junior",
    "platform engineer",
    "python script",
    "automacao RPA",
]

# Score minimo para aparecer na interface
SCORE_MINIMO = 20

# ---------------------------------------------------------------------------
# Perfil completo — baseado no curriculo e nos projetos reais
# ---------------------------------------------------------------------------

# Palavras no TITULO — peso alto
TITULO_PESOS = {
    # Cargo / area
    "python":         25,
    "automacao":      25,
    "automação":      25,
    "automation":     25,
    "infraestrutura": 18,
    "infrastructure": 18,
    "suporte":        15,
    "support":        15,
    "devops":         18,
    "dev ops":        18,
    "backend":        18,
    "back-end":       18,
    "back end":       18,
    "sre":            15,
    "platform":       12,
    "analista":       10,
    "analyst":        10,
    "sistemas":        8,
    "systems":         8,
    "tecnico":        10,
    "technician":     10,
    "ti ":             8,
    "it ":             8,
    "cloud":           8,
    "linux":          10,
    "integra":        12,
    "script":         12,
    "rpa":            15,
    "engenheiro":     10,
    "engineer":       10,
    "administrador":  10,
    "administrator":  10,
}

# Palavras na DESCRICAO — peso menor
DESCRICAO_PESOS = {
    # Linguagens e ferramentas que usa
    "python":              15,
    "powershell":          12,
    "bash":                 8,
    "shell":                8,
    "script":              10,
    # APIs e integrações
    "api":                 10,
    "rest":                 8,
    "webhook":              8,
    "integracao":          10,
    "integração":          10,
    "integration":         10,
    # Google / Microsoft
    "google workspace":    12,
    "gsuite":              12,
    "g suite":             12,
    "active directory":    12,
    "microsoft 365":        8,
    "m365":                 8,
    "exchange":             6,
    "azure":                8,
    "entra":                8,
    # Infra / DevOps
    "docker":               8,
    "linux":                8,
    "windows server":       8,
    "ansible":              8,
    "terraform":            8,
    "kubernetes":           6,
    "ci/cd":                8,
    "pipeline":             6,
    "monitoramento":        6,
    "monitoring":           6,
    "zabbix":               6,
    "grafana":              6,
    # BD e dados
    "sql":                  5,
    "sqlite":               5,
    "banco de dados":       5,
    "database":             5,
    # Suporte / ITSM
    "chamados":             8,
    "tickets":              8,
    "itsm":                 8,
    "service desk":         8,
    "helpdesk":             8,
    "n2":                   6,
    "n3":                   6,
    "sla":                  6,
    "totvs":               10,
    # BPM / automação
    "zeev":                12,
    "bpm":                  8,
    "workflow":             8,
    "rpa":                 10,
    "automacao":           12,
    "automação":           12,
    # Dev
    "git":                  5,
    "github":               5,
    "gitlab":               5,
    "html":                 4,
    "django":               6,
    "flask":                6,
    "fastapi":              6,
    # IA / ferramentas modernas
    "llm":                  6,
    "openai":               5,
    "anthropic":            5,
    "ia aplicada":          6,
}

# Palavras que PENALIZAM (tecnologias fora do perfil atual)
PENALIZACOES = {
    "react":         -10,
    "angular":       -10,
    "vue":           -10,
    "next.js":       -10,
    "frontend":       -8,
    "front-end":      -8,
    "java":           -6,
    "kotlin":         -8,
    ".net":           -8,
    "c#":             -8,
    "ruby":           -8,
    "php":            -8,
    "golang":         -5,
    "rust":           -5,
    "machine learning": -5,
    "data science":   -8,
    "data scientist": -8,
    "bi developer":   -8,
    "salesforce":     -8,
    "sap":            -8,
    "r estatistica":  -8,
    "cobol":          -8,
    "embedded":       -8,
    "firmware":       -8,
    "mobile":         -5,
    "ios":            -8,
    "android":        -8,
}

# Bonus por modalidade
BONUS_REMOTO     = 15
BONUS_HIBRIDO    = 10
BONUS_PRESENCIAL =  0
