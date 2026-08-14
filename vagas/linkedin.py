# vagas/linkedin.py — scraping LinkedIn Jobs (pagina publica, sem login)

import requests
import time
from bs4 import BeautifulSoup
from filtros_vagas import detectar_modalidade
from vagas.base import HEADERS

SEARCH_URL = "https://www.linkedin.com/jobs/search/"

# Triplas (keywords, location, somente_remoto) para cobrir Rio + exterior.
BUSCAS = [
    ("analista de automacao",       "Rio de Janeiro, Brazil", False),
    ("analista de integracoes",     "Rio de Janeiro, Brazil", False),
    ("analista de suporte N2",      "Rio de Janeiro, Brazil", False),
    ("analista de infraestrutura",  "Rio de Janeiro, Brazil", False),
    ("tecnico de suporte",          "Rio de Janeiro, Brazil", False),
    ("analista de service desk",    "Rio de Janeiro, Brazil", False),
    ("analista de TI",              "Rio de Janeiro, Brazil", False),
    ("analista IAM",                "Rio de Janeiro, Brazil", False),
    ("IT support analyst",          "Worldwide", True),
    ("application support analyst", "Worldwide", True),
    ("desktop support analyst",      "Worldwide", True),
    ("identity access analyst",      "Worldwide", True),
    ("python automation junior",    "Worldwide", True),
    ("backend python junior",       "Worldwide", True),
    ("desenvolvedor python junior", "Worldwide", True),
    ("devops junior",               "Worldwide", True),
]


def buscar() -> list[dict]:
    vagas = {}

    for keywords, location, somente_remoto in BUSCAS:
        try:
            params = {
                "keywords": keywords,
                "location": location,
                "f_TPR": "r604800",   # ultima semana
                "sortBy": "DD",       # mais recentes
            }
            if somente_remoto:
                params["f_WT"] = "2"
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
                local   = local_el.get_text(strip=True)   if local_el   else ""
                data    = data_el.get("datetime", "")      if data_el    else ""

                modalidade = "Remoto" if somente_remoto else detectar_modalidade(titulo, local)

                referencia_pais = (local or location).lower()
                pais_vaga = "BR" if ("brazil" in referencia_pais or "brasil" in referencia_pais) else "WW"
                vagas[url] = {
                    "titulo":     titulo,
                    "empresa":    empresa,
                    "local":      local,
                    "local_consulta": location,
                    "local_confiavel": bool(local_el),
                    "modalidade": modalidade,
                    "modalidade_confiavel": bool(local_el) or somente_remoto,
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
