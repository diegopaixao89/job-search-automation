# vagas/gupy.py — API publica Gupy
# Param correto: name (nao jobName). Filtro de estado nao funciona na API,
# entao filtramos pos-fetch: estado RJ ou trabalho remoto/hibrido.

import requests
from vagas.base import HEADERS

API_URL = "https://portal.api.gupy.io/api/job"


def buscar(termos: list[str], limite_por_termo: int = 30) -> list[dict]:
    vagas = {}

    for termo in termos:
        try:
            params = {"name": termo, "limit": limite_por_termo, "offset": 0}
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue

            jobs = r.json().get("data", [])

            for j in jobs:
                url = j.get("jobUrl") or ""
                if not url or url in vagas:
                    continue

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
                local = f"{cidade}, {estado}".strip(", ") or "Rio de Janeiro"

                vagas[url] = {
                    "titulo":     j.get("name", ""),
                    "empresa":    j.get("careerPageName", ""),
                    "local":      local,
                    "modalidade": modalidade,
                    "url":        url,
                    "descricao":  "",
                    "data":       j.get("publishedDate", ""),
                    "plataforma": "Gupy",
                }

        except Exception as e:
            print(f"[Gupy] erro no termo '{termo}': {e}")

    return list(vagas.values())
