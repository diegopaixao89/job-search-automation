# vagas/linkedin.py — scraping LinkedIn Jobs (pagina publica, sem login)

import requests
import time
from bs4 import BeautifulSoup
from vagas.base import HEADERS

SEARCH_URL = "https://www.linkedin.com/jobs/search/"

# Pares (keywords, location) para cobrir remoto + Rio
BUSCAS = [
    ("python automacao",     "Rio de Janeiro, Brazil"),
    ("devops infraestrutura","Rio de Janeiro, Brazil"),
    ("suporte TI python",    "Rio de Janeiro, Brazil"),
    ("backend python",       "Rio de Janeiro, Brazil"),
    ("python automacao",     "Brazil"),          # pega remotas no Brasil todo
    ("devops junior",        "Brazil"),
    ("infraestrutura TI",    "Rio de Janeiro, Brazil"),
    ("analista sistemas",    "Rio de Janeiro, Brazil"),
]


def buscar() -> list[dict]:
    vagas = {}

    for keywords, location in BUSCAS:
        try:
            params = {
                "keywords": keywords,
                "location": location,
                "f_TPR": "r604800",   # ultima semana
                "sortBy": "DD",       # mais recentes
            }
            r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("div.base-card")

            for card in cards:
                link_el = card.select_one("a[href*='/jobs/view/']") or card.find("a", href=True)
                if not link_el:
                    continue

                url = _normalizar_url(link_el.get("href", ""))
                if not url or url in vagas:
                    continue

                titulo_el  = card.select_one("h3.base-search-card__title")
                empresa_el = card.select_one("h4.base-search-card__subtitle")
                local_el   = card.select_one("span.job-search-card__location")
                data_el    = card.select_one("time")

                titulo  = titulo_el.get_text(strip=True)  if titulo_el  else ""
                empresa = empresa_el.get_text(strip=True) if empresa_el else ""
                local   = local_el.get_text(strip=True)   if local_el   else location
                data    = data_el.get("datetime", "")      if data_el    else ""

                modalidade = _detectar_modalidade(titulo + " " + local)

                pais_vaga = "BR" if ("brazil" in local.lower() or "brasil" in local.lower()) else "WW"
                vagas[url] = {
                    "titulo":     titulo,
                    "empresa":    empresa,
                    "local":      local,
                    "modalidade": modalidade,
                    "url":        url,
                    "descricao":  "",
                    "data":       data,
                    "plataforma": "LinkedIn",
                    "pais":       pais_vaga,
                }

            time.sleep(1)  # pausa leve entre buscas

        except Exception as e:
            print(f"[LinkedIn] erro em '{keywords}' / '{location}': {e}")

    return list(vagas.values())


def _normalizar_url(href: str) -> str:
    import re
    url = href.split("?")[0]
    # Extrair o ID numerico do job para normalizar independente de subdominio
    m = re.search(r"/jobs/view/[^/]+-(\d{7,})", url)
    if m:
        return f"https://www.linkedin.com/jobs/view/{m.group(1)}"
    return url


def _detectar_modalidade(texto: str) -> str:
    t = texto.lower()
    if "remoto" in t or "remote" in t or "home office" in t:
        return "Remoto"
    if "hibrid" in t or "hybrid" in t:
        return "Hibrido"
    return "Presencial"
