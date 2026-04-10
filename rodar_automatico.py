#!/usr/bin/env python3
"""
rodar_automatico.py — Busca vagas em 8 fontes, envia candidaturas automaticamente
e manda um digest HTML por e-mail com todas as vagas encontradas.

Uso:
  python rodar_automatico.py                  # padrao
  python rodar_automatico.py --score 30       # score minimo personalizado
  python rodar_automatico.py --dry-run        # simula sem enviar e-mails (salva preview HTML)
"""
import argparse
import os
import sys
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(ROOT, ".env"))
sys.path.insert(0, ROOT)

import config
import banco
import matcher
import aplicador

# Caminhos dos curriculos PDF
_DESKTOP_IA = os.path.join(os.path.expanduser("~"), "Desktop", "Projetos IA")
CV_PT = os.path.join(_DESKTOP_IA, "curriculo_profissional_diego_paixao.pdf")
CV_EN = os.path.join(_DESKTOP_IA, "curriculo_diego_paixao_en.pdf")

# Plataformas internacionais -> usar CV e carta em ingles
PLATAFORMAS_INTERNACIONAIS = {"Remotive", "WeWorkRemotely", "Himalayas"}

# ---------------------------------------------------------------------------
# Templates de carta de apresentacao
# ---------------------------------------------------------------------------
ASSUNTO_PT = "Candidatura — {titulo} — Diego Mendonça Paixão"
ASSUNTO_EN = "Job Application — {titulo} — Diego Mendonca Paixao"

CARTA_PT = """Prezados(as),

Venho manifestar meu interesse na vaga de {titulo}{empresa_str}.

Sou técnico de TI com experiência em suporte, infraestrutura e desenvolvimento de automações em Python. Trabalho com integrações REST, Google Workspace, Active Directory e Zeev BPM, com projetos em produção usando Docker, processamento paralelo e interfaces gráficas.

Segue em anexo meu currículo para apreciação.

Agradeço a atenção e fico à disposição para uma conversa.

Atenciosamente,
{{NOME}}
{{TELEFONE}} | {{EMAIL}}
LinkedIn: {{LINKEDIN}}"""

CARTA_EN = """Dear Hiring Team,

I am writing to express my interest in the {titulo} position{empresa_str}.

I am an IT professional based in Rio de Janeiro, Brazil, with hands-on experience in \
infrastructure support, process automation, and system integration at enterprise scale. \
I build Python-based tools that integrate with REST APIs, Google Workspace, Active Directory, \
and BPM platforms — projects running in production with Docker, parallel processing, and \
custom GUIs.

A note on language: my English is at an intermediate level (B1–B2). I am proficient in reading \
and writing, and I use AI-assisted communication tools to work effectively in professional \
contexts. This is not a barrier to collaborating with English-speaking teams.

Please find my CV attached. I would welcome the opportunity to discuss how my background can \
contribute to your team.

Best regards,
{{NOME}}
{{TELEFONE}} | {{EMAIL}}
LinkedIn: {{LINKEDIN}}"""


def _escolher_idioma(vaga: dict) -> str:
    """Retorna 'en' para plataformas internacionais, 'pt' para as demais."""
    return "en" if vaga.get("plataforma", "") in PLATAFORMAS_INTERNACIONAIS else "pt"


def _cv_e_templates(idioma: str) -> tuple[str, str, str]:
    """Retorna (cv_path, assunto_template, corpo_template)."""
    if idioma == "en":
        return CV_EN, ASSUNTO_EN, CARTA_EN
    return CV_PT, ASSUNTO_PT, CARTA_PT


# ---------------------------------------------------------------------------
# Busca de vagas em todas as fontes
# ---------------------------------------------------------------------------
def _buscar_todas(verbose: bool = True) -> list[dict]:
    from vagas import remotive, weworkremotely, himalayas, gupy
    from vagas import infojobs, programathor, linkedin, vagas_com

    FONTES = [
        ("Remotive",       lambda: remotive.buscar()),
        ("WeWorkRemotely", lambda: weworkremotely.buscar()),
        ("Himalayas",      lambda: himalayas.buscar()),
        ("Gupy",           lambda: gupy.buscar(config.TERMOS_BUSCA)),
        ("InfoJobs",       lambda: infojobs.buscar()),
        ("ProgramaThor",   lambda: programathor.buscar(config.LOCAIS_BUSCA)),
        ("LinkedIn",       lambda: linkedin.buscar()),
        ("Vagas.com",      lambda: vagas_com.buscar()),
    ]

    todas = []
    urls_vistas: set[str] = set()

    for nome, fn in FONTES:
        try:
            resultado = fn()
            novas = [v for v in resultado if v.get("url") and v["url"] not in urls_vistas]
            for v in novas:
                urls_vistas.add(v["url"])
                v["score"] = matcher.calcular_score(v)
                v["_email_candidatura"] = aplicador.extrair_email_candidatura(v.get("descricao", ""))
            todas.extend(novas)
            if verbose:
                print(f"  [{nome}] {len(resultado)} encontradas, {len(novas)} novas nesta sessao")
        except Exception as e:
            if verbose:
                print(f"  [{nome}] ERRO: {e}")

    return todas


