#!/usr/bin/env python3
# ranking_vagas.py — Re-classifica todas as vagas do banco cruzando com o
# perfil real do Diego e gera ranking HTML "mais chances → menos chances".
#
# Uso:
#   python ranking_vagas.py               → gera ranking_vagas.html
#   python ranking_vagas.py --top 100     → só os top-N

import argparse
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH  = Path(__file__).parent / "vagas_vistas.db"
OUT_PATH = Path(__file__).parent / "ranking_vagas.html"

# ---------------------------------------------------------------------------
# Perfil Diego — extraído do CV
# ---------------------------------------------------------------------------

HABILIDADES_FORTES = [
    "python", "automacao", "automação", "automation",
    "infraestrutura", "infrastructure", "suporte", "support",
    "api", "rest", "webhook", "integracao", "integração", "integration",
    "google workspace", "gsuite", "g suite", "active directory",
    "microsoft 365", "m365", "powershell", "bash", "shell",
    "docker", "linux", "git", "sql", "sqlite",
    "zeev", "bpm", "workflow", "rpa", "script",
    "devops", "dev ops", "sre", "platform engineer",
    "backend", "back-end", "back end",
    "django", "flask", "fastapi",
    "chamados", "helpdesk", "service desk", "itsm", "tickets",
    "totvs", "windows server", "azure", "entra", "ansible",
    "terraform", "ci/cd", "pipeline", "monitoring", "monitoramento",
    "ia", "llm", "openai", "anthropic",
]

# Cargos com alta aderência ao perfil (termos no título)
CARGO_ALTO = [
    r"analista.{0,15}(suporte|infra|ti\b|infraestrutura|sistemas|n[o0]c|redes|service)",
    r"(suporte|infraestrutura).{0,15}(jr|junior|pl|pleno|analista)",
    r"tecnico.{0,15}(ti\b|suporte|infra|redes|sistemas)",
    r"(devops|sre|platform).{0,15}(jr|junior|pl|pleno)",
    r"(python|automac|automa[cç]).{0,20}(developer|desenvolvedor|engineer|engenheiro|analista)",
    r"(backend|back.end).{0,15}(jr|junior|pl|pleno|python)",
    r"rpa.{0,20}(jr|junior|desenvolvedor|analista|engineer)",
    r"integracao.{0,20}(analista|developer|engineer)",
    r"ti\b.{0,20}(jr|junior|analista|tecnico)",
    r"helpdesk|service desk|noc",
]

CARGO_MEDIO = [
    r"(desenvolvedor|developer|engineer|engenheiro).{0,25}(jr|junior|pl|pleno)",
    r"analista.{0,20}(dados|data|bi|negocios|negócios)",
    r"(cloud|aws|gcp|azure).{0,20}(jr|junior|engineer|analista)",
    r"(linux|windows).{0,15}(admin|analista|engineer)",
    r"qa|quality assurance|teste|testing",
    r"(full.?stack).{0,15}(jr|junior|pl|pleno)",
    r"administrador.{0,20}(sistemas|redes|ti)",
    r"back.?office.{0,20}(ti|dados|automac)",
]

CARGO_BAIXO = [
    r"data sci|machine learning|ml engineer|deep learning|nlp",
    r"front.?end|frontend|react|angular|vue|next\.js",
    r"mobile|ios|android|flutter|react native",
    r"java\b(?!script).{0,15}(developer|engineer|desenvolvedor)",
    r"\.net|c#|kotlin|swift|ruby|php|golang|rust",
    r"design(er|ux|ui)|product design",
    r"gerente|coordenador|manager|diretor|head of|vp de|lider",
    r"especialista.{0,20}senior|senior.{0,20}especialista",
    r"sales|comercial|vendas|account",
    r"bi developer|tableau developer|power bi developer",
]

# Seniority
SENIOR_RE = re.compile(
    r"\b(s[êe]nior|sr\.?|lead|principal|staff|head|coordenador|gerente|diretor|"
    r"especialista\s+s[êe]nior|vp|arquiteto(?!\s+j[uú]nior))\b", re.I
)
JUNIOR_RE = re.compile(
    r"\b(j[uú]nior|jr\.?|trainee|est[áa]gi[oó]|estagiário|aprendiz|apprentice)\b", re.I
)
PLENO_RE  = re.compile(r"\b(pleno|pl\.?|mid.level|mid\s+level|i{1,3}\b)\b", re.I)


def _senioridade(titulo: str):
    t = titulo.lower()
    if JUNIOR_RE.search(t):  return "junior"
    if PLENO_RE.search(t):   return "pleno"
    if SENIOR_RE.search(t):  return "senior"
    return "nao_informado"


def _score_senioridade(nivel: str) -> int:
    return {"junior": 35, "pleno": 22, "nao_informado": 12, "senior": 3}[nivel]


def _match_cargo(titulo: str) -> str:
    t = titulo.lower()
    for pat in CARGO_ALTO:
        if re.search(pat, t, re.I):
            return "alto"
    for pat in CARGO_MEDIO:
        if re.search(pat, t, re.I):
            return "medio"
    for pat in CARGO_BAIXO:
        if re.search(pat, t, re.I):
            return "baixo"
    return "generico"


