# curriculo_parser.py — extrai texto do CV PDF e analisa com Google Gemini (gratuito)

import os
import json
import hashlib
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from banco import DB_PATH

# ---------------------------------------------------------------------------
# Skills conhecidas para fallback NLP local
# ---------------------------------------------------------------------------
_SKILLS_CONHECIDAS = [
    "python", "powershell", "bash", "linux", "windows server",
    "docker", "kubernetes", "ansible", "terraform", "ci/cd",
    "google workspace", "active directory", "microsoft 365", "azure", "aws",
    "rest api", "api", "webhook", "json", "sql", "sqlite", "postgresql", "mysql",
    "git", "github", "gitlab", "html", "css", "javascript",
    "django", "flask", "fastapi", "node.js",
    "zeev", "bpm", "totvs", "rpa", "automação", "automacao",
    "suporte", "infraestrutura", "devops", "sre", "platform engineering",
    "monitoramento", "zabbix", "grafana", "prometheus",
    "chatgpt", "claude", "llm", "ia", "openai",
    "customtkinter", "tkinter", "gui",
]

# ---------------------------------------------------------------------------
# Extração de texto do PDF
# ---------------------------------------------------------------------------

def extrair_texto_pdf(caminho_pdf: str) -> str:
    """Extrai texto de todas as páginas do PDF. Máx 8000 chars."""
    try:
        import pdfplumber
        texto_total = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto_total.append(t.strip())
        return "\n".join(texto_total)[:8000]
    except Exception as e:
        raise RuntimeError(f"Erro ao extrair texto do PDF: {e}")


# ---------------------------------------------------------------------------
# Cache SQLite
# ---------------------------------------------------------------------------

def _calcular_hash(caminho: str) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        h.update(f.read(524288))  # primeiros 512KB
    return h.hexdigest()


