# vagas/himalayas.py — API pública Himalayas (remotas globais)
# Docs: https://himalayas.app/jobs/api

import requests
import html
from vagas.base import HEADERS
import re

API_URL = "https://himalayas.app/jobs/api"

TERMOS_BUSCA = [
    "python automation",
    "integration analyst",
    "IT support analyst",
    "application support analyst",
    "desktop support analyst",
    "identity access analyst",
    "infrastructure analyst",
    "junior python backend",
    "junior devops",
    "junior systems administrator",
]

TERMOS_FILTRO = [
    "python", "devops", "backend", "automation", "infrastructure",
    "api", "support", "integr", "sysadmin", "identity access", "iam",
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

                restricoes = j.get("locationRestrictions") or []
                # A busca solicitada aceita oportunidades remotas internacionais.
                # A restricao continua visivel em `local`, para o candidato poder
                # avaliar elegibilidade antes de se inscrever.

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
                    "modalidade_confiavel": True,
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
    texto = html.unescape(str(texto or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()