def _score_cargo(fit: str) -> int:
    return {"alto": 40, "medio": 28, "generico": 15, "baixo": 3}[fit]


def _score_habilidades_titulo(titulo: str) -> int:
    t = titulo.lower()
    pts = 0
    for h in HABILIDADES_FORTES:
        if h in t:
            pts += 5
    return min(pts, 25)


def calcular_aderencia(row: dict) -> dict:
    titulo   = row["titulo"] or ""
    score_kw = row["score"] or 0        # score original por keywords desc

    nivel    = _senioridade(titulo)
    fit      = _match_cargo(titulo)

    s_sen  = _score_senioridade(nivel)
    s_cargo= _score_cargo(fit)
    s_hab  = _score_habilidades_titulo(titulo)
    s_kw   = int(score_kw * 0.20)       # até 20pts do score de keywords

    total  = s_sen + s_cargo + s_hab + s_kw
    total  = max(0, min(total, 100))

    if   total >= 72: categoria = "Alta"
    elif total >= 48: categoria = "Média"
    else:             categoria = "Baixa"

    return {
        **row,
        "aderencia":  total,
        "categoria":  categoria,
        "senioridade": nivel,
        "fit_cargo":  fit,
        "s_sen":      s_sen,
        "s_cargo":    s_cargo,
        "s_hab":      s_hab,
        "s_kw":       s_kw,
    }


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CAT_COR = {
    "Alta":  ("#166534", "#dcfce7", "#16a34a"),
    "Média": ("#92400e", "#fef3c7", "#d97706"),
    "Baixa": ("#991b1b", "#fee2e2", "#ef4444"),
}

PLAT_COR = {
    "LinkedIn":       "#0a66c2",
    "Gupy":           "#7c3aed",
    "WeWorkRemotely": "#1a7f5a",
    "Remotive":       "#0891b2",
    "Himalayas":      "#be185d",
    "InfoJobs":       "#d97706",
    "ProgramaThor":   "#dc2626",
    "Vagas.com":      "#4f46e5",
    "Indeed":         "#2557a7",
}

SEN_LABEL = {
    "junior":       "Junior/Trainee",
    "pleno":        "Pleno",
    "senior":       "Sênior/Lead",
    "nao_informado":"Não informado",
}

FIT_LABEL = {
    "alto":    "Alta aderência",
    "medio":   "Média aderência",
    "generico":"Genérico",
    "baixo":   "Baixa aderência",
}


