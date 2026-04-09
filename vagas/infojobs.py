# vagas/infojobs.py — scraping InfoJobs Brasil

import requests
from bs4 import BeautifulSoup
from vagas.base import HEADERS

BASE_URL  = "https://www.infojobs.com.br"
BUSCA_URL = f"{BASE_URL}/empregos.aspx"

TERMOS = [
    "python automacao",
    "infraestrutura ti",
    "suporte tecnico python",
    "devops junior",
    "analista ti python",
    "backend python",
    "automacao processos",
]

LOCAIS = [
    "rio-de-janeiro",
    "",  # vazio = todo o Brasil (pega remotas também)
]


def buscar() -> list[dict]:
    vagas = {}

    for termo in TERMOS:
        for local in LOCAIS:
            try:
                params = {"palabra": termo}
                if local:
                    params["provincia"] = local

                r = requests.get(BUSCA_URL, params=params, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    continue

                soup  = BeautifulSoup(r.text, "html.parser")
                links = soup.select("a[href*='/vaga-de-']")

                for link in links:
                    href = link.get("href", "")
                    if not href:
                        continue

                    url = BASE_URL + href if href.startswith("/") else href
                    url = url.split("?")[0]
                    if url in vagas:
                        continue

                    titulo  = link.get_text(strip=True)
                    if not titulo or len(titulo) < 5:
                        continue

                    parent  = link.find_parent("li") or link.find_parent("div") or link.find_parent("article")
                    texto   = parent.get_text(" ", strip=True) if parent else titulo

                    empresa = _extrair_empresa(parent)
                    data    = _extrair_data(parent)
                    modalidade = _detectar_modalidade(titulo + " " + texto)

                    vagas[url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local.replace("-", " ").title() if local else "Brasil",
                        "modalidade": modalidade,
                        "url":        url,
                        "descricao":  texto[:1000],
                        "data":       data,
                        "plataforma": "InfoJobs",
                    }

            except Exception as e:
                print(f"[InfoJobs] erro em '{termo}' / '{local}': {e}")

    return list(vagas.values())


def _extrair_empresa(parent) -> str:
    if not parent:
        return ""
    for sel in [".company", ".empresa", "span[class*=company]", "span[class*=empresa]"]:
        el = parent.select_one(sel)
        if el:
            return el.get_text(strip=True)
    return ""


def _extrair_data(parent) -> str:
    if not parent:
        return ""
    for sel in ["time", "span[class*=date]", "span[class*=data]"]:
        el = parent.select_one(sel)
        if el:
            return el.get("datetime", "") or el.get_text(strip=True)
    return ""


def _detectar_modalidade(texto: str) -> str:
    t = texto.lower()
    if "home office" in t or "remoto" in t or "100% remoto" in t:
        return "Remoto"
    if "hibrid" in t or "híbrid" in t:
        return "Hibrido"
    return "Presencial"
