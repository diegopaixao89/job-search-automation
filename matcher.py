# matcher.py — calcula score de aderencia de uma vaga aos perfis dos curriculos

import re

from config import (
    BONUS_HIBRIDO,
    BONUS_PRESENCIAL,
    BONUS_REMOTO,
    DESCRICAO_PESOS,
    PENALIZACOES,
    TITULO_PESOS,
)
from filtros_vagas import normalizar_texto
from perfis_busca import BLOQUEIOS_TITULO_COMUNS, PERFIS_BUSCA

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


def _perfil_legado() -> dict:
    """Constroi o formato usado pela analise interativa de um unico CV."""
    return {
        "TITULO_PESOS":    TITULO_PESOS,
        "DESCRICAO_PESOS": DESCRICAO_PESOS,
        "PENALIZACOES":    PENALIZACOES,
        "BONUS_REMOTO":    BONUS_REMOTO,
        "BONUS_HIBRIDO":   BONUS_HIBRIDO,
        "BONUS_PRESENCIAL": BONUS_PRESENCIAL,
    }


def _contem(texto_normalizado: str, termo: str) -> bool:
    termo_n = normalizar_texto(termo)
    if not termo_n:
        return False
    return bool(re.search(rf"(?<!\w){re.escape(termo_n)}(?!\w)", texto_normalizado))


def _modalidade(vaga: dict) -> str:
    modalidade = normalizar_texto(vaga.get("modalidade", ""))
    if modalidade in {"remoto", "remote"}:
        return "Remoto"
    if modalidade in {"hibrido", "hybrid"}:
        return "Hibrido"
    return "Presencial"


def _calcular_legado(vaga: dict, perfil: dict) -> int:
    titulo = normalizar_texto(vaga.get("titulo", ""))
    descricao = normalizar_texto(vaga.get("descricao", ""))
    texto = f"{titulo} {descricao}".strip()

    if any(_contem(titulo, termo) for termo in BLOQUEIOS_TITULO_COMUNS):
        return 0

    score_titulo = 0
    for kw, peso in perfil.get("TITULO_PESOS", {}).items():
        if _contem(titulo, kw):
            score_titulo += peso
    if score_titulo == 0:
        return 0

    score = score_titulo
    for kw, peso in perfil.get("DESCRICAO_PESOS", {}).items():
        if _contem(descricao, kw):
            score += peso
    for kw, penalizacao in perfil.get("PENALIZACOES", {}).items():
        if _contem(texto, kw):
            score += penalizacao

    modalidade = _modalidade(vaga)
    if modalidade == "Remoto":
        score += perfil.get("BONUS_REMOTO", BONUS_REMOTO)
    elif modalidade == "Hibrido":
        score += perfil.get("BONUS_HIBRIDO", BONUS_HIBRIDO)
    else:
        score += perfil.get("BONUS_PRESENCIAL", 0)

    return max(0, min(score, 100))


def _maior_grupo(grupos: list, texto: str) -> int:
    return max(
        (peso for termos, peso, *_ in grupos if any(_contem(texto, termo) for termo in termos)),
        default=0,
    )


def _somar_grupos(grupos: list, texto: str, limite: int | None = None) -> int:
    total = sum(
        peso
        for termos, peso, *_ in grupos
        if any(_contem(texto, termo) for termo in termos)
    )
    return min(total, limite) if limite is not None else total