def gerar_html(vagas: list[dict], top: int | None) -> str:
    if top:
        vagas = vagas[:top]

    altas  = [v for v in vagas if v["categoria"] == "Alta"]
    medias = [v for v in vagas if v["categoria"] == "Média"]
    baixas = [v for v in vagas if v["categoria"] == "Baixa"]

    def linha(v, i):
        tc, bg, bc = CAT_COR[v["categoria"]]
        pc = PLAT_COR.get(v["plataforma"], "#6b7280")
        url = v["url"] or "#"
        titulo = (v["titulo"] or "")[:70]
        empresa = (v["empresa"] or "—")[:35]
        data = (v["data_vista"] or "")[:10]
        pais_badge = "🌍 WW" if v.get("pais") == "WW" else "🇧🇷 BR"

        return f"""
<tr>
  <td class="rank">{i}</td>
  <td><span class="badge" style="background:{bg};color:{tc};border:1px solid {bc};">{v["aderencia"]}</span></td>
  <td><span class="badge" style="background:{bg};color:{tc};border:1px solid {bc};">{v["categoria"]}</span></td>
  <td class="titulo"><a href="{url}" target="_blank">{titulo}</a></td>
  <td>{empresa}</td>
  <td><span class="badge" style="background:{pc};color:#fff;">{v["plataforma"]}</span></td>
  <td><small>{SEN_LABEL.get(v["senioridade"],"")}</small></td>
  <td><small>{FIT_LABEL.get(v["fit_cargo"],"")}</small></td>
  <td><small>{pais_badge}</small></td>
  <td><small>{data}</small></td>
</tr>"""

    rows_altas  = "".join(linha(v, i+1)     for i, v in enumerate(altas))
    rows_medias = "".join(linha(v, i+1+len(altas)) for i, v in enumerate(medias))
    rows_baixas = "".join(linha(v, i+1+len(altas)+len(medias)) for i, v in enumerate(baixas))

    total = len(vagas)
    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")

    def secao(titulo_sec, cor, rows, qtd):
        if not rows:
            return ""
        return f"""
<tr class="sec-header" style="background:{cor}">
  <td colspan="10" style="padding:10px 16px;font-weight:700;font-size:13px;letter-spacing:.5px;">
    {titulo_sec} — {qtd} vagas
  </td>
</tr>
{rows}"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Ranking de Vagas — Diego Paixão</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Segoe UI",Arial,sans-serif; background:#f1f5f9; color:#1e293b; }}
  .header {{ background:#0f172a; color:#f8fafc; padding:28px 40px; }}
  .header h1 {{ font-size:22px; margin-bottom:4px; }}
  .header p {{ font-size:13px; color:#94a3b8; }}
  .stats {{ display:flex; gap:20px; padding:20px 40px; background:#fff; border-bottom:1px solid #e2e8f0; flex-wrap:wrap; }}
  .stat {{ text-align:center; }}
  .stat .n {{ font-size:28px; font-weight:700; }}
  .stat .l {{ font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:.5px; }}
  .stat.alta .n {{ color:#16a34a; }}
  .stat.media .n {{ color:#d97706; }}
  .stat.baixa .n {{ color:#ef4444; }}
  .nota {{ padding:12px 40px; background:#eff6ff; border-left:4px solid #3b82f6;
           font-size:12px; color:#1e40af; margin:16px 40px; border-radius:4px; }}
  .wrapper {{ padding:0 24px 40px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff;
           border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
  th {{ background:#1e293b; color:#f8fafc; font-size:11px; text-transform:uppercase;
        letter-spacing:.5px; padding:10px 12px; text-align:left; position:sticky; top:0; }}
  td {{ padding:9px 12px; font-size:13px; border-bottom:1px solid #f1f5f9; vertical-align:middle; }}
  tr:hover td {{ background:#f8fafc; }}
  .rank {{ color:#94a3b8; font-size:12px; width:36px; text-align:center; }}
  .titulo a {{ color:#0f172a; text-decoration:none; font-weight:500; }}
  .titulo a:hover {{ color:#2563eb; text-decoration:underline; }}
  .badge {{ display:inline-block; padding:2px 8px; border-radius:999px;
            font-size:11px; font-weight:700; white-space:nowrap; }}
  .sec-header td {{ color:#fff !important; font-size:13px; }}
  @media(max-width:900px){{ .wrapper{{ padding:0 8px 24px; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>Ranking de Vagas — Diego Paixão</h1>
  <p>Gerado em {data_hoje} &nbsp;·&nbsp; {total} vagas classificadas pelo cruzamento com o perfil profissional</p>
</div>
<div class="stats">
  <div class="stat alta"><div class="n">{len(altas)}</div><div class="l">Alta chance</div></div>
  <div class="stat media"><div class="n">{len(medias)}</div><div class="l">Média chance</div></div>
  <div class="stat baixa"><div class="n">{len(baixas)}</div><div class="l">Baixa chance</div></div>
  <div class="stat"><div class="n" style="color:#3b82f6">{total}</div><div class="l">Total analisadas</div></div>
</div>
<div class="nota">
  <b>Como o score de aderência é calculado:</b>
  Seniority fit (até 35 pts) + Fit de cargo/área (até 40 pts) + Habilidades no título (até 25 pts) + Score de keywords original (até 20 pts).
  Vagas de Alta chance (≥72) batem diretamente com seu perfil de Analista TI Jr / Python / Automação / Infra.
  Score de keywords original vem do matcher.py e considera também a descrição completa da vaga (só disponível no momento da busca).
</div>
<div class="wrapper">
<table>
<thead>
<tr>
  <th>#</th><th>Score</th><th>Categoria</th><th>Título</th>
  <th>Empresa</th><th>Plataforma</th><th>Seniority</th>
  <th>Fit de Cargo</th><th>País</th><th>Data</th>
</tr>
</thead>
<tbody>
{secao("🟢  ALTA CHANCE", "#166534", rows_altas, len(altas))}
{secao("🟡  MÉDIA CHANCE", "#92400e", rows_medias, len(medias))}
{secao("🔴  BAIXA CHANCE — incluídas para referência", "#991b1b", rows_baixas, len(baixas))}
</tbody>
</table>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=None,
                        help="Limitar a N vagas no relatório (padrão: todas)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT url, titulo, empresa, plataforma, score, data_vista,
               idioma, idioma_obrigatorio, pais, distancia_km
        FROM vagas_vistas
        WHERE titulo NOT LIKE '%PCD%'
          AND titulo NOT LIKE '%pcd%'
          AND titulo NOT LIKE '%defici%'
        ORDER BY score DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    print(f"Analisando {len(rows)} vagas...", flush=True)

    classificadas = [calcular_aderencia(r) for r in rows]
    classificadas.sort(key=lambda v: (-v["aderencia"], -v["score"]))

    html = gerar_html(classificadas, args.top)
    OUT_PATH.write_text(html, encoding="utf-8")

    altas  = sum(1 for v in classificadas if v["categoria"] == "Alta")
    medias = sum(1 for v in classificadas if v["categoria"] == "Média")
    baixas = sum(1 for v in classificadas if v["categoria"] == "Baixa")

    print(f"Alta chance  : {altas}")
    print(f"Media chance : {medias}")
    print(f"Baixa chance : {baixas}")
    print(f"Relatorio    : {OUT_PATH}")

    top5 = classificadas[:5]
    print()
    print("Top 5:")
    for i, v in enumerate(top5, 1):
        print(f"  {i}. [{v['aderencia']}] {v['titulo'][:60]} ({v['plataforma']})")


if __name__ == "__main__":
    main()
