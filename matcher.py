# matcher.py — calcula score de aderencia entre vaga e perfil

from config import (
    TITULO_PESOS, DESCRICAO_PESOS, PENALIZACOES,
    BONUS_REMOTO, BONUS_HIBRIDO
)


def calcular_score(vaga: dict) -> int:
    titulo = (vaga.get("titulo") or "").lower()
    descricao = (vaga.get("descricao") or "").lower()
    texto_completo = titulo + " " + descricao

    score = 0

    for kw, peso in TITULO_PESOS.items():
        if kw in titulo:
            score += peso

    for kw, peso in DESCRICAO_PESOS.items():
        if kw in descricao:
            score += peso

    for kw, pen in PENALIZACOES.items():
        if kw in texto_completo:
            score += pen  # pen e negativo

    modalidade = (vaga.get("modalidade") or "").lower()
    if "remoto" in modalidade or "remote" in modalidade or "remoto" in texto_completo:
        score += BONUS_REMOTO
    elif "hibrid" in modalidade or "hibrid" in texto_completo:
        score += BONUS_HIBRIDO

    return max(0, min(score, 100))


def keywords_encontradas(vaga: dict) -> list[str]:
    titulo = (vaga.get("titulo") or "").lower()
    descricao = (vaga.get("descricao") or "").lower()

    encontradas = []
    for kw in list(TITULO_PESOS) + list(DESCRICAO_PESOS):
        if kw in titulo or kw in descricao:
            if kw not in encontradas:
                encontradas.append(kw)
    return encontradas[:8]