def _calcular_por_grupos(vaga: dict, perfil: dict) -> int:
    titulo = normalizar_texto(vaga.get("titulo", ""))
    descricao = normalizar_texto(vaga.get("descricao", ""))
    texto = f"{titulo} {descricao}".strip()

    if any(_contem(titulo, termo) for termo in perfil.get("BLOQUEIOS_TITULO", ())):
        return 0

    score_titulo = _maior_grupo(perfil.get("TITULO_GRUPOS", []), titulo)
    # Competencias na descricao refinam uma familia de cargo reconhecida, mas
    # nunca fazem um cargo sem relacao atingir o corte sozinho.
    if score_titulo == 0:
        return 0
    score_descricao = _somar_grupos(
        perfil.get("DESCRICAO_GRUPOS", []),
        descricao,
        perfil.get("DESCRICAO_LIMITE", 40),
    )
    score_tecnico = score_titulo + score_descricao

    # Modalidade nunca transforma uma vaga sem aderencia tecnica em relevante.
    if score_tecnico == 0:
        return 0

    score = score_tecnico
    score += _somar_grupos(perfil.get("AJUSTES_TITULO", []), titulo)

    for termos, peso, campo in perfil.get("PENALIZACOES_GRUPOS", []):
        alvo = titulo if campo == "titulo" else texto
        if any(_contem(alvo, termo) for termo in termos):
            score += peso

    modalidade = _modalidade(vaga)
    if modalidade == "Remoto":
        score += perfil.get("BONUS_REMOTO", BONUS_REMOTO)
    elif modalidade == "Hibrido":
        score += perfil.get("BONUS_HIBRIDO", BONUS_HIBRIDO)
    else:
        score += perfil.get("BONUS_PRESENCIAL", BONUS_PRESENCIAL)

    return max(0, min(score, 100))


def calcular_score(vaga: dict, perfil: dict | None = None) -> int:
    """Calcula score 0-100; por padrao usa a melhor das trilhas Infra e Dev."""
    if perfil is not None:
        if "TITULO_GRUPOS" in perfil:
            return _calcular_por_grupos(vaga, perfil)
        return _calcular_legado(vaga, perfil)

    perfis = list(PERFIS_BUSCA.values())
    if _perfil_ativo:
        perfis.append(_perfil_ativo)
    return max(calcular_score(vaga, p) for p in perfis)


def calcular_aderencia(vaga: dict) -> dict:
    """Retorna score final, trilha vencedora e scores individuais."""
    scores = {chave: calcular_score(vaga, perfil) for chave, perfil in PERFIS_BUSCA.items()}
    if _perfil_ativo:
        scores["cv"] = calcular_score(vaga, _perfil_ativo)
    melhor = max(scores, key=scores.get)
    nomes = {chave: perfil["NOME"] for chave, perfil in PERFIS_BUSCA.items()}
    nomes["cv"] = "CV analisado"
    return {
        "score": scores[melhor],
        "perfil_match": nomes[melhor],
        "scores": scores,
    }


def pontuar_vaga(vaga: dict) -> dict:
    """Anexa a aderencia ao dicionario da vaga e o devolve."""
    aderencia = calcular_aderencia(vaga)
    vaga["score"] = aderencia["score"]
    vaga["perfil_match"] = aderencia["perfil_match"]
    vaga["score_infra"] = aderencia["scores"].get("infra", 0)
    vaga["score_dev"] = aderencia["scores"].get("dev", 0)
    return vaga


def keywords_encontradas(vaga: dict, perfil: dict | None = None) -> list[str]:
    """
    Retorna ate 8 keywords do perfil encontradas no titulo/descricao da vaga.
    Usado pelo notificador para exibir palavras-chave no digest.
    """
    titulo = normalizar_texto(vaga.get("titulo", ""))
    descricao = normalizar_texto(vaga.get("descricao", ""))
    texto = f"{titulo} {descricao}".strip()

    if perfil is None:
        aderencia = calcular_aderencia(vaga)
        chave = max(aderencia["scores"], key=aderencia["scores"].get)
        perfil = _perfil_ativo if chave == "cv" else PERFIS_BUSCA.get(chave, _perfil_legado())

    if "TITULO_GRUPOS" in perfil:
        grupos = perfil.get("TITULO_GRUPOS", []) + perfil.get("DESCRICAO_GRUPOS", [])
        termos = [
            termo
            for grupo, _peso, *_ in grupos
            for termo in grupo
            if _contem(texto, termo)
        ]
    else:
        termos = [
            termo
            for termo in (
                list(perfil.get("TITULO_PESOS", {}))
                + list(perfil.get("DESCRICAO_PESOS", {}))
            )
            if _contem(texto, termo)
        ]

    unicas = []
    for termo in termos:
        if termo not in unicas:
            unicas.append(termo)
        if len(unicas) == 8:
            break
    return unicas
