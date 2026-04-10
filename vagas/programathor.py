# vagas/programathor.py — scraping ProgramaThor (vagas tech Brasil)

import requests
from bs4 import BeautifulSoup
from vagas.base import HEADERS

BASE_URL = "https://programathor.com.br"
JOBS_URL  = f"{BASE_URL}/jobs"

TERMOS_TECH = [
    "python", "devops", "backend", "infraestrutura",
    "automacao", "suporte", "sre",
]


def buscar(locais: list[str]) -> list[dict]:
    vagas = {}

    for termo in TERMOS_TECH:
        for local in locais + ["remoto"]:
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

                    modalidade = _detectar_modalidade(titulo + " " + desc + " " + local)

                    vagas[vaga_url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local.title(),
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


def _detectar_modalidade(texto: str) -> str:
    t = texto.lower()
    if "remoto" in t or "home office" in t or "remote" in t:
        return "Remoto"
    if "hibrid" in t or "híbrid" in t:
        return "Hibrido"
    return "Presencial"
