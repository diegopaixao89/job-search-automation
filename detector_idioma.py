# detector_idioma.py — deteccao de idioma e sinalizacao de requisitos de idioma

import re

# ---------------------------------------------------------------------------
# Deteccao de idioma (fast-langdetect)
# ---------------------------------------------------------------------------

def detectar_idioma(texto: str) -> str:
    """
    Detecta o idioma do texto usando fast-langdetect.
    Retorna codigo ISO 639-1: 'pt', 'en', 'es', etc.
    Fallback: 'pt' em caso de erro ou texto muito curto.
    """
    if not texto or len(texto.strip()) < 20:
        return "pt"
    try:
        from fast_langdetect import detect
        resultado = detect(texto[:400], low_memory=True)
        return resultado.get("lang", "pt").lower()
    except Exception:
        return _detectar_por_heuristica(texto)


def _detectar_por_heuristica(texto: str) -> str:
    """Fallback sem dependencias externas."""
    t = texto.lower()
    palavras_en = ["the", "and", "for", "with", "you", "are", "this",
                   "have", "will", "our", "your", "we're", "we are",
                   "experience", "skills", "team", "role", "join us"]
    palavras_pt = ["para", "com", "que", "uma", "por", "nos", "voce",
                   "experiencia", "habilidades", "equipe", "vaga", "empresa"]
    score_en = sum(1 for w in palavras_en if w in t)
    score_pt = sum(1 for w in palavras_pt if w in t)
    return "en" if score_en > score_pt else "pt"


# ---------------------------------------------------------------------------
# Deteccao de idioma obrigatorio na descricao
# ---------------------------------------------------------------------------

_PADROES_INGLES_OBRIGATORIO = [
    r"\bfluent\s+(?:in\s+)?english\b",
    r"\bfluency\s+in\s+english\b",
    r"\badvanced\s+english\b",
    r"\bprofessional\s+english\b",
    r"\bnative\s+english\b",
    r"\bfull\s+professional\s+proficiency\b",
    r"\bingl[eê]s\s+avan[cç]ado\b",
    r"\bingl[eê]s\s+fluente\b",
    r"\bflu[eê]ncia\s+em\s+ingl[eê]s\b",
    r"\bdomin[ií]o\s+(?:do\s+)?ingl[eê]s\b",
    r"\brequer.*ingl[eê]s",
    r"\brequired.*english",
    r"\benglish.*required",
    r"\bmust.*english",
    r"\bnecessita.*ingl[eê]s",
]

_PADROES_ESPANHOL_OBRIGATORIO = [
    r"\bespañol\s+fluido\b",
    r"\bespanhol\s+avan[cç]ado\b",
    r"\bespanhol\s+fluente\b",
    r"\bflu[eê]ncia\s+em\s+espanhol\b",
]

_RE_EN = re.compile("|".join(_PADROES_INGLES_OBRIGATORIO), re.IGNORECASE)
_RE_ES = re.compile("|".join(_PADROES_ESPANHOL_OBRIGATORIO), re.IGNORECASE)


def detectar_idioma_obrigatorio(descricao: str) -> str | None:
    """
    Verifica se a descricao exige fluencia em outro idioma.
    Retorna 'en', 'es', ou None.
    """
    if not descricao:
        return None
    if _RE_EN.search(descricao):
        return "en"
    if _RE_ES.search(descricao):
        return "es"
    return None


# ---------------------------------------------------------------------------
# Enriquecimento do dict de vaga
# ---------------------------------------------------------------------------

def enriquecer_vaga(vaga: dict) -> dict:
    """
    Adiciona vaga['idioma'] e vaga['idioma_obrigatorio'] ao dict.
    Nao modifica outros campos. Retorna o mesmo dict modificado.
    """
    titulo = vaga.get("titulo", "")
    descricao = vaga.get("descricao", "")
    texto = f"{titulo} {descricao}".strip()

    vaga["idioma"] = detectar_idioma(texto)
    vaga["idioma_obrigatorio"] = detectar_idioma_obrigatorio(descricao)
    return vaga


# ---------------------------------------------------------------------------
# Teste direto
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    testes = [
        ("Python Developer - Remote - Join our amazing team!", "We're looking for a fluent English speaker."),
        ("Analista de Infraestrutura Python", "Experiencia com Docker e Linux. Ingles avancado obrigatorio."),
        ("DevOps Engineer - Automacao", "Trabalhamos com Python, Ansible e Terraform. Ingles intermediario desejavel."),
        ("Backend Developer", "Must have advanced English for daily communication with international teams."),
        ("Tecnico de Suporte N2", "Experiencia em Active Directory e Windows Server."),
    ]
    print("Teste detector_idioma.py\n" + "=" * 40)
    for titulo, desc in testes:
        v = {"titulo": titulo, "descricao": desc}
        enriquecer_vaga(v)
        print(f"Titulo:    {titulo[:55]}")
        print(f"Idioma:    {v['idioma']}  |  Obrigatorio: {v['idioma_obrigatorio']}")
        print()
