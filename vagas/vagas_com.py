# vagas/vagas_com.py — scraping Vagas.com via Playwright (site JS-rendered)
# Requer: playwright install chromium

from vagas.base import HEADERS
from filtros_vagas import detectar_modalidade, extrair_localizacao_anuncio

BASE_URL = "https://www.vagas.com.br"

BUSCAS = [
    ("analista de automacao", "Rio de Janeiro"),
    ("analista de integracoes", "Rio de Janeiro"),
    ("analista de suporte", "Rio de Janeiro"),
    ("analista de infraestrutura", "Rio de Janeiro"),
    ("analista de ti", "Rio de Janeiro"),
    ("tecnico de suporte", "Rio de Janeiro"),
    ("analista de service desk", "Rio de Janeiro"),
    ("analista iam", "Rio de Janeiro"),
    ("devops junior", "Rio de Janeiro"),
    ("backend python junior", ""),
    ("desenvolvedor python junior", ""),
]

TIMEOUT_PAGINA = 15000   # 15s por pagina
TIMEOUT_TOTAL  = 120     # segundos (2min total para Vagas.com)


def buscar() -> list[dict]:
    import threading
    resultado = []
    thread = threading.Thread(target=_buscar_inner, args=(resultado,))
    thread.daemon = True
    thread.start()
    thread.join(TIMEOUT_TOTAL)
    if thread.is_alive():
        print("[Vagas.com] TIMEOUT geral — pulando fonte")
    return resultado


def _buscar_inner(resultado: list) -> None:
    vagas = {}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Vagas.com] Playwright nao instalado.")
        return

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page    = browser.new_page(extra_http_headers=HEADERS)

            for termo, local in BUSCAS:
                try:
                    slug   = termo.replace(" ", "-")
                    url    = f"{BASE_URL}/vagas-de-{slug}"
                    params = f"?onde={local.replace(' ', '+')}" if local else ""
                    page.goto(url + params, timeout=TIMEOUT_PAGINA, wait_until="domcontentloaded")
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
                        local_real = extrair_localizacao_anuncio(texto, vaga_url)
                        modalidade = detectar_modalidade(titulo + " " + texto, local_real)

                        vagas[vaga_url] = {
                            "titulo":     titulo,
                            "empresa":    empresa,
                            "local":      local_real,
                            "local_consulta": local or "Brasil",
                            "local_confiavel": bool(local_real),
                            "modalidade": modalidade,
                            "url":        vaga_url,
                            "descricao":  texto[:1000],
                            "data":       "",
                            "plataforma": "Vagas.com",
                            "pais": "BR",
                        }

                except Exception as e:
                    print(f"[Vagas.com] erro em '{termo}': {e}")

            browser.close()

    except Exception as e:
        print(f"[Vagas.com] erro geral: {e}")

    resultado.extend(list(vagas.values()))
