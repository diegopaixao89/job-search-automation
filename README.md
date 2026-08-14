# CaçaVagas

Aplicativo que busca vagas em **8 fontes na interface e até 9 na automação diária**, classifica cada oportunidade pelos perfis Infra/Suporte e Automação/Dev e permite enviar candidaturas por e-mail com CV anexado.

**Stack:** Python 3.11+ · CustomTkinter · SQLite · BeautifulSoup · Playwright · Google Gemini

![CI](https://github.com/diegopaixao89/job-search-automation/actions/workflows/ci.yml/badge.svg)

---

## Screenshots

> Interface principal — 3 abas de resultados, badges de score e modalidade, filtros em tempo real

![App desktop com lista de vagas](docs/screenshots/app-main.png)

> Painel de análise de currículo com IA — pontos fortes, dicas e termos sugeridos

![Painel de análise de CV](docs/screenshots/analise-cv.png)

---

## Funcionalidades

- **Busca multi-plataforma** — 8 fontes na interface e uma fonte adicional no digest diário
- **Análise de currículo com IA** — envia o PDF para o Gemini (ou usa IA local via Ollama, ou NLP offline) e extrai perfil, palavras-chave, pontos fortes e dicas de melhoria
- **Perfil dinâmico** — um CV analisado complementa os dois perfis padrão; não apaga a trilha Infra nem a trilha Dev
- **3 abas de resultados** — Todas · Nacionais 🇧🇷 · Internacional 🌍, priorizadas por aderência
- **Score de aderência** — cada vaga recebe 0–100 pontos com base nas keywords do perfil
- **Badges visuais** — modalidade (Remoto/Híbrido/Presencial), idioma (EN), inglês obrigatório, distância em km
- **Geocodificação em background** — calcula distância até vagas presenciais/híbridas usando Nominatim (gratuito, sem API key)
- **Filtros em tempo real** — score mínimo, modalidade, idioma, país, só vagas com e-mail
- **Candidatura integrada** — envia e-mail com CV anexado sem sair do app
- **Histórico SQLite** — evita duplicatas entre sessões, registra candidaturas enviadas
- **Loading progressivo** — cards aparecem conforme cada fonte vai respondendo
- **Wizard de primeiro uso** — na primeira abertura pede e-mail e cidade, salva no `.env`
- **Instalador one-click** — gerado com Inno Setup, inclui Python 3.11, deps e Playwright

---

## Fontes de vagas

| Fonte | Tipo | Foco |
|---|---|---|
| Remotive | API pública | Vagas remotas globais (`pais: WW`) |
| WeWorkRemotely | RSS (3 feeds) | Dev, DevOps, Backend (`pais: WW`) |
| Himalayas | API pública | Filtro por Brasil ou global (`pais: WW`) |
| Gupy | Endpoint público do portal | ATS brasileiro (`pais: BR`) |
| Indeed | Integração opcional | Desativada por padrão; requer acesso autorizado |
| InfoJobs | Scraping | Brasil (`pais: BR`) |
| ProgramaThor | Scraping | Devs brasileiros (`pais: BR`) |
| LinkedIn | Scraping (página pública) | BR ou WW por localização |
| Vagas.com | Playwright (JS renderizado) | Brasil (`pais: BR`) |

---

## Análise de currículo — fluxo de IA

O sistema usa três motores em cascata, sem necessidade de configuração:

```
1. Google Gemini 2.5 Flash  ←  GEMINI_API_KEY no .env (gratuito, sem cartão)
        ↓ se sem chave ou erro
2. Ollama local             ←  llama3.2 / gemma2 / qwen2.5 (detectado automaticamente)
        ↓ se Ollama não instalado
3. NLP offline              ←  regex + lista de keywords (funciona sem internet)
```

O resultado retorna JSON com: `cargo_atual`, `habilidades`, `termos_busca_sugeridos`, `titulo_pesos_sugeridos`, `penalizacoes_sugeridas`, `dicas_melhoria`, `pontos_fortes`, `palavras_chave_ausentes`.

---

## Sistema de score

Cada vaga é pontuada automaticamente. Com perfil do config.py (padrão) ou com perfil extraído do CV:

| Seção | Exemplos | Peso |
|---|---|---|
| Título | cargo alinhado a Infra/Suporte ou Automação/Dev | até 40 pts |
| Descrição | `Python`, APIs, IAM, Google Workspace, ITSM, Docker | até 40 pts |
| Bloqueios | senioridade alta ou outra família (QA, SAP, dados etc.) | score 0 |
| Modalidade | Remoto +4, Híbrido +3, Presencial +3 | bônus leve |

Score mínimo padrão: **40 pontos** (ajustável pelo slider na interface).

### Critérios atuais de seleção

- **Dois perfis independentes** — Infra/Suporte e Automação/Dev, derivados dos dois currículos sem versionar dados pessoais.
- **Aderência final** — usa o maior score entre os dois perfis; competências das duas trilhas não são somadas artificialmente.
- **Presencial e híbrido** — somente vagas com cidade do Rio de Janeiro confirmada no anúncio. Estado do RJ, Região Metropolitana, cidades vizinhas e local ambíguo são rejeitados.
- **Remoto** — aceita vagas nacionais e internacionais; eventuais restrições de país/região continuam visíveis no campo de localização.
- **Corte padrão** — 40 pontos; modalidade concede apenas bônus leve e não faz uma vaga tecnicamente irrelevante passar.
- **Ordenação** — aderência primeiro, modalidade apenas como desempate.

---

## Estrutura

```
.
├── app.py                  # Interface principal (CustomTkinter dark theme)
├── config.py               # Perfil profissional, keywords, pesos de score
├── perfis_busca.py         # Perfis sanitizados derivados dos CVs Infra e Dev
├── filtros_vagas.py        # Modalidade e filtro geográfico da cidade do Rio
├── matcher.py              # Cálculo de score — suporta perfil dinâmico do CV
├── banco.py                # SQLite: deduplicação, histórico, geocache, cache de CV
├── curriculo_parser.py     # Extrai texto do PDF + analisa com Gemini/Ollama/NLP
├── detector_idioma.py      # Detecta idioma da vaga e inglês obrigatório
├── geolocalizador.py       # Geocodifica endereços (Nominatim), calcula distância
├── aplicador.py            # Envio de candidatura via Gmail SMTP
├── notificador.py          # Digest HTML por e-mail com lista de vagas
├── main.py                 # CLI alternativa (sem interface gráfica)
├── rodar_automatico.py     # Automação headless: busca + score + envio
├── setup.iss               # Script Inno Setup — gera instalador .exe
├── iniciar.bat             # Launcher robusto (localiza pythonw em múltiplos paths)
├── _instalar_deps.bat      # Instala pip + Playwright após instalação pelo wizard
├── gerar_icone.py          # Gera icone.ico via Pillow
├── requirements.txt
├── .env.exemplo            # Template de variáveis de ambiente
└── vagas/
    ├── gupy.py
    ├── indeed.py
    ├── remotive.py
    ├── weworkremotely.py
    ├── himalayas.py
    ├── infojobs.py
    ├── programathor.py
    ├── linkedin.py
    └── vagas_com.py        # Playwright — requer Chromium instalado
```

---

## Como configurar

```bash
# 1. Dependências
pip install -r requirements.txt
playwright install chromium

# 2. Variáveis de ambiente
cp .env.exemplo .env
# Preencher: EMAIL_REMETENTE, EMAIL_DESTINO, GMAIL_APP_PASSWORD, CIDADE, ESTADO
# GEMINI_API_KEY é opcional — sem ela usa Ollama ou NLP local
```

**Como gerar o Gmail App Password:**
Conta Google → Segurança → Verificação em duas etapas → Senhas de app

**Como obter chave Gemini (gratuita):**
`aistudio.google.com/app/apikey` — sem cartão de crédito, 15 req/min free

---

## Como usar

```bash
pythonw app.py   # abre sem terminal (produção)
python app.py    # abre com terminal (debug)
```

---

## Distribuição (instalador Windows)

Para gerar o instalador one-click para usuários finais:

```
1. Baixar python-3.11.9-amd64.exe e colocar na raiz do projeto
2. Instalar Inno Setup 6 (jrsoftware.org/isdl.php)
3. Abrir setup.iss no Inno Setup e compilar (Ctrl+F9)
4. Distribuir: Output\CacaVagas_Setup.exe
```

O instalador instala Python 3.11 (se necessário), todas as dependências e o Playwright Chromium automaticamente. O usuário só clica em "Avançar".

---

## Como adicionar uma nova fonte de vagas

1. Criar `vagas/nova_fonte.py` com função `buscar() -> list[dict]`
2. Cada vaga deve ter: `titulo, empresa, local, modalidade, url, descricao, data, plataforma, pais`
3. `modalidade`: `"Remoto"`, `"Hibrido"` ou `"Presencial"`
4. `pais`: `"BR"` (nacional) ou `"WW"` (internacional)
5. Adicionar na lista `FONTES` dentro de `_worker_busca()` em `app.py`

---

## Testes

```bash
pytest tests/
```

---

## Dependências

```
requests · beautifulsoup4 · python-dotenv · customtkinter · playwright
pdfplumber · google-genai · fast-langdetect · geopy · haversine · pillow
```
