# vagas/gupy.py — endpoint publico usado pelo portal de candidatos da Gupy.
# Nao e a API corporativa documentada (que exige Bearer token); por isso uma
# mudanca de rota/esquema deve falhar com aviso claro e sem varias tentativas.

import html
import re
import requests
from vagas.base import HEADERS

API_URL = "https://employability-portal.gupy.io/api/v1/jobs"


def buscar(termos: list[str], limite_por_termo: int = 30) -> list[dict]:
    vagas = {}

    for termo in termos:
        try:
            params = {"jobName": termo, "limit": limite_por_termo, "offset": 0}
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"[Gupy] endpoint indisponivel (HTTP {r.status_code}); fonte interrompida.")
                return []

            payload = r.json()
            jobs = payload.get("data", [])
            if not isinstance(jobs, list):
                print("[Gupy] resposta sem a lista 'data'; fonte interrompida.")
                return []

            for j in jobs:
                url = j.get("jobUrl") or ""
                if not url or url in vagas:
                    continue

                # Pula empresas inativas (URL com "inactive" no subdomínio)
                try:
                    from urllib.parse import urlparse
                    host = urlparse(url).hostname or ""
                    if "inactive" in host:
                        continue
                except Exception:
                    pass

                estado = j.get("state") or ""
                is_remoto = j.get("isRemoteWork", False)
                tipo = j.get("workplaceType", "")  # "remote" | "hybrid" | "on-site"

                # Manter apenas: remoto/hibrido (qualquer estado) ou presencial no Rio
                if not is_remoto and tipo not in ("remote", "hybrid"):
                    if "rio de janeiro" not in estado.lower():
                        continue

                if tipo == "remote" or is_remoto:
                    modalidade = "Remoto"
                elif tipo == "hybrid":
                    modalidade = "Hibrido"
                else:
                    modalidade = "Presencial"

                cidade = j.get("city") or ""
                pais = j.get("country") or ""
                local = ", ".join(parte for parte in (cidade, estado, pais) if parte)

                vagas[url] = {
                    "titulo":     j.get("name", ""),
                    "empresa":    j.get("careerPageName", ""),
                    "local":      local,
                    "local_confiavel": bool(cidade),
                    "modalidade": modalidade,
                    "modalidade_confiavel": True,
                    "url":        url,
                    "descricao":  _limpar_html(j.get("description") or ""),
                    "data":       j.get("publishedDate", ""),
                    "plataforma": "Gupy",
                    "pais": "BR" if not pais or pais.lower() in {"brasil", "brazil"} else "WW",
                }

        except Exception as e:
            print(f"[Gupy] erro no termo '{termo}': {e}")

    return list(vagas.values())


def _limpar_html(texto: str) -> str:
    texto = html.unescape(str(texto or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()[:3000]
