# vagas/indeed.py — RSS feed publico Indeed Brasil

import requests
import xml.etree.ElementTree as ET
from vagas.base import HEADERS

RSS_URL = "https://br.indeed.com/rss"


def buscar(termos: list[str], locais: list[str], limite_por_combo: int = 15) -> list[dict]:
    vagas = {}

    for termo in termos:
        for local in locais:
            try:
                params = {
                    "q":    termo,
                    "l":    local,
                    "sort": "date",
                    "limit": limite_por_combo,
                }
                r = requests.get(RSS_URL, params=params, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    continue

                root = ET.fromstring(r.content)
                items = root.findall(".//item")

                for item in items:
                    url = _tag(item, "link") or _tag(item, "guid") or ""
                    if not url or url in vagas:
                        continue

                    titulo = _tag(item, "title") or ""
                    desc = _tag(item, "description") or ""
                    empresa = _tag(item, "source") or ""
                    data = _tag(item, "pubDate") or ""

                    modalidade = _detectar_modalidade(titulo + " " + desc)

                    vagas[url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local,
                        "modalidade": modalidade,
                        "url":        url,
                        "descricao":  _limpar_html(desc),
                        "data":       data,
                        "plataforma": "Indeed",
                    }

            except Exception as e:
                print(f"[Indeed] erro em '{termo}' / '{local}': {e}")

    return list(vagas.values())


def _tag(el, name: str) -> str:
    child = el.find(name)
    return (child.text or "").strip() if child is not None else ""


def _limpar_html(texto: str) -> str:
    import re
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()


def _detectar_modalidade(texto: str) -> str:
    t = texto.lower()
    if "remoto" in t or "home office" in t or "100% remoto" in t:
        return "Remoto"
    if "hibrid" in t or "híbrid" in t:
        return "Hibrido"
    return "Presencial"
