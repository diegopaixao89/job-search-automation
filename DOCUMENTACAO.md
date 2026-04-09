# Automação de Vagas — Documentação Completa
**Criado em:** 2026-04-08  
**Autor:** Diego Mendonça Paixão  
**Stack:** Python 3.13 · CustomTkinter · SQLite · BeautifulSoup · Playwright  

---

## O que é

Aplicativo desktop que busca vagas de emprego em 8 plataformas simultaneamente, filtra por aderência ao perfil profissional via sistema de score, e permite enviar candidatura por e-mail com CV anexado diretamente da interface.

---

## Como executar

```bash
cd "C:\Users\diego.paixao\Desktop\Projetos IA\automacao-vagas"
pythonw app.py          # abre sem terminal (produção)
python app.py           # abre com terminal (debug — mostra erros)
```

---

## Estrutura de arquivos

```
automacao-vagas/
├── app.py              # Interface gráfica principal (CustomTkinter)
├── config.py           # Perfil profissional, palavras-chave, pesos de score
├── matcher.py          # Calcula score de aderência de cada vaga
├── banco.py            # SQLite: deduplicação e histórico de candidaturas
├── aplicador.py        # Envio de candidatura por e-mail (Gmail SMTP)
├── notificador.py      # Digest HTML por e-mail com lista de vagas
├── tradutor.py         # Tradução automática PT-BR (não usada na interface)
├── main.py             # CLI alternativa (sem interface gráfica)
├── build_exe.py        # Script para gerar AutomacaoVagas.exe
├── requirements.txt    # Dependências Python
├── .env                # Senha do Gmail (não commitar!)
├── vagas_vistas.db     # SQLite gerado automaticamente
└── vagas/
    ├── gupy.py         # API oficial Gupy
    ├── remotive.py     # API pública Remotive
    ├── weworkremotely.py  # RSS WeWorkRemotely (3 feeds)
    ├── himalayas.py    # API pública Himalayas
    ├── infojobs.py     # Scraping InfoJobs Brasil
    ├── programathor.py # Scraping ProgramaThor
    ├── linkedin.py     # Scraping LinkedIn (página pública)
    └── vagas_com.py    # Playwright (site JS) — requer browser instalado
```

---

## Arquivo .env

```
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

Gerar em: Google → Conta → Segurança → Senhas de app  
**Nunca commitar esse arquivo.**

---

## Sistema de score (config.py)

Cada vaga recebe pontuação de 0–100 baseada em palavras-chave:

| Seção | Exemplo | Peso |
|-------|---------|------|
| Título | `python`, `devops`, `automacao` | 18–25 pts |
| Descrição | `powershell`, `docker`, `zeev`, `api` | 5–15 pts |
| Penalização | `react`, `java`, `mobile`, `frontend` | −5 a −10 pts |
| Modalidade | Remoto +15, Híbrido +10 | bônus |

Score mínimo padrão: **20 pontos** (ajustável pelo slider na interface).

---

## Fontes de vagas (ordem de busca)

| Fonte | Tipo | Velocidade | Notas |
|-------|------|-----------|-------|
| Remotive | API | Rápida | Vagas remotas globais |
| WeWorkRemotely | RSS | Rápida | 3 categorias: dev, devops, backend |
| Himalayas | API | Rápida | Filtra por Brasil ou sem restrição |
| Gupy | API | Rápida | Plataforma brasileira de ATS |
| InfoJobs | Scraping | Média | 7 termos × 2 locais |
| ProgramaThor | Scraping | Média | Foco em devs brasileiros |
| LinkedIn | Scraping | Lenta | Página pública, sem login |
| Vagas.com | Playwright | Lenta | Requer Chromium instalado |

---

## Interface (app.py)

### Fluxo de busca
1. Usuário clica **Buscar Vagas**
2. Thread de background busca cada fonte sequencialmente
3. Após cada fonte, `_fonte_ok()` é chamado no main thread via `after(0, ...)`
4. Cards são adicionados ao scroll à medida que chegam (sem esperar todas as fontes)
5. Ao final, `_busca_completa()` atualiza o status

### Componentes principais
- **`CardVaga`** — card de cada vaga com: score colorido, modalidade, plataforma, botões
- **`PainelCandidatura`** — modal para enviar e-mail com CV anexado
- **`App`** — janela principal com sidebar + lista de cards + log

### Bug crítico corrigido (2026-04-08)
**Problema:** `CardVaga` estendia `ctk.CTkFrame` e definia um método chamado `_draw()`.  
O CustomTkinter chama internamente `self._draw(no_color_updates=True)` ao inicializar qualquer frame.  
Como o `_draw` customizado não aceita esse argumento, gerava `TypeError` silencioso (com `pythonw`, exceções em callbacks Tkinter são descartadas sem mostrar nada).  
**Solução:** renomear o método de `_draw` para `_build`.

```python
# ERRADO — conflita com método interno do CustomTkinter
class CardVaga(ctk.CTkFrame):
    def _draw(self): ...