def _conn_cache():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS curriculo_cache (
            cv_hash TEXT PRIMARY KEY,
            cv_path TEXT,
            data_analise TEXT,
            texto_extraido TEXT,
            resultado_json TEXT
        )
    """)
    c.commit()
    return c


def _buscar_cache(cv_hash: str) -> dict | None:
    with _conn_cache() as c:
        r = c.execute(
            "SELECT resultado_json FROM curriculo_cache WHERE cv_hash = ?",
            (cv_hash,)
        ).fetchone()
        if r:
            try:
                return json.loads(r[0])
            except Exception:
                return None
    return None


def _salvar_cache(cv_hash: str, cv_path: str, texto: str, resultado: dict):
    with _conn_cache() as c:
        c.execute(
            """INSERT OR REPLACE INTO curriculo_cache
               (cv_hash, cv_path, data_analise, texto_extraido, resultado_json)
               VALUES (?,?,?,?,?)""",
            (cv_hash, cv_path, datetime.now().isoformat(), texto, json.dumps(resultado, ensure_ascii=False))
        )
        c.commit()


# ---------------------------------------------------------------------------
# Análise com Google Gemini (gratuito)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """Você é um coach de carreira especializado em TI.
Analise o currículo abaixo e responda APENAS com JSON válido, sem markdown, sem texto extra, sem blocos de código.
O JSON deve seguir EXATAMENTE este schema:
{
  "cargo_atual": "string — cargo mais recente/relevante",
  "habilidades": ["lista de até 20 habilidades técnicas"],
  "localizacao_extraida": "Cidade, UF — extraída do currículo",
  "anos_experiencia": 0,
  "nivel": "junior ou pleno ou senior",
  "termos_busca_sugeridos": ["15 termos para buscar vagas compatíveis com este perfil"],
  "titulo_pesos_sugeridos": {"keyword": 15},
  "descricao_pesos_sugeridos": {"keyword": 10},
  "penalizacoes_sugeridas": {"tecnologia_incompativel": -8},
  "dicas_melhoria": ["5 a 8 dicas concretas para melhorar o currículo"],
  "pontos_fortes": ["3 a 5 pontos fortes identificados"],
  "palavras_chave_ausentes": ["keywords importantes para o mercado que NÃO estão no currículo"]
}
Regras para os pesos:
- titulo_pesos_sugeridos: 12 a 20 entradas, valores entre 8 e 25
- descricao_pesos_sugeridos: 20 a 30 entradas, valores entre 4 e 15
- penalizacoes_sugeridas: 6 a 12 entradas com valores negativos entre -5 e -12"""


def analisar_com_gemini(texto_cv: str, api_key: str) -> dict:
    """Envia o texto do CV ao Gemini 2.5 Flash e retorna o JSON analisado."""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        resposta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Analise este currículo:\n\n{texto_cv}",
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=8000,
                response_mime_type="application/json",
            ),
        )
        texto_json = resposta.text.strip()
        return json.loads(texto_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini retornou JSON invalido: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro na chamada Gemini: {e}")


# ---------------------------------------------------------------------------
# Análise com Ollama (IA local, sem API key, sem internet)
# ---------------------------------------------------------------------------

# Modelos preferidos em ordem — o primeiro disponível será usado
_MODELOS_OLLAMA = [
    "llama3.2",
    "llama3.2:3b",
    "llama3.1",
    "gemma2",
    "gemma2:2b",
    "qwen2.5",
    "mistral",
    "phi3",
]

_OLLAMA_URL = "http://localhost:11434"


def _ollama_modelo_disponivel() -> str | None:
    """Retorna o nome do primeiro modelo Ollama disponível, ou None."""
    try:
        import requests as _req
        r = _req.get(f"{_OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code != 200:
            return None
        modelos = [m["name"] for m in r.json().get("models", [])]
        # Prefere modelos da lista, mas aceita qualquer um
        for pref in _MODELOS_OLLAMA:
            for m in modelos:
                if m.startswith(pref):
                    return m
        return modelos[0] if modelos else None
    except Exception:
        return None


def analisar_com_ollama(texto_cv: str) -> dict:
    """
    Envia o CV ao Ollama (IA 100% local).
    Requer Ollama rodando em localhost:11434 com pelo menos um modelo instalado.
    """
    import requests as _req

    modelo = _ollama_modelo_disponivel()
    if not modelo:
        raise RuntimeError("Ollama não está rodando ou nenhum modelo instalado.")

    payload = {
        "model":  modelo,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
        "messages": [
            {"role": "system",  "content": _SYSTEM_PROMPT},
            {"role": "user",    "content": f"Analise este currículo:\n\n{texto_cv}"},
        ],
    }
    r = _req.post(f"{_OLLAMA_URL}/api/chat", json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Ollama retornou status {r.status_code}")

    conteudo = r.json().get("message", {}).get("content", "")
    try:
        resultado = json.loads(conteudo)
        resultado["_modelo_ollama"] = modelo
        return resultado
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Ollama retornou JSON inválido: {e}")


# ---------------------------------------------------------------------------
# Fallback NLP local (sem API)
# ---------------------------------------------------------------------------

def _analisar_local(texto_cv: str) -> dict:
    """
    Analise sem API: extrai skills por keyword matching + dicas fixas.
    Menos detalhada mas 100% offline e sem custo.
    """
    txt = texto_cv.lower()

    habilidades = [s for s in _SKILLS_CONHECIDAS if s in txt]
    habilidades = list(dict.fromkeys(habilidades))[:20]  # dedup, max 20

    # Termos de busca baseados nas skills encontradas
    termos_mapa = {
        "python": ["python developer", "python automacao", "backend python"],
        "devops": ["devops junior", "engenheiro devops", "sre junior"],
        "docker": ["docker kubernetes", "platform engineer"],
        "linux": ["administrador linux", "sysadmin linux"],
        "google workspace": ["administrador google workspace"],
        "active directory": ["analista active directory"],
        "suporte": ["suporte tecnico N2", "analista suporte TI"],
        "infraestrutura": ["analista infraestrutura TI", "tecnico infraestrutura"],
        "rpa": ["automacao rpa", "desenvolvedor rpa"],
    }
    termos = []
    for skill, t in termos_mapa.items():
        if skill in txt:
            termos.extend(t)
    if not termos:
        termos = ["analista TI", "suporte tecnico", "python developer"]
    termos = list(dict.fromkeys(termos))[:15]

    # Extrair localização simples
    localizacao = "Rio de Janeiro, RJ"
    for cidade in ["são paulo", "rio de janeiro", "belo horizonte", "curitiba",
                   "porto alegre", "brasilia", "fortaleza", "recife", "salvador"]:
        if cidade in txt:
            localizacao = cidade.title() + ", BR"
            break

    dicas = [
        "Adicione métricas quantificadas aos projetos (ex: 'reduziu em 40% o tempo de...')",
        "Inclua link para repositório GitHub ou portfólio de projetos",
        "Detalhe o impacto de cada automação criada (número de usuários afetados, tempo economizado)",
        "Mencione certificações ou cursos relevantes concluídos recentemente",
        "Descreva o ambiente de cada empresa (tamanho da equipe, escala, tecnologias)",
        "Adicione um resumo profissional objetivo no início do currículo",
        "Inclua palavras-chave relevantes para sistemas de ATS (rastreamento de candidatos)",
    ]

    # Pesos básicos derivados das skills
    titulo_pesos = {"python": 25, "automacao": 20, "devops": 18, "suporte": 15,
                    "infraestrutura": 18, "backend": 18, "sre": 15, "engenheiro": 10}
    desc_pesos = {s: 10 for s in habilidades[:20]}
    penalizacoes = {"react": -10, "angular": -10, "java": -6, "mobile": -5,
                    "frontend": -8, ".net": -8, "data science": -8}

    return {
        "cargo_atual": "Analista / Técnico de TI",
        "habilidades": habilidades,
        "localizacao_extraida": localizacao,
        "anos_experiencia": 0,
        "nivel": "pleno",
        "termos_busca_sugeridos": termos,
        "titulo_pesos_sugeridos": titulo_pesos,
        "descricao_pesos_sugeridos": desc_pesos,
        "penalizacoes_sugeridas": penalizacoes,
        "dicas_melhoria": dicas,
        "pontos_fortes": ["Experiência prática com automações em Python",
                          "Familiaridade com ambiente Google Workspace e Active Directory",
                          "Projetos em produção com Docker e processamento paralelo"],
        "palavras_chave_ausentes": ["terraform", "ansible", "ci/cd", "prometheus", "grafana"],
        "_fonte": "local",
    }


# ---------------------------------------------------------------------------
# Orquestrador: Ollama → fallback local
# ---------------------------------------------------------------------------

def _tentar_ollama_ou_local(texto: str) -> dict:
    """Tenta Ollama local; se não disponível usa NLP local."""
    try:
        resultado = analisar_com_ollama(texto)
        resultado["_fonte"] = "ollama"
        print(f"[CurriculoParser] Ollama ok — modelo: {resultado.get('_modelo_ollama')}")
        return resultado
    except Exception as e:
        print(f"[CurriculoParser] Ollama indisponível ({e}), usando análise local")
        return _analisar_local(texto)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def analisar_curriculo(caminho_pdf: str, forcar_reanalise: bool = False) -> dict:
    """
    Analisa o currículo PDF.
    1. Verifica cache por hash MD5 do arquivo
    2. Se cache inválido ou forcar_reanalise=True: extrai texto e analisa
    3. Usa Gemini se GEMINI_API_KEY estiver no .env, senão fallback local
    Retorna dict com o resultado completo.
    """
    if not os.path.isfile(caminho_pdf):
        raise FileNotFoundError(f"PDF não encontrado: {caminho_pdf}")

    cv_hash = _calcular_hash(caminho_pdf)

    if not forcar_reanalise:
        cached = _buscar_cache(cv_hash)
        if cached:
            cached["_cache"] = True
            return cached

    texto = extrair_texto_pdf(caminho_pdf)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    # Chave do usuário tem prioridade; chave padrão garante que a IA funcione sem configuração
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or "AIzaSyA3g687YgcuNqlr2MVIrM0OaPnuS2YIHjU"

    try:
        resultado = analisar_com_gemini(texto, api_key)
        resultado["_fonte"] = "gemini"
    except Exception as e:
        print(f"[CurriculoParser] Gemini falhou ({e}), tentando Ollama...")
        resultado = _tentar_ollama_ou_local(texto)

    _salvar_cache(cv_hash, caminho_pdf, texto, resultado)
    return resultado


def resultado_para_perfil(resultado: dict) -> dict:
    """
    Converte o resultado da análise no formato de perfil do matcher.py.
    Merge com config.py para garantir que campos ausentes tenham valores.
    """
    from config import TITULO_PESOS, DESCRICAO_PESOS, PENALIZACOES, BONUS_REMOTO, BONUS_HIBRIDO

    return {
        "TITULO_PESOS":    resultado.get("titulo_pesos_sugeridos") or TITULO_PESOS,
        "DESCRICAO_PESOS": resultado.get("descricao_pesos_sugeridos") or DESCRICAO_PESOS,
        "PENALIZACOES":    resultado.get("penalizacoes_sugeridas") or PENALIZACOES,
        "BONUS_REMOTO":    BONUS_REMOTO,
        "BONUS_HIBRIDO":   BONUS_HIBRIDO,
    }


# ---------------------------------------------------------------------------
# Teste direto
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import glob
    pdfs = glob.glob(os.path.join(os.path.expanduser("~"), "Desktop", "Projetos IA", "*.pdf"))
    if not pdfs:
        print("Nenhum PDF encontrado em Desktop/Projetos IA/")
        sys.exit(1)
    caminho = pdfs[0]
    print(f"Analisando: {caminho}")
    resultado = analisar_curriculo(caminho, forcar_reanalise=True)
    fonte = resultado.get("_fonte", "?")
    cache = resultado.get("_cache", False)
    print(f"Fonte: {fonte}  |  Cache: {cache}")
    print(f"Cargo: {resultado.get('cargo_atual')}")
    print(f"Habilidades: {resultado.get('habilidades', [])[:10]}")
    print(f"Localizacao: {resultado.get('localizacao_extraida')}")
    print(f"\nDicas de melhoria:")
    for i, d in enumerate(resultado.get("dicas_melhoria", []), 1):
        print(f"  {i}. {d}")
    print(f"\nPalavras ausentes: {resultado.get('palavras_chave_ausentes')}")
