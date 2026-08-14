# vagas/indeed.py — integracao opcional com o antigo RSS do Indeed Brasil.
# O endpoint esta protegido por Cloudflare e a fonte fica desativada por padrao;
# nao tentamos contornar mecanismos de acesso do site.

import os
import html
import requests
import xml.etree.ElementTree as ET
from filtros_vagas import detectar_modalidade, extrair_localizacao_anuncio
from vagas.base import HEADERS

RSS_URL = "https://br.indeed.com/rss"


def buscar(termos: list[str], locais: list[str], limite_por_combo: int = 15) -> list[dict]:
    if os.getenv("ENABLE_INDEED", "false").strip().lower() not in {"1", "true", "yes", "sim"}:
        print("[Indeed] fonte desativada por padrao; use apenas com acesso autorizado.")
        return []

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
                    print(f"[Indeed] RSS indisponivel (HTTP {r.status_code}); fonte interrompida.")
                    return []

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

                    descricao = _limpar_html(desc)
                    local_real = extrair_localizacao_anuncio(titulo + " " + descricao, url)
                    modalidade = detectar_modalidade(titulo + " " + descricao, local_real)

                    vagas[url] = {
                        "titulo":     titulo,
                        "empresa":    empresa,
                        "local":      local_real,
                        "local_consulta": local,
                        "local_confiavel": bool(local_real),
                        "modalidade": modalidade,
                        "url":        url,
                        "descricao":  descricao,
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
    texto = html.unescape(str(texto or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto[:2000].strip()