# CORRETO
class CardVaga(ctk.CTkFrame):
    def _build(self): ...
```

### Filtros disponíveis
- **Score mínimo** — slider 0–80, padrão 20
- **Modalidade** — Remoto / Híbrido / Presencial (checkboxes)
- **Só com e-mail direto** — exibe só vagas onde e-mail de candidatura foi detectado

### Envio de candidatura
Só funciona para vagas onde um e-mail foi encontrado na descrição.  
Configura assunto e corpo antes de enviar. CV em PDF ou DOCX.  
Usa Gmail SMTP SSL porta 465 com senha de app (não senha da conta).

---

## Gerar .exe (para usar em outro PC)

```bash
cd "C:\Users\diego.paixao\Desktop\Projetos IA\automacao-vagas"
python build_exe.py
```

- Saída: `dist/AutomacaoVagas/AutomacaoVagas.exe`
- Copiar a **pasta inteira** `dist/AutomacaoVagas/` para o outro PC
- O `.env` é copiado automaticamente pelo script
- **Vagas.com** não funciona sem instalar Playwright no destino:
  ```
  pip install playwright
  playwright install chromium
  ```
- As outras 7 fontes funcionam sem instalar nada

---

## Banco de dados (vagas_vistas.db)

Criado automaticamente na mesma pasta do app.

```sql
-- Vagas já vistas (deduplicação entre sessões)
vagas_vistas(url, titulo, empresa, plataforma, score, data_vista)

-- Histórico de candidaturas enviadas
candidaturas(url, titulo, empresa, email_destino, curriculo, data_envio, status)
```

---

## Dependências (requirements.txt)

```
requests
beautifulsoup4
python-dotenv
customtkinter
playwright
```

Instalar tudo:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Alterações futuras comuns

### Adicionar nova fonte de vagas
1. Criar `vagas/nova_fonte.py` com função `buscar() -> list[dict]`
2. Cada vaga deve ter: `titulo, empresa, local, modalidade, url, descricao, data, plataforma`
3. `modalidade` deve ser exatamente: `"Remoto"`, `"Hibrido"` ou `"Presencial"`
4. Adicionar a fonte na lista `FONTES` em `_worker_busca()` no `app.py`

### Ajustar palavras-chave do perfil
Editar `config.py`:
- `TITULO_PESOS` — palavras no título da vaga (peso maior)
- `DESCRICAO_PESOS` — palavras na descrição (peso menor)
- `PENALIZACOES` — tecnologias fora do perfil (valores negativos)
- `SCORE_MINIMO` — mínimo padrão exibido na interface

### Alterar template de e-mail
Editar `aplicador.py`:
- `ASSUNTO_PADRAO` — template do assunto
- `CORPO_PADRAO` — template do corpo (suporta `{titulo}`, `{empresa}`, `{empresa_str}`)

---

## Histórico de sessão (2026-04-08)

1. Projeto criado com 4 fontes iniciais (Gupy, Remotive, LinkedIn, ProgramaThor)
2. Expandido para 8 fontes: + WeWorkRemotely, Himalayas, InfoJobs, Vagas.com
3. Sistema de score refinado com perfil completo (TOTVS, RPA, Zeev, ITSM, N2/N3...)
4. Interface gráfica CustomTkinter dark criada do zero
5. Sistema de candidatura por e-mail com CV anexado
6. Módulo de tradução automático criado (PT-BR via Google Translate + cache SQLite)
7. Interface redesenhada: cards com barra de score colorida, badges de plataforma/modalidade
8. Bug crítico identificado e corrigido: `_draw` → `_build` (conflito com CustomTkinter interno)
9. Loading progressivo implementado: cards aparecem conforme cada fonte termina
10. Script `build_exe.py` criado para distribuição sem Python instalado
