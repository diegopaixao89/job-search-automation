#!/usr/bin/env python3
# vagas_por_email/buscar_e_enviar.py
# Roda sem interface gráfica — coleta vagas, filtra por score e envia digest HTML por e-mail.
# Indicado para agendar via Task Scheduler (Windows) ou cron (Linux/Mac).
#
# Uso:
#   python buscar_e_enviar.py                  # execução normal
#   python buscar_e_enviar.py --score 30       # score mínimo personalizado
#   python buscar_e_enviar.py --dry-run        # simula sem enviar; salva preview_digest.html

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Resolve raiz do projeto (pasta pai desta pasta) ──────────────────────────
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Importa módulos do projeto principal ─────────────────────────────────────
from config import (
    EMAIL_DESTINO, EMAIL_REMETENTE,
    TERMOS_BUSCA, LOCAIS_BUSCA, SCORE_MINIMO,
)
from matcher import calcular_score
import banco
import notificador
from vagas import (
    gupy, remotive, linkedin, programathor,
    weworkremotely, himalayas, infojobs, vagas_com, indeed,
)

# ── Fontes de busca ───────────────────────────────────────────────────────────
FONTES = [
    ("Gupy",            lambda: gupy.buscar(TERMOS_BUSCA)),
    ("LinkedIn",        lambda: linkedin.buscar()),
    ("Indeed",          lambda: indeed.buscar(TERMOS_BUSCA, LOCAIS_BUSCA)),
    ("Remotive",        lambda: remotive.buscar()),
    ("WeWorkRemotely",  lambda: weworkremotely.buscar()),
    ("Himalayas",       lambda: himalayas.buscar()),
    ("InfoJobs",        lambda: infojobs.buscar()),
    ("ProgramaThor",    lambda: programathor.buscar(LOCAIS_BUSCA)),
    ("Vagas.com",       lambda: vagas_com.buscar()),
]


def coletar() -> list[dict]:
    """Consulta todas as fontes e retorna lista deduplicada por URL."""
    todas: list[dict] = []
    urls_vistas: set[str] = set()

    for i, (nome, fn) in enumerate(FONTES, 1):
        print(f"  [{i}/{len(FONTES)}] {nome}...", flush=True)
        try:
            resultado = fn()
            novas = [
                v for v in resultado
                if v.get("url") and v["url"] not in urls_vistas
            ]
            for v in novas:
                urls_vistas.add(v["url"])
            todas.extend(novas)
            print(f"         {len(resultado)} encontradas, {len(novas)} únicas")
        except Exception as e:
            print(f"         Erro: {e}")

    return todas


def processar(todas: list[dict], score_minimo: int) -> list[dict]:
    """Calcula score de cada vaga, filtra pelo mínimo e ordena."""
    for v in todas:
        v["score"] = calcular_score(v)

    filtradas = [v for v in todas if v["score"] >= score_minimo]

    # Remoto primeiro, depois Hibrido, depois Presencial; desempate por score desc
    filtradas.sort(key=lambda v: (
        {"Remoto": 0, "Hibrido": 1}.get(v.get("modalidade", ""), 2),
        -v.get("score", 0),
    ))

    return filtradas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CaçaVagas — busca vagas e envia digest por e-mail"
    )
    parser.add_argument(
        "--score", type=int, default=SCORE_MINIMO,
        help=f"Score mínimo para incluir vaga (padrão: {SCORE_MINIMO})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simula sem enviar e-mail; salva o HTML em preview_digest.html",
    )
    args = parser.parse_args()

    senha = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not senha and not args.dry_run:
        print("[ERRO] GMAIL_APP_PASSWORD não encontrada no .env")
        sys.exit(1)

    print("=" * 60)
    print(f"CaçaVagas — digest e-mail  [{datetime.now().strftime('%d/%m/%Y %H:%M')}]")
    print(f"Score mínimo : {args.score}")
    print(f"Destino      : {EMAIL_DESTINO}")
    print(f"Modo         : {'DRY-RUN (sem envio)' if args.dry_run else 'PRODUÇÃO'}")
    print("=" * 60)

    # ── Coleta ───────────────────────────────────────────────────────────────
    print("\nBuscando vagas em todas as fontes...\n")
    todas = coletar()
    print(f"\nTotal coletado : {len(todas)} vagas únicas")

    # ── Scoring e filtro ──────────────────────────────────────────────────────
    filtradas = processar(todas, args.score)

    remotas     = sum(1 for v in filtradas if v.get("modalidade") == "Remoto")
    hibridas    = sum(1 for v in filtradas if v.get("modalidade") == "Hibrido")
    presenciais = len(filtradas) - remotas - hibridas

    print(f"Relevantes     : {len(filtradas)}  "
          f"(remotas: {remotas} | híbridas: {hibridas} | presenciais: {presenciais})")

    # ── Filtra apenas as que ainda não foram enviadas ─────────────────────────
    novas = [v for v in filtradas if banco.is_nova(v["url"])]
    print(f"Não enviadas   : {len(novas)}\n")

    if not novas:
        print("Nenhuma vaga nova para enviar. Encerrando.")
        return

    # ── Detecta vagas de Analista Jr. para destaque ───────────────────────────
    def _is_analista_jr(vaga: dict) -> bool:
        titulo = vaga.get("titulo", "").lower()
        tem_analista = "analista" in titulo or "analyst" in titulo
        tem_jr = any(kw in titulo for kw in ("jr", "jr.", "junior", "júnior", "i ", " i "))
        return tem_analista and tem_jr

    destaques = [v for v in novas if _is_analista_jr(v)]
    if destaques:
        print(f"Vagas Analista Jr. em destaque: {len(destaques)}")

    # ── Dry-run: salva HTML e encerra ─────────────────────────────────────────
    if args.dry_run:
        html = notificador._montar_html(novas, destaques=destaques or None)
        preview = Path(__file__).parent / "preview_digest.html"
        preview.write_text(html, encoding="utf-8")
        print(f"[DRY-RUN] HTML salvo em: {preview}")
        print(f"[DRY-RUN] Seriam enviadas {len(novas)} vagas para {EMAIL_DESTINO}")
        return

    # ── Envia digest ──────────────────────────────────────────────────────────
    print(f"Enviando digest para {EMAIL_DESTINO}...")
    notificador.enviar_digest(novas, EMAIL_DESTINO, EMAIL_REMETENTE, senha,
                              destaques=destaques or None)

    # ── Marca como vistas no banco (evita reenvio) ────────────────────────────
    for v in novas:
        banco.marcar_vista(
            v["url"],
            v["titulo"],
            v.get("empresa", ""),
            v["plataforma"],
            v["score"],
        )

    print(f"\nConcluído. {len(novas)} vagas enviadas por e-mail.")
    print(f"Total histórico no banco: {banco.total_vistas()} vagas vistas")


if __name__ == "__main__":
    main()
