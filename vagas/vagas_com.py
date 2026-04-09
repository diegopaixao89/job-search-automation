# vagas/vagas_com.py — scraping Vagas.com via Playwright (site JS-rendered)
# Requer: playwright install chromium

from vagas.base import HEADERS
import re

BASE_URL = "https://www.vagas.com.br"

BUSCAS = [
    ("python", "Rio de Janeiro"),
    ("automacao", "Rio de Janeiro"),
    ("infraestrutura ti", "Rio de Janeiro"),
    ("suporte tecnico", "Rio de Janeiro"),
    ("devops", "Rio de Janeiro"),
    ("python automacao", ""),        # sem local = pega remotas
]


def buscar() -> list[dict]:
    vagas = {}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Vagas.com] Playwright nao instalado.")
        return []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page    = browser.new_page(extra_http_headers=HEADERS)

            for termo, local in BUSCAS:
                try:
                    slug   = termo.replace(" ", "-")
                    url    = f"{BASE_URL}/vagas-de-{slug}"
                    params = f"?onde={local.replace(' ', '+')}" if local else ""
                    page.goto(url + params, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2500)

                    cards = page.query_selector_all("li.vaga") or page.query_selector_all("article.job")

                    for card in cards:
                        link_el = card.query_selector("a.link-detalhes-vaga") or card.query_selector("a[href*='/vaga']")
                        if not link_el:
                            continue

                        href = link_el.get_attribute("href") or ""
                        vaga_url = BASE_URL + href if href.startswith("/") else href
                        vaga_url = vaga_url.split("?")[0]
                        if not vaga_url or vaga_url in vagas:
                            continue

                        titulo  = link_el.inner_text().strip()
                        empresa_el = card.query_selector("span.emprVaga") or card.query_selector(".company")
                        empresa = empresa_el.inner_text().strip() if empresa_el else ""

                        texto = card.inner_text()
                        modalidade = _detectar_modalidade(titulo + " " + texto)

                        vagas[vaga_url] = {
                            "titulo":     titulo,
                            "empresa":    empresa,
                            "local":      local or "Brasil",
                            "modalidade": modalidade,
                            "url":        vaga_url,
                            "descricao":  texto[:1000],
                            "data":       "",
                            "plataforma": "Vagas.com",
                        }

                except Exception as e:
                    print(f"[Vagas.com] erro em '{termo}': {e}")

            browser.close()

    except Exception as e:
        print(f"[Vagas.com] erro geral: {e}")

    return list(vagas.values())


def _detectar_modalidade(texto: str) -> str:
    t = texto.lower()
    if "remoto" in t or "home office" in t:
        return "Remoto"
    if "hibrid" in t or "híbrid" in t:
        return "Hibrido"
    return "Presencial"
