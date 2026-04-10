# vagas/weworkremotely.py — RSS We Work Remotely (100% remote, tech)

import requests
import xml.etree.ElementTree as ET
import re
from vagas.base import HEADERS

# Categorias tech relevantes para o perfil
RSS_URLS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
]

TERMOS_FILTRO = [
    "python", "devops", "backend", "back-end", "automation", "automacao",
    "infrastructure", "sre", "platform", "api", "support", "suporte",
    "integr", "cloud", "linux",
]


def buscar() -> list[dict]:
    vagas = {}

    for rss_url in RSS_URLS:
        try:
            r = requests.get(rss_url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue

            root  = ET.fromstring(r.content)
            items = root.findall(".//item")

            for item in items:
                tags  = {child.tag: (child.text or "").strip() for child in item}
                url   = tags.get("link", "")
                if not url or url in vagas:
                    continue

                titulo = tags.get("title", "")
                desc   = _limpar_html(tags.get("description", ""))
                regiao = tags.get("region", "")

                texto = (titulo + " " + desc + " " + regiao).lower()
                if not any(t in texto for t in TERMOS_FILTRO):
                    continue

                vagas[url] = {
                    "titulo":     titulo,
                    "empresa":    _extrair_empresa(titulo),
                    "local":      regiao or "Worldwide",
                    "modalidade": "Remoto",
                    "url":        url,
                    "descricao":  desc,
                    "data":       tags.get("pubDate", ""),
                    "plataforma": "WeWorkRemotely",
                    "pais": "WW",
                }

        except Exception as e:
            print(f"[WeWorkRemotely] erro em '{rss_url}': {e}")

    return list(vagas.values())


def _extrair_empresa(titulo: str) -> str:
    # Formato padrão: "Empresa: Título do Cargo"
    if ":" in titulo:
        return titulo.split(":")[0].strip()
    return ""


def _limpar_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()
