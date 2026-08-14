# vagas/infojobs.py — scraping InfoJobs Brasil

import requests
from bs4 import BeautifulSoup
from filtros_vagas import detectar_modalidade, extrair_localizacao_anuncio
from vagas.base import HEADERS

BASE_URL  = "https://www.infojobs.com.br"
BUSCA_URL = f"{BASE_URL}/empregos.aspx"

TERMOS = [
    "analista de automacao",
    "analista de integracoes",
    "analista de suporte N2",
    "analista de infraestrutura",
    "analista de TI",
    "tecnico de suporte",
    "analista de service desk",
    "analista IAM",
    "devops junior",
    "backend python junior",
    "desenvolvedor python junior",
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

                    parent = (
                        link.find_parent(class_="js_rowCard")
                        or link.find_parent("li")
                        or link.find_parent("article")
                        or link.find_parent("div")
                    )
                    texto   = parent.get_text(" ", strip=True) if parent else titulo

                    empresa = _extrair_empresa(parent)
                    data    = _extrair_data(parent)
                    local_el = parent.select_one("div.mb-8") if parent else None
                    local_texto = local_el.get_text(" ", strip=True) if local_el else texto
                    local_real = extrair_localizacao_anuncio(local_texto, url)
                    modalidade = detectar_modalidade(titulo + " " + texto, local_real)

                    vagas[url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local_real,
                        "local_consulta": local.replace("-", " ").title() if local else "Brasil",
                        "local_confiavel": bool(local_real),
                        "modalidade": modalidade,
                        "url":        url,
                        "descricao":  texto[:1000],
                        "data":       data,
                        "plataforma": "InfoJobs",
                        "pais": "BR",
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
