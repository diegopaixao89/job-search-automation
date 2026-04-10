# vagas/himalayas.py — API pública Himalayas (remotas globais)
# Docs: https://himalayas.app/jobs/api

import requests
from vagas.base import HEADERS
import re

API_URL = "https://himalayas.app/jobs/api"

TERMOS_BUSCA = [
    "python automation",
    "python devops",
    "backend python",
    "infrastructure engineer",
    "python developer",
    "devops engineer",
    "sre python",
    "support engineer python",
]

TERMOS_FILTRO = [
    "python", "devops", "backend", "automation", "infrastructure",
    "sre", "platform", "api", "support", "integr", "cloud", "linux",
]


def buscar(limite_por_termo: int = 20) -> list[dict]:
    vagas = {}

    for termo in TERMOS_BUSCA:
        try:
            params = {"q": termo, "limit": limite_por_termo}
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue

            jobs = r.json().get("jobs", [])

            for j in jobs:
                url = j.get("guid") or j.get("applicationLink") or ""
                if not url or url in vagas:
                    continue

                # Filtro de localização: manter vagas abertas ao Brasil ou worldwide
                restricoes = j.get("locationRestrictions") or []
                if restricoes and "Brazil" not in restricoes and "Worldwide" not in restricoes:
                    # Aceitar também se não tem restrição (lista vazia = worldwide)
                    continue

                titulo = j.get("title", "")
                desc   = _limpar_html(j.get("description") or j.get("excerpt") or "")

                texto = (titulo + " " + desc).lower()
                if not any(t in texto for t in TERMOS_FILTRO):
                    continue

                local = ", ".join(restricoes) if restricoes else "Worldwide"
                pais = "BR" if "Brazil" in restricoes else "WW"

                vagas[url] = {
                    "titulo":     titulo,
                    "empresa":    j.get("companyName", ""),
                    "local":      local,
                    "modalidade": "Remoto",
                    "url":        url,
                    "descricao":  desc,
                    "data":       str(j.get("pubDate", "")),
                    "plataforma": "Himalayas",
                    "pais":       pais,
                }

        except Exception as e:
            print(f"[Himalayas] erro no termo '{termo}': {e}")

    return list(vagas.values())


def _limpar_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()