# ---------------------------------------------------------------------------
# Envio individual de candidatura
# ---------------------------------------------------------------------------
def _tentar_enviar(vaga: dict, email_rem: str, senha: str, dry_run: bool) -> dict:
    """
    Tenta enviar candidatura. Retorna dict com chaves:
      status: 'enviado' | 'dry_run' | 'cv_ausente' | 'erro'
      mensagem: str
      idioma: 'pt' | 'en'
    """
    idioma = _escolher_idioma(vaga)
    cv_path, assunto_tpl, corpo_tpl = _cv_e_templates(idioma)
    email_dest = vaga.get("_email_candidatura", "")

    if not os.path.isfile(cv_path):
        return {"status": "cv_ausente", "mensagem": f"PDF nao encontrado: {cv_path}", "idioma": idioma}

    if dry_run:
        print(f"    [DRY-RUN] Para: {email_dest} | CV: {os.path.basename(cv_path)}")
        return {"status": "dry_run", "mensagem": "dry-run", "idioma": idioma}

    ok, msg = aplicador.enviar_candidatura(
        email_destino=email_dest,
        email_remetente=email_rem,
        senha_app=senha,
        vaga=vaga,
        curriculo_path=cv_path,
        assunto_template=assunto_tpl,
        corpo_template=corpo_tpl,
    )
    return {"status": "enviado" if ok else "erro", "mensagem": msg, "idioma": idioma}


