#!/usr/bin/env python3
"""
gerar_pdfs.py — Gera os PDFs dos curriculos a partir dos HTMLs.

Prerequisito: playwright instalado com chromium
  pip install playwright
  playwright install chromium

Uso:
  python gerar_pdfs.py
"""
import os
import sys

DESKTOP_IA = os.path.join(os.path.expanduser("~"), "Desktop", "Projetos IA")

CURRICULOS = [
    {
        "html":  os.path.join(DESKTOP_IA, "curriculo_profissional_diego_paixao.html"),
        "pdf":   os.path.join(DESKTOP_IA, "curriculo_profissional_diego_paixao.pdf"),
        "label": "CV Portugues",
    },
    {
        "html":  os.path.join(DESKTOP_IA, "curriculo_diego_paixao_en.html"),
        "pdf":   os.path.join(DESKTOP_IA, "curriculo_diego_paixao_en.pdf"),
        "label": "CV Ingles",
    },
]


def gerar(html_path: str, pdf_path: str, label: str) -> bool:
    if not os.path.isfile(html_path):
        print(f"[{label}] HTML nao encontrado: {html_path}")
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERRO: playwright nao instalado. Execute:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    print(f"[{label}] Gerando PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file:///{html_path.replace(os.sep, '/')}")
        page.wait_for_load_state("networkidle")
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()

    print(f"[{label}] Salvo em: {pdf_path}")
    return True


def main():
    print("Gerando PDFs dos curriculos...\n")
    sucesso = 0
    for item in CURRICULOS:
        ok = gerar(item["html"], item["pdf"], item["label"])
        if ok:
            sucesso += 1
    print(f"\n{sucesso}/{len(CURRICULOS)} PDFs gerados com sucesso.")
    if sucesso == len(CURRICULOS):
        print("\nAgora voce pode rodar:")
        print("  python rodar_automatico.py --dry-run   # testar sem enviar")
        print("  python rodar_automatico.py             # execucao real")


if __name__ == "__main__":
    main()
