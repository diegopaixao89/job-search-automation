# aplicador.py — envia candidatura por e-mail com CV anexado

import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

EMAILS_IGNORADOS = {
    "noreply", "no-reply", "donotreply", "notifications",
    "mailer", "bounce", "support", "info", "contato",
}

ASSUNTO_PADRAO = "Candidatura — {titulo} — Diego Mendonça Paixão"

CORPO_PADRAO = """Prezados(as),

Venho por meio deste e-mail manifestar meu interesse na vaga de {titulo}{empresa_str}.

Sou técnico de TI com experiência em suporte, infraestrutura e desenvolvimento de automações em Python, com atuação em integrações de APIs, Google Workspace, Active Directory e Zeev BPM. Projetos em produção com Docker, processamento paralelo e interfaces gráficas.

Segue em anexo meu currículo para apreciação.

Agradeço a atenção e fico à disposição para uma conversa.

Atenciosamente,
{{NOME}}
{{TELEFONE}} | {{EMAIL}}"""


def extrair_email_candidatura(descricao: str) -> str | None:
    if not descricao:
        return None
    emails = EMAIL_REGEX.findall(descricao)
    for email in emails:
        local = email.split("@")[0].lower()
        if not any(ig in local for ig in EMAILS_IGNORADOS):
            return email
    return None


def montar_assunto(template: str, vaga: dict) -> str:
    return template.format(
        titulo=vaga.get("titulo", ""),
        empresa=vaga.get("empresa", ""),
    )


def montar_corpo(template: str, vaga: dict) -> str:
    empresa = vaga.get("empresa", "")
    empresa_str = f" na {empresa}" if empresa else ""
    return template.format(
        titulo=vaga.get("titulo", ""),
        empresa=vaga.get("empresa", ""),
        empresa_str=empresa_str,
        local=vaga.get("local", ""),
        plataforma=vaga.get("plataforma", ""),
    )


def enviar_candidatura(
    email_destino: str,
    email_remetente: str,
    senha_app: str,
    vaga: dict,
    curriculo_path: str,
    assunto_template: str = ASSUNTO_PADRAO,
    corpo_template: str = CORPO_PADRAO,
) -> tuple[bool, str]:
    """
    Envia candidatura por e-mail com CV anexado.
    Retorna (sucesso: bool, mensagem: str).
    """
    if not os.path.isfile(curriculo_path):
        return False, f"Arquivo nao encontrado: {curriculo_path}"

    try:
        assunto = montar_assunto(assunto_template, vaga)
        corpo   = montar_corpo(corpo_template, vaga)

        msg = MIMEMultipart()
        msg["From"]    = email_remetente
        msg["To"]      = email_destino
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        # Anexar CV
        nome_arquivo = os.path.basename(curriculo_path)
        with open(curriculo_path, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
        msg.attach(parte)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.sendmail(email_remetente, email_destino, msg.as_string())

        return True, f"Candidatura enviada para {email_destino}"

    except Exception as e:
        return False, f"Erro ao enviar: {e}"
