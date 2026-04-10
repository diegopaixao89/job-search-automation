# notificador.py — monta e envia o digest de vagas por e-mail HTML

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from matcher import keywords_encontradas


def enviar_digest(vagas_novas: list[dict], email_destino: str, email_remetente: str, senha_app: str):
    if not vagas_novas:
        print("[Email] Nenhuma vaga nova. E-mail nao enviado.")
        return

    html = _montar_html(vagas_novas)
    total = len(vagas_novas)
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Vagas] {total} nova{'s' if total > 1 else ''} vaga{'s' if total > 1 else ''} — {data_hoje}"
    msg["From"]    = email_remetente
    msg["To"]      = email_destino
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.sendmail(email_remetente, email_destino, msg.as_string())
        print(f"[Email] Digest enviado: {total} vagas para {email_destino}")
    except Exception as e:
        print(f"[Email] Erro ao enviar: {e}")
        raise


def _montar_html(vagas: list[dict]) -> str:
    # Separar por modalidade (remoto/hibrido primeiro, presencial depois)
    remotas  = [v for v in vagas if v.get("modalidade") == "Remoto"]
    hibridas = [v for v in vagas if v.get("modalidade") == "Hibrido"]
    presenciais = [v for v in vagas if v.get("modalidade") not in ("Remoto", "Hibrido")]

    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = len(vagas)

    secoes = ""
    if remotas:
        secoes += _secao("Remoto", remotas, "#1a7f4b", "#e8f5ee")
    if hibridas:
        secoes += _secao("Hibrido", hibridas, "#0f5c8a", "#eef5fa")
    if presenciais:
        secoes += _secao("Presencial — Rio de Janeiro e Regiao", presenciais, "#5a4e00", "#faf8e8")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: "Segoe UI", Arial, sans-serif; background: #f2f4f7; margin: 0; padding: 20px; }}
  .wrapper {{ max-width: 720px; margin: 0 auto; }}
  .header {{ background: #0d2d5e; color: #fff; padding: 24px 28px; border-radius: 10px 10px 0 0; }}
  .header h1 {{ margin: 0; font-size: 22px; }}
  .header p {{ margin: 6px 0 0; font-size: 13px; color: #aac4e0; }}
  .summary {{ background: #fff; padding: 16px 28px; border-bottom: 1px solid #e0e6ef; font-size: 14px; color: #444; }}
  .secao-titulo {{ font-size: 13px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
                   padding: 12px 28px 8px; margin-top: 12px; }}
  .card {{ background: #fff; border-radius: 8px; margin: 0 0 10px; padding: 18px 22px;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
  .card-titulo {{ font-size: 16px; font-weight: 700; color: #0d2d5e; margin: 0 0 4px; }}
  .card-meta {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
  .badge {{ display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; margin-right: 6px; }}
  .badge-score {{ background: #e8effe; color: #0d2d5e; }}
  .badge-plat  {{ background: #f0f0f0; color: #444; }}
  .badge-remoto {{ background: #e8f5ee; color: #1a7f4b; }}
  .badge-hibrido {{ background: #eef5fa; color: #0f5c8a; }}
  .badge-presencial {{ background: #faf8e8; color: #5a4e00; }}
  .keywords {{ font-size: 11px; color: #888; margin: 8px 0 12px; }}
  .btn {{ display: inline-block; background: #0d2d5e; color: #fff !important; text-decoration: none;
          padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 600; }}
  .footer {{ text-align: center; font-size: 11px; color: #aaa; padding: 20px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Vagas encontradas</h1>
    <p>{total} nova{'s' if total > 1 else ''} vaga{'s' if total > 1 else ''} &mdash; {data_hoje}</p>
  </div>
  <div class="summary">
    <b>{len(remotas)}</b> remotas &nbsp;|&nbsp;
    <b>{len(hibridas)}</b> hibridas &nbsp;|&nbsp;
    <b>{len(presenciais)}</b> presenciais (Rio de Janeiro e regiao)
  </div>
  {secoes}
  <div class="footer">CaçaVagas</div>
</div>
</body>
</html>"""


def _secao(titulo: str, vagas: list[dict], cor: str, bg: str) -> str:
    cards = "".join(_card(v, cor, bg) for v in sorted(vagas, key=lambda x: x.get("score", 0), reverse=True))
    return f"""
<div class="secao-titulo" style="color:{cor};">{titulo} &mdash; {len(vagas)} vaga{'s' if len(vagas) > 1 else ''}</div>
<div style="padding: 0 10px;">
  {cards}
</div>"""


def _card(v: dict, cor: str, bg: str) -> str:
    score = v.get("score", 0)
    modalidade = v.get("modalidade", "")
    kws = keywords_encontradas(v)
    kw_texto = " &bull; ".join(kws) if kws else ""

    badge_mod_class = {
        "Remoto": "badge-remoto",
        "Hibrido": "badge-hibrido",
    }.get(modalidade, "badge-presencial")

    empresa = v.get("empresa") or "Empresa nao informada"
    local   = v.get("local") or ""
    data    = v.get("data") or ""
    meta_partes = [p for p in [empresa, local, data] if p]

    descricao = v.get("descricao", "")
    trecho = descricao[:200].strip() + "..." if len(descricao) > 200 else descricao

    return f"""
<div class="card">
  <div class="card-titulo">{v.get('titulo', '')}</div>
  <div class="card-meta">{" &nbsp;&mdash;&nbsp; ".join(meta_partes)}</div>
  <span class="badge badge-score" style="background:{bg};color:{cor};">Score {score}</span>
  <span class="badge badge-plat">{v.get('plataforma', '')}</span>
  <span class="badge {badge_mod_class}">{modalidade}</span>
  {f'<div class="keywords">Palavras-chave: {kw_texto}</div>' if kw_texto else ''}
  {f'<p style="font-size:13px;color:#555;margin:8px 0;">{trecho}</p>' if trecho else ''}
  <a href="{v.get('url', '#')}" class="btn">Ver vaga &rarr;</a>
</div>"""
