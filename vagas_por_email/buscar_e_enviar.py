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
import re
import sys
import threading
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
from filtros_vagas import vaga_elegivel_geograficamente
from matcher import pontuar_vaga
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

TIMEOUT_FONTE = 90  # segundos max por fonte


def _executar_com_timeout(fn, timeout: float):
    """Executa coletor em thread daemon sem bloquear no encerramento do timeout."""
    estado = {}

    def alvo():
        try:
            estado["resultado"] = fn()
        except BaseException as exc:
            estado["erro"] = exc

    thread = threading.Thread(target=alvo, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError
    if "erro" in estado:
        raise estado["erro"]
    return estado.get("resultado", [])


def coletar() -> list[dict]:
    """Consulta todas as fontes e retorna lista deduplicada por URL."""
    todas: list[dict] = []
    urls_vistas: set[str] = set()

    for i, (nome, fn) in enumerate(FONTES, 1):
        print(f"  [{i}/{len(FONTES)}] {nome}...", flush=True)
        try:
            resultado = _executar_com_timeout(fn, TIMEOUT_FONTE)
            novas = [
                v for v in resultado
                if v.get("url") and v["url"] not in urls_vistas
            ]
            for v in novas:
                urls_vistas.add(v["url"])
            todas.extend(novas)
            print(f"         {len(resultado)} encontradas, {len(novas)} únicas")
        except TimeoutError:
            print(f"         TIMEOUT após {TIMEOUT_FONTE}s — pulando")
        except Exception as e:
            print(f"         Erro: {e}")

    return todas


_PCD_RE = re.compile(r"\bpcd\b|pessoa(?:s)? com defici[êe]ncia", re.I)
_PCD_INCLUSIVA_RE = re.compile(
    r"(?:incluindo|inclusive|tamb[eé]m para)\s+(?:pessoas? com defici[êe]ncia|pcd)"
    r"|pessoas? com e sem defici[êe]ncia|com ou sem defici[êe]ncia"
    r"|pcd\s+(?:e|ou)\s+n[aã]o\s+pcd|ampla concorr[êe]ncia|aberta? a todos"
    r"|tamb[eé]m aberta?[^.;\n]{0,35}(?:sem defici[êe]ncia|n[aã]o pcd)",
    re.I,
)
_PCD_EXCLUSIVA_RE = re.compile(
    r"(?:exclusiv[ao]|exclusivamente|somente|apenas|destinad[ao]|afirmativa|preferencial)[^.;\n]{0,45}"
    r"(?:pessoas? com defici[êe]ncia|pcd)"
    r"|(?:pessoas? com defici[êe]ncia|pcd)[^.;\n]{0,25}(?:exclusiv[ao]|apenas|somente|preferencial)",
    re.I,
)


def _nao_e_pcd_exclusiva(vaga: dict) -> bool:
    titulo = vaga.get("titulo") or ""
    descricao = vaga.get("descricao") or ""
    texto = titulo + " " + descricao
    if _PCD_EXCLUSIVA_RE.search(texto):
        return False
    if _PCD_RE.search(titulo) and not _PCD_INCLUSIVA_RE.search(texto):
        return False
    return True


def processar(todas: list[dict], score_minimo: int) -> list[dict]:
    """Aplica geografia, perfis dos curriculos, corte e ordenacao."""
    filtradas = []
    for vaga in todas:
        if not vaga_elegivel_geograficamente(vaga):
            continue
        if not _nao_e_pcd_exclusiva(vaga):
            continue
        pontuar_vaga(vaga)
        if vaga["score"] >= score_minimo:
            filtradas.append(vaga)

    # Aderencia primeiro; modalidade funciona apenas como desempate.
    filtradas.sort(key=lambda v: (
        -v.get("score", 0),
        {"Remoto": 0, "Hibrido": 1}.get(v.get("modalidade", ""), 2),
        v.get("titulo", "").lower(),
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
    parser.add_argument(
        "--history-days", type=int, default=30,
        help="Mantem no historico apenas vagas vistas nos ultimos N dias (padrão: 30; use 0 para permanente)",
    )
    parser.add_argument(
        "--reset-history", action="store_true",
        help="Limpa o historico de vagas vistas antes de executar",
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
    print(f"Historico    : {'permanente' if args.history_days <= 0 else f'ultimos {args.history_days} dias'}")
    print("=" * 60)

    if args.reset_history:
        banco.limpar_vagas_vistas()
        print("[INFO] Historico de vagas limpo antes da execucao.")
    elif args.history_days > 0:
        banco.limpar_vagas_vistas_mais_antigas_que(args.history_days)
        print(f"[INFO] Mantendo apenas historico dos ultimos {args.history_days} dias.")

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
    novas = [v for v in filtradas if banco.is_nova(v["url"], args.history_days if args.history_days > 0 else None)]
    print(f"Não enviadas   : {len(novas)}\n")

    if not novas:
        print("Nenhuma vaga nova para enviar. Encerrando.")
        if filtradas:
            if args.history_days > 0:
                print(f"Todas as vagas relevantes já apareceram nos últimos {args.history_days} dias.")
                print("Para recomeçar do zero, use --reset-history.")
            else:
                print("Todas as vagas relevantes já estavam no historico permanente.")
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
            local=v.get("local", ""),
            modalidade=v.get("modalidade", ""),
            pais=v.get("pais", "BR"),
        )

    print(f"\nConcluído. {len(novas)} vagas enviadas por e-mail.")
    print(f"Total histórico no banco: {banco.total_vistas()} vagas vistas")


if __name__ == "__main__":
    main()
