# matcher.py — calcula score de aderencia de uma vaga ao perfil

from config import TITULO_PESOS, DESCRICAO_PESOS, PENALIZACOES, BONUS_REMOTO, BONUS_HIBRIDO

# Perfil ativo em runtime — substituido por curriculo_parser apos analise de CV.
# None = usa config.py como fallback.
_perfil_ativo: dict | None = None


def configurar_perfil(perfil: dict):
    """
    Define o perfil de scoring em runtime, derivado da analise do curriculo.
    Chamado por app.py apos o usuario aplicar o perfil do CV analisado.
    Thread-safe: chamado apenas do main thread antes de iniciar busca.
    """
    global _perfil_ativo
    _perfil_ativo = perfil


def _perfil() -> dict:
    """Retorna o perfil ativo ou constroi a partir do config.py."""
    if _perfil_ativo:
        return _perfil_ativo
    return {
        "TITULO_PESOS":    TITULO_PESOS,
        "DESCRICAO_PESOS": DESCRICAO_PESOS,
        "PENALIZACOES":    PENALIZACOES,
        "BONUS_REMOTO":    BONUS_REMOTO,
        "BONUS_HIBRIDO":   BONUS_HIBRIDO,
    }


def calcular_score(vaga: dict, perfil: dict | None = None) -> int:
    """
    Calcula score de 0-100 para uma vaga.
    perfil: dict opcional — se None, usa _perfil_ativo ou config.py.
    """
    p = perfil or _perfil()

    titulo    = vaga.get("titulo", "").lower()
    descricao = vaga.get("descricao", "").lower()
    texto     = titulo + " " + descricao

    score = 0
    for kw, peso in p["TITULO_PESOS"].items():
        if kw in titulo:
            score += peso
    for kw, peso in p["DESCRICAO_PESOS"].items():
        if kw in descricao:
            score += peso
    for kw, pen in p["PENALIZACOES"].items():
        if kw in texto:
            score += pen  # valor negativo

    modalidade = vaga.get("modalidade", "").lower()
    if "remot" in modalidade or "remote" in modalidade:
        score += p.get("BONUS_REMOTO", BONUS_REMOTO)
    elif "hibrid" in modalidade or "hybrid" in modalidade:
        score += p.get("BONUS_HIBRIDO", BONUS_HIBRIDO)

    return max(0, min(score, 100))


def keywords_encontradas(vaga: dict, perfil: dict | None = None) -> list[str]:
    """
    Retorna ate 8 keywords do perfil encontradas no titulo/descricao da vaga.
    Usado pelo notificador para exibir palavras-chave no digest.
    """
    p = perfil or _perfil()

    titulo    = vaga.get("titulo", "").lower()
    descricao = vaga.get("descricao", "").lower()

    encontradas = []
    todas_kw = list(p["TITULO_PESOS"].keys()) + list(p["DESCRICAO_PESOS"].keys())
    for kw in todas_kw:
        if kw in titulo or kw in descricao:
            if kw not in encontradas:
                encontradas.append(kw)
        if len(encontradas) >= 8:
            break
    return encontradas