# ---------------------------------------------------------------------------
# Digest HTML
# ---------------------------------------------------------------------------
def _montar_digest(
    enviadas: list[dict],
    com_email: list[dict],
    formulario: list[dict],
) -> str:
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = len(enviadas) + len(com_email) + len(formulario)

    def _badge_en(v: dict) -> str:
        if v.get("_idioma") == "en":
            return ('<span style="background:#fff3e0;color:#c2410c;padding:2px 8px;'
                    'border-radius:999px;font-size:10px;font-weight:700;margin-left:8px;">'
                    'EN</span>')
        return ""

    def _card(v: dict, borda: str, extra_html: str = "") -> str:
        score    = v.get("score", 0)
        plat     = v.get("plataforma", "")
        mod      = v.get("modalidade", "Presencial")
        empresa  = v.get("empresa") or "Empresa nao informada"
        local    = v.get("local", "")
        titulo   = v.get("titulo", "")
        url      = v.get("url", "#")

        score_cor = ("#22c55e" if score >= 60 else
                     "#f59e0b" if score >= 35 else "#94a3b8")
        mod_cor, mod_bg = {
            "Remoto":    ("#16a34a", "#f0fdf4"),
            "Hibrido":   ("#2563eb", "#eff6ff"),
        }.get(mod, ("#78716c", "#f5f5f4"))

        return f"""
<div style="background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:10px;
            border-left:4px solid {borda};box-shadow:0 1px 3px rgba(0,0,0,.07);">
  <div style="font-size:16px;font-weight:700;color:#0f172a;margin-bottom:3px;">
    {titulo}{_badge_en(v)}
  </div>
  <div style="font-size:12px;color:#64748b;margin-bottom:10px;">
    {empresa}{f" &mdash; {local}" if local else ""}
  </div>
  <span style="background:{score_cor}22;color:{score_cor};padding:2px 10px;
               border-radius:999px;font-size:11px;font-weight:700;margin-right:5px;">Score {score}</span>
  <span style="background:#f1f5f9;color:#475569;padding:2px 10px;
               border-radius:999px;font-size:11px;margin-right:5px;">{plat}</span>
  <span style="background:{mod_bg};color:{mod_cor};padding:2px 10px;
               border-radius:999px;font-size:11px;font-weight:600;">{mod}</span>
  {extra_html}
  <div style="margin-top:14px;">
    <a href="{url}" style="background:#0f172a;color:#fff;text-decoration:none;
       padding:8px 18px;border-radius:6px;font-size:13px;font-weight:600;">
      Ver vaga &rarr;
    </a>
  </div>
</div>"""

    def _secao(titulo: str, cor: str, bg: str, vagas: list[dict], builder) -> str:
        if not vagas:
            return ""
        qtd = len(vagas)
        cards = "".join(builder(v) for v in sorted(vagas, key=lambda x: -x.get("score", 0)))
        return f"""
<div style="margin-bottom:28px;">
  <div style="background:{bg};border-radius:8px;padding:12px 20px;margin-bottom:14px;">
    <span style="font-size:11px;font-weight:700;text-transform:uppercase;
                 letter-spacing:1.5px;color:{cor};">{titulo}</span>
    <span style="font-size:12px;color:{cor};margin-left:8px;opacity:.75;">
      &mdash; {qtd} vaga{'s' if qtd != 1 else ''}
    </span>
  </div>
  <div style="padding:0 4px;">{cards}</div>
</div>"""

    def _build_enviada(v: dict) -> str:
        cv_label = "CV em Ingles enviado" if v.get("_idioma") == "en" else "CV em Portugues enviado"
        extra = (f'<p style="font-size:12px;color:#15803d;margin:8px 0 0;">&#10003; {cv_label} '
                 f'para {v.get("_email_candidatura", "")}</p>')
        return _card(v, "#22c55e", extra)

    def _build_com_email(v: dict) -> str:
        email = v.get("_email_candidatura", "")
        motivo = v.get("_motivo", "")
        extra = (f'<p style="font-size:12px;color:#1d4ed8;margin:8px 0 0;">&#128231; {email}'
                 f'{f" &mdash; {motivo}" if motivo else ""}</p>')
        return _card(v, "#3b82f6", extra)

    def _build_formulario(v: dict) -> str:
        return _card(v, "#f59e0b")

    sec_env = _secao("Candidaturas Enviadas Automaticamente",
                     "#15803d", "#f0fdf4", enviadas, _build_enviada)
    sec_email = _secao("Vagas com E-mail Direto",
                       "#1d4ed8", "#eff6ff", com_email, _build_com_email)
    sec_form = _secao("Aplicar via Formulario / Link",
                      "#92400e", "#fffbeb", formulario, _build_formulario)

    partes_resumo = []
    if enviadas:
        partes_resumo.append(
            f"<b style='color:#15803d;'>{len(enviadas)}</b> candidatura{'s' if len(enviadas) != 1 else ''} enviada{'s' if len(enviadas) != 1 else ''}")
    if com_email:
        partes_resumo.append(
            f"<b style='color:#1d4ed8;'>{len(com_email)}</b> com e-mail direto")
    if formulario:
        partes_resumo.append(
            f"<b style='color:#92400e;'>{len(formulario)}</b> via formulario")
    resumo = " &nbsp;&bull;&nbsp; ".join(partes_resumo) if partes_resumo else "Nenhuma vaga encontrada"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:20px;background:#f1f5f9;
             font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:700px;margin:0 auto;">

  <!-- Cabecalho -->
  <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);
              border-radius:12px 12px 0 0;padding:28px 32px;color:#fff;">
    <div style="font-size:22px;font-weight:700;margin-bottom:4px;">
      Automacao de Vagas
    </div>
    <div style="font-size:13px;color:#93c5fd;">
      {total} vaga{'s' if total != 1 else ''} encontrada{'s' if total != 1 else ''} &mdash; {data_hora}
    </div>
  </div>

  <!-- Resumo rapido -->
  <div style="background:#fff;padding:14px 32px;border-bottom:1px solid #e2e8f0;
              font-size:13px;color:#475569;">
    {resumo}
  </div>

  <!-- Secoes -->
  <div style="padding:24px 0;">
    {sec_env}
    {sec_email}
    {sec_form}
  </div>

  <!-- Rodape -->
  <div style="text-align:center;font-size:11px;color:#94a3b8;padding:12px 0 24px;">
    CaçaVagas
  </div>

