# tradutor.py — traducao automatica de titulos e descricoes para PT-BR
# Usa Google Translate via deep-translator (gratuito, sem chave de API)
# Cache em SQLite para nao re-traduzir o mesmo texto

import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "vagas_vistas.db")

_cache_mem: dict[str, str] = {}   # cache em memoria para a sessao


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS traducoes (
            hash TEXT PRIMARY KEY,
            original TEXT,
            traduzido TEXT
        )
    """)
    c.commit()
    return c


def _hash(texto: str) -> str:
    return hashlib.md5(texto.encode()).hexdigest()


def _do_cache(h: str) -> str | None:
    if h in _cache_mem:
        return _cache_mem[h]
    with _conn() as c:
        r = c.execute("SELECT traduzido FROM traducoes WHERE hash = ?", (h,)).fetchone()
        if r:
            _cache_mem[h] = r[0]
            return r[0]
    return None


def _salvar_cache(h: str, original: str, traduzido: str):
    _cache_mem[h] = traduzido
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO traducoes (hash, original, traduzido) VALUES (?,?,?)",
                  (h, original, traduzido))
        c.commit()


def _e_ingles(texto: str) -> bool:
    """Detecta se o texto e predominantemente em ingles."""
    try:
        from langdetect import detect
        return detect(texto[:200]) == "en"
    except Exception:
        # Fallback: checa palavras comuns em ingles
        palavras_en = {"the", "and", "for", "with", "you", "are", "will", "our", "we",
                       "join", "team", "role", "remote", "skills", "experience", "looking"}
        palavras = set(texto.lower().split())
        return len(palavras & palavras_en) >= 3


def traduzir(texto: str) -> str:
    """Traduz texto para PT-BR se estiver em ingles. Retorna o texto original se ja for PT."""
    if not texto or not texto.strip():
        return texto

    if not _e_ingles(texto):
        return texto   # ja esta em portugues

    h = _hash(texto[:500])  # hash dos primeiros 500 chars
    cached = _do_cache(h)
    if cached:
        return cached

    try:
        from deep_translator import GoogleTranslator
        # Limita o texto para evitar timeout (titulos sao curtos, descricoes podem ser longas)
        trecho = texto[:500]
        traduzido = GoogleTranslator(source="auto", target="pt").translate(trecho)
        if traduzido:
            _salvar_cache(h, trecho, traduzido)
            return traduzido
    except Exception:
        pass   # Se falhar, retorna o original sem travar

    return texto


def traduzir_vaga(vaga: dict) -> dict:
    """Traduz titulo e descricao de uma vaga. Retorna o dict modificado."""
    titulo_original = vaga.get("titulo", "")
    desc_original   = vaga.get("descricao", "")

    vaga["_titulo_original"] = titulo_original
    vaga["titulo"]           = traduzir(titulo_original)

    if desc_original:
        vaga["_desc_original"] = desc_original
        vaga["descricao"]      = traduzir(desc_original[:500])

    return vaga
