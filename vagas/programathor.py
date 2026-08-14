# vagas/programathor.py — scraping ProgramaThor (vagas tech Brasil)

import requests
from bs4 import BeautifulSoup
from filtros_vagas import detectar_modalidade, extrair_localizacao_anuncio
from vagas.base import HEADERS

BASE_URL = "https://programathor.com.br"
JOBS_URL  = f"{BASE_URL}/jobs"

TERMOS_TECH = [
    "python", "devops junior", "backend python", "infraestrutura",
    "automacao", "integracao", "suporte",
]


def buscar(locais: list[str]) -> list[dict]:
    vagas = {}

    locais_unicos = list(dict.fromkeys([*locais, "remoto"]))
    for termo in TERMOS_TECH:
        for local in locais_unicos:
            try:
                params = {"search": termo, "location": local}
                r = requests.get(JOBS_URL, params=params, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    continue

                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.select("div.cell-list") or soup.select("article.job-card")

                for card in cards:
                    link_el = card.select_one("a[href*='/jobs/']")
                    if not link_el:
                        continue

                    href = link_el.get("href", "")
                    vaga_url = BASE_URL + href if href.startswith("/") else href
                    if not vaga_url or vaga_url in vagas:
                        continue

                    titulo_el = card.select_one("h2") or card.select_one("h3") or link_el
                    titulo = titulo_el.get_text(strip=True)

                    empresa_el = card.select_one(".company-name") or card.select_one("span.tag-list")
                    empresa = empresa_el.get_text(strip=True) if empresa_el else ""

                    desc_el = card.select_one(".description") or card.select_one("p")
                    desc = desc_el.get_text(" ", strip=True) if desc_el else ""
                    texto_card = card.get_text(" ", strip=True)

                    local_real = extrair_localizacao_anuncio(texto_card, vaga_url)
                    modalidade = detectar_modalidade(titulo + " " + texto_card, local_real)

                    vagas[vaga_url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local_real,
                        "local_consulta": local.title(),
                        "local_confiavel": bool(local_real),
                        "modalidade": modalidade,
                        "url":        vaga_url,
                        "descricao":  desc[:2000],
                        "data":       "",
                        "plataforma": "ProgramaThor",
                        "pais": "BR",
                    }

            except Exception as e:
                print(f"[ProgramaThor] erro em '{termo}' / '{local}': {e}")

    return list(vagas.values())
