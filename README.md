# Job Search Automation — Desktop App

Aplicativo desktop que busca vagas de emprego em **8 plataformas simultaneamente**, classifica cada vaga por aderência ao perfil via sistema de score customizável, e permite enviar candidaturas por e-mail com CV anexado direto pela interface — sem abrir o navegador.

**Stack:** Python 3.13 · CustomTkinter · SQLite · BeautifulSoup · Playwright

---

## Funcionalidades

- **Busca multi-plataforma** — 8 fontes em paralelo: APIs públicas, RSS, scraping e Playwright
- **Score de aderência** — cada vaga recebe 0–100 pontos baseado em palavras-chave do perfil
- **Filtros em tempo real** — score mínimo (slider), modalidade, só vagas com e-mail direto
- **Candidatura integrada** — envia e-mail com CV anexado sem sair do app
- **Histórico SQLite** — evita duplicatas entre sessões, registra candidaturas enviadas
- **Loading progressivo** — cards aparecem conforme cada fonte vai respondendo
- **Exportável como .exe** — `build_exe.py` gera binário standalone via PyInstaller

---

## Fontes de vagas

| Fonte | Tipo | Foco |
|---|---|---|
| Remotive | API pública | Vagas remotas globais |
| WeWorkRemotely | RSS (3 feeds) | Dev, DevOps, Backend |
| Himalayas | API pública | Filtro por Brasil |
| Gupy | API oficial | ATS brasileiro |
| InfoJobs | Scraping | Brasil |
| ProgramaThor | Scraping | Devs brasileiros |
| LinkedIn | Scraping (página pública) | Geral |
| Vagas.com | Playwright (JS) | Brasil |

---

## Sistema de score

Cada vaga é pontuada automaticamente com base no perfil configurado em `config.py`:

| Seção | Exemplos | Peso |
|---|---|---|
| Título | `python`, `devops`, `automacao` | 18–25 pts |
| Descrição | `powershell`, `docker`, `api`, `itsm` | 5–15 pts |
| Penalização | `react`, `java`, `mobile`, `frontend` | −5 a −10 pts |
| Modalidade | Remoto +15, Híbrido +10 | bônus |

Score mínimo padrão: **20 pontos** (ajustável pelo slider na interface).

---

## Estrutura

```
.
├── app.py              # Interface principal (CustomTkinter dark theme)
├── config.py           # Perfil profissional, keywords, pesos de score
├── matcher.py          # Cálculo de score por vaga
├── banco.py            # SQLite: deduplicação e histórico
├── aplicador.py        # Envio de candidatura via Gmail SMTP
├── notificador.py      # Digest HTML por e-mail com lista de vagas
├── main.py             # CLI alternativa (sem interface gráfica)
├── build_exe.py        # Gera AutomacaoVagas.exe via PyInstaller
├── requirements.txt
├── .env.example        # Template de variáveis de ambiente
└── vagas/
    ├── gupy.py
    ├── remotive.py
    ├── weworkremotely.py
    ├── himalayas.py
    ├── infojobs.py
    ├── programathor.py
    ├── linkedin.py
    └── vagas_com.py    # Playwright — requer Chromium instalado
```

---

## Como configurar

```bash
# 1. Dependências
pip install -r requirements.txt
playwright install chromium  # só se for usar Vagas.com

# 2. Variáveis de ambiente
cp .env.example .env
# Preencher GMAIL_APP_PASSWORD

# 3. Personalizar perfil
# Editar config.py: keywords, pesos de score, cidade, e-mail
```

---

## Como usar

```bash
pythonw app.py   # abre sem terminal (produção)
python app.py    # abre com terminal (debug)
```

Para gerar executável standalone:
```bash
python build_exe.py
# Saída: dist/AutomacaoVagas/AutomacaoVagas.exe
```

---

## Como adicionar uma nova fonte de vagas

1. Criar `vagas/nova_fonte.py` com função `buscar() -> list[dict]`
2. Cada vaga deve ter: `titulo, empresa, local, modalidade, url, descricao, data, plataforma`
3. `modalidade` deve ser: `"Remoto"`, `"Hibrido"` ou `"Presencial"`
4. Adicionar na lista `FONTES` dentro de `_worker_busca()` em `app.py`

---

## Dependências

```
requests
beautifulsoup4
python-dotenv
customtkinter
playwright
pyinstaller
```