</div>
</body>
</html>"""


def _enviar_digest(html: str, enviadas: list[dict], com_email: list[dict],
                   formulario: list[dict], email_rem: str, email_dest: str,
                   senha: str, dry_run: bool) -> None:
    total = len(enviadas) + len(com_email) + len(formulario)
    if total == 0:
        print("[Digest] Nenhuma vaga nova. E-mail nao enviado.")
        return

    data_hoje = datetime.now().strftime("%d/%m/%Y")
    n_env = len(enviadas)
    assunto = (f"[Vagas] {total} nova{'s' if total != 1 else ''} — "
               f"{n_env} candidatura{'s' if n_env != 1 else ''} enviada{'s' if n_env != 1 else ''} — "
               f"{data_hoje}")

    if dry_run:
        preview = os.path.join(ROOT, "digest_preview.html")
        with open(preview, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Digest] DRY-RUN — preview salvo em: {preview}")
        print(f"[Digest] Assunto seria: {assunto}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = email_rem
    msg["To"]      = email_dest
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_rem, senha)
        smtp.sendmail(email_rem, email_dest, msg.as_string())
    print(f"[Digest] Enviado para {email_dest} ({total} vagas, {n_env} candidaturas)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Automacao de vagas sem interface grafica")
    parser.add_argument("--score", type=int, default=config.SCORE_MINIMO,
                        help=f"Score minimo (default: {config.SCORE_MINIMO})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sem enviar e-mails; salva digest_preview.html")
    args = parser.parse_args()

    senha = os.getenv("GMAIL_APP_PASSWORD", "")
    if not senha and not args.dry_run:
        print("ERRO: GMAIL_APP_PASSWORD nao encontrada no .env")
        sys.exit(1)

    email_rem  = config.EMAIL_REMETENTE
    email_dest = config.EMAIL_DESTINO

    # Verificar CVs
    print("=" * 60)
    print("Automacao de Vagas — modo CLI")
    print("=" * 60)
    cv_pt_ok = os.path.isfile(CV_PT)
    cv_en_ok = os.path.isfile(CV_EN)
    print(f"CV Portugues: {'OK' if cv_pt_ok else 'AUSENTE — ' + CV_PT}")
    print(f"CV Ingles:    {'OK' if cv_en_ok else 'AUSENTE — ' + CV_EN}")
    if not cv_pt_ok or not cv_en_ok:
        print("\nDica: execute 'python gerar_pdfs.py' para gerar os PDFs dos curriculos.")
    print(f"Score minimo: {args.score}")
    print(f"Modo: {'DRY-RUN (sem envio)' if args.dry_run else 'PRODUCAO'}")
    print()

    # Buscar vagas
    print("Buscando vagas...")
    todas = _buscar_todas(verbose=True)
    print(f"\nTotal encontrado: {len(todas)} vagas\n")

    # Classificar e enviar
    enviadas:   list[dict] = []
    com_email:  list[dict] = []
    formulario: list[dict] = []

    print("Processando candidaturas...")
    for vaga in todas:
        if vaga.get("score", 0) < args.score:
            continue

        url         = vaga.get("url", "")
        email_vaga  = vaga.get("_email_candidatura")

        if email_vaga:
            # Ja aplicou antes? Pular.
            if banco.ja_aplicou(url):
                continue

            result = _tentar_enviar(vaga, email_rem, senha, args.dry_run)
            vaga["_idioma"] = result["idioma"]

            if result["status"] in ("enviado", "dry_run"):
                if not args.dry_run:
                    cv_path, _, _ = _cv_e_templates(result["idioma"])
                    banco.registrar_candidatura(
                        url=url,
                        titulo=vaga.get("titulo", ""),
                        empresa=vaga.get("empresa", ""),
                        email_destino=email_vaga,
                        curriculo=cv_path,
                        status="enviado",
                    )
                    banco.marcar_vista(url, vaga.get("titulo", ""), vaga.get("empresa", ""),
                                       vaga.get("plataforma", ""), vaga.get("score", 0))
                enviadas.append(vaga)
                print(f"  [OK] {vaga.get('titulo', '')[:55]} -> {email_vaga}")
            else:
                # Nao conseguiu enviar (CV ausente, erro SMTP...)
                vaga["_motivo"] = result["mensagem"]
                if banco.is_nova(url):
                    com_email.append(vaga)
                    banco.marcar_vista(url, vaga.get("titulo", ""), vaga.get("empresa", ""),
                                       vaga.get("plataforma", ""), vaga.get("score", 0))
                print(f"  [!] {vaga.get('titulo', '')[:55]} — {result['mensagem']}")
        else:
            # Sem email — so inclui se e vaga nova
            if banco.is_nova(url):
                formulario.append(vaga)
                banco.marcar_vista(url, vaga.get("titulo", ""), vaga.get("empresa", ""),
                                   vaga.get("plataforma", ""), vaga.get("score", 0))

    print()
    print("Resultado desta sessao:")
    print(f"  Candidaturas enviadas:    {len(enviadas)}")
    print(f"  Vagas com e-mail direto:  {len(com_email)}")
    print(f"  Vagas via formulario:     {len(formulario)}")
    print()

    # Montar e enviar digest
    html = _montar_digest(enviadas, com_email, formulario)
    print("Enviando digest por e-mail...")
    _enviar_digest(html, enviadas, com_email, formulario,
                   email_rem, email_dest, senha, args.dry_run)

    print("\nConcluido.")


if __name__ == "__main__":
    main()
