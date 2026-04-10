# vagas/remotive.py — API publica Remotive (vagas 100% remotas)
# Documentacao: https://remotive.com/api

import requests
from vagas.base import HEADERS

API_URL = "https://remotive.com/api/remote-jobs"

CATEGORIAS = [
    "software-dev",
    "devops-sysadmin",
]

TERMOS_FILTRO = [
    "python", "automation", "automacao", "devops", "backend",
    "infrastructure", "support", "sysadmin", "api",
]


def buscar(limite: int = 100) -> list[dict]:
    vagas = {}

    for categoria in CATEGORIAS:
        try:
            r = requests.get(
                API_URL,
                params={"category": categoria, "limit": limite},
                headers=HEADERS,
                timeout=15,
            )
            if r.status_code != 200:
                continue

            jobs = r.json().get("jobs", [])

            for j in jobs:
                url = j.get("url", "")
                if not url or url in vagas:
                    continue

                titulo = (j.get("title") or "").lower()
                desc = (j.get("description") or "").lower()
                texto = titulo + " " + desc

                if not any(t in texto for t in TERMOS_FILTRO):
                    continue

                vagas[url] = {
                    "titulo":     j.get("title", ""),
                    "empresa":    j.get("company_name", ""),
                    "local":      j.get("candidate_required_location", "Worldwide"),
                    "modalidade": "Remoto",
                    "url":        url,
                    "descricao":  _limpar_html(j.get("description", "")),
                    "data":       j.get("publication_date", ""),
                    "plataforma": "Remotive",
                    "pais": "WW",
                }

        except Exception as e:
            print(f"[Remotive] erro na categoria '{categoria}': {e}")

    return list(vagas.values())


def _limpar_html(texto: str) -> str:
    import re
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()
