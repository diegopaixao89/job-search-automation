# app.py — CaçaVagas — interface CustomTkinter moderna
# -*- coding: utf-8 -*-

import os, sys, threading, webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import EMAIL_REMETENTE, EMAIL_DESTINO, TERMOS_BUSCA, SCORE_MINIMO
from matcher import calcular_score
import banco, notificador, aplicador
import curriculo_parser
from detector_idioma import enriquecer_vaga

# ── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta
BG        = "#080e1a"
BG2       = "#0d1527"
BG3       = "#111d35"
CARD      = "#131e32"
CARD2     = "#182644"
BORDER    = "#1e2f4a"
BLUE      = "#3b82f6"
BLUE2     = "#2563eb"
BLUE_DIM  = "#1e3a5f"
GREEN     = "#22c55e"
GREEN_DIM = "#14532d"
YELLOW    = "#f59e0b"
YELLOW_DIM= "#78350f"
RED       = "#ef4444"
RED_DIM   = "#7f1d1d"
MUTED     = "#334155"
TEXT      = "#e2e8f0"
TEXT2     = "#94a3b8"
TEXT3     = "#64748b"

CURRICULO_PADRAO = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "curriculo_diego_paixao.pdf"
))

# ── Helpers ───────────────────────────────────────────────────────────────────

def cor_score(s):
    if s >= 70: return GREEN,  GREEN_DIM
    if s >= 40: return BLUE,   BLUE_DIM
    if s >= 20: return YELLOW, YELLOW_DIM
    return TEXT3, MUTED

def cor_modalidade(m):
    return {
        "Remoto":    (GREEN,  GREEN_DIM,  "🌐  Remoto"),
        "Hibrido":   (BLUE,   BLUE_DIM,   "🔀  Híbrido"),
        "Presencial":(YELLOW, YELLOW_DIM, "📍  Presencial"),
    }.get(m, (TEXT3, MUTED, m))

def plat_cor(p):
    return {
        "LinkedIn":       "#0a66c2",
        "Gupy":           "#7c3aed",
        "WeWorkRemotely": "#1a7f5a",
        "Remotive":       "#0891b2",
        "Himalayas":      "#be185d",
        "InfoJobs":       "#d97706",
        "ProgramaThor":   "#dc2626",
        "Vagas.com":      "#4f46e5",
    }.get(p, MUTED)


# ── Widget: Separador ─────────────────────────────────────────────────────────

class Sep(ctk.CTkFrame):
    def __init__(self, p, **kw):
        super().__init__(p, height=1, fg_color=BORDER, **kw)


# ── Card de Vaga ──────────────────────────────────────────────────────────────

class CardVaga(ctk.CTkFrame):
    def __init__(self, parent, vaga, app, **kw):
        super().__init__(parent, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        self.vaga = vaga
        self.app  = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        v          = self.vaga
        score      = v.get("score", 0)
        modalidade = v.get("modalidade", "")
        email_app  = v.get("_email_candidatura")
        ja_aplic   = banco.ja_aplicou(v.get("url", ""))
        sc, sc_bg  = cor_score(score)
        mc, mc_bg, mlabel = cor_modalidade(modalidade)
        pc         = plat_cor(v.get("plataforma", ""))
        titulo_orig= v.get("_titulo_original", "")

        bar = ctk.CTkFrame(self, width=4, fg_color=sc, corner_radius=0)
        bar.grid(row=0, column=0, rowspan=6, sticky="ns")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=1, sticky="nsew", padx=(12, 14), pady=(12, 10))
        inner.grid_columnconfigure(0, weight=1)

        # ── Badges ──
        badges = ctk.CTkFrame(inner, fg_color="transparent")
        badges.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(badges, text=f"  {score}  ",
                     fg_color=sc_bg, text_color=sc,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     corner_radius=6).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(badges, text=f"  {mlabel}  ",
                     fg_color=mc_bg, text_color=mc,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     corner_radius=6).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(badges, text=f"  {v.get('plataforma','')}  ",
                     fg_color=pc, text_color="white",
                     font=ctk.CTkFont(size=10),
                     corner_radius=6).pack(side="left", padx=(0, 5))

        # Badge idioma inglês
        if v.get("idioma") == "en":
            ctk.CTkLabel(badges, text="  🌐 EN  ",
                         fg_color=BLUE2, text_color="white",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="left", padx=(0, 5))

        # Badge inglês obrigatório
        if v.get("idioma_obrigatorio") == "en":
            ctk.CTkLabel(badges, text="  ⚠ Inglês req.  ",
                         fg_color=YELLOW_DIM, text_color=YELLOW,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="left", padx=(0, 5))

        # Badge distância
        distancia = v.get("distancia_km")
        if distancia is not None:
            d_fg = GREEN if distancia < 30 else (YELLOW if distancia < 100 else RED)
            d_bg = GREEN_DIM if distancia < 30 else (YELLOW_DIM if distancia < 100 else RED_DIM)
            ctk.CTkLabel(badges, text=f"  📍 {distancia:.0f} km  ",
                         fg_color=d_bg, text_color=d_fg,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="left", padx=(0, 5))

        # Badge aplicado / e-mail
        if ja_aplic:
            ctk.CTkLabel(badges, text="  ✓ Aplicado  ",
                         fg_color=GREEN_DIM, text_color=GREEN,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="right")
        elif email_app:
            ctk.CTkLabel(badges, text="  📧 E-mail direto  ",
                         fg_color="#1e3a5f", text_color="#60a5fa",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="right")

        # ── Título ──
        titulo_display = v.get("titulo", "")[:90]
        ctk.CTkLabel(inner, text=titulo_display,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT, anchor="w", wraplength=540, justify="left"
                     ).grid(row=1, column=0, sticky="ew", pady=(6, 0))

        if titulo_orig and titulo_orig != titulo_display:
            ctk.CTkLabel(inner, text=f"Original: {titulo_orig[:70]}",
                         font=ctk.CTkFont(size=10), text_color=TEXT3, anchor="w"
                         ).grid(row=2, column=0, sticky="ew")

        meta_partes = [p for p in [v.get("empresa"), v.get("local"), (v.get("data") or "")[:10]] if p]
        ctk.CTkLabel(inner, text="  ·  ".join(meta_partes),
                     font=ctk.CTkFont(size=11), text_color=TEXT2, anchor="w"
                     ).grid(row=3, column=0, sticky="ew", pady=(2, 0))

        if email_app:
            ctk.CTkLabel(inner, text=f"📧  {email_app}",
                         font=ctk.CTkFont(size=11), text_color="#60a5fa", anchor="w"
                         ).grid(row=4, column=0, sticky="ew", pady=(4, 0))

        # ── Botões ──
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.grid(row=5, column=0, sticky="w", pady=(8, 0))

        if email_app and not ja_aplic:
            ctk.CTkButton(btns, text="Aplicar por E-mail  📎",
                          fg_color=GREEN, hover_color="#16a34a",
                          font=ctk.CTkFont(size=12, weight="bold"),
                          height=32, width=185, corner_radius=8,
                          command=lambda: self.app.abrir_candidatura(self.vaga, email_app, self)
                          ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btns, text="Ver Vaga  →",
                      fg_color=BLUE2, hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=12),
                      height=32, width=110, corner_radius=8,
                      command=lambda: webbrowser.open(v.get("url", ""))
                      ).pack(side="left")

    def refresh(self):
        if not self.winfo_exists():
            return
        for w in self.winfo_children():
            w.destroy()
        self._build()


# ── Painel de Candidatura ─────────────────────────────────────────────────────

class PainelCandidatura(ctk.CTkToplevel):
    def __init__(self, parent, vaga, email_dest, cv_path, remetente, senha, on_ok):
        super().__init__(parent)
        self.title("Enviar Candidatura")
        self.geometry("600x580")
        self.resizable(False, False)
        self.configure(fg_color=BG2)
        self.grab_set()
        self.vaga       = vaga
        self.email_dest = email_dest
        self.cv_path    = cv_path
        self.remetente  = remetente
        self.senha      = senha
        self.on_ok      = on_ok
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        pad = {"padx": 24, "sticky": "ew"}

        ctk.CTkLabel(self, text="Enviar Candidatura",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, **pad, pady=(20, 2))

        ctk.CTkLabel(self, text=f"Para: {self.email_dest}",
                     font=ctk.CTkFont(size=12), text_color=BLUE
                     ).grid(row=1, column=0, **pad)

        ctk.CTkLabel(self, text=f"Vaga: {self.vaga.get('titulo','')[:70]}",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=2, column=0, **pad, pady=(0, 12))

        Sep(self).grid(row=3, column=0, **pad, pady=(0, 12))

        cv_row = ctk.CTkFrame(self, fg_color="transparent")
        cv_row.grid(row=4, column=0, **pad, pady=(0, 10))
        cv_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cv_row, text="Currículo anexado:",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT
                     ).grid(row=0, column=0, sticky="w")

        self.lbl_cv = ctk.CTkLabel(cv_row, text=os.path.basename(self.cv_path),
                                    font=ctk.CTkFont(size=12), text_color=BLUE)
        self.lbl_cv.grid(row=1, column=0, sticky="w")

        ctk.CTkButton(cv_row, text="Trocar", width=80, height=28,
                      fg_color=CARD2, corner_radius=6,
                      command=self._trocar).grid(row=1, column=1, padx=(8, 0))

        ctk.CTkLabel(self, text="Assunto:",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT
                     ).grid(row=5, column=0, **pad, pady=(4, 0))

        self.entry_assunto = ctk.CTkEntry(self, height=36, font=ctk.CTkFont(size=12),
                                          fg_color=CARD, border_color=BORDER)
        self.entry_assunto.insert(0, aplicador.montar_assunto(aplicador.ASSUNTO_PADRAO, self.vaga))
        self.entry_assunto.grid(row=6, column=0, **pad, pady=(4, 10))

        ctk.CTkLabel(self, text="Corpo:",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT
                     ).grid(row=7, column=0, **pad)

        self.txt = ctk.CTkTextbox(self, height=190, font=ctk.CTkFont(size=11),
                                   fg_color=CARD, border_color=BORDER, border_width=1)
        self.txt.insert("0.0", aplicador.montar_corpo(aplicador.CORPO_PADRAO, self.vaga))
        self.txt.grid(row=8, column=0, **pad, pady=(4, 14))

        Sep(self).grid(row=9, column=0, **pad, pady=(0, 14))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=10, column=0, **pad, pady=(0, 20))

        self.btn_env = ctk.CTkButton(btns, text="Enviar Candidatura  📎",
                                     fg_color=GREEN, hover_color="#16a34a",
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     height=38, corner_radius=8,
                                     command=self._enviar)
        self.btn_env.pack(side="left", padx=(0, 10))

        ctk.CTkButton(btns, text="Cancelar",
                      fg_color=CARD2, hover_color=MUTED,
                      height=38, corner_radius=8,
                      command=self.destroy).pack(side="left")

    def _trocar(self):
        p = filedialog.askopenfilename(filetypes=[("PDF/Word", "*.pdf *.docx *.doc"), ("Todos", "*.*")])
        if p:
            self.cv_path = p
            self.lbl_cv.configure(text=os.path.basename(p))

    def _enviar(self):
        self.btn_env.configure(text="Enviando...", state="disabled")
        assunto = self.entry_assunto.get()
        corpo   = self.txt.get("0.0", "end").strip()

        def worker():
            ok, msg = aplicador.enviar_candidatura(
                self.email_dest, self.remetente, self.senha,
                self.vaga, self.cv_path, assunto, corpo)
            self.after(0, lambda: self._pos(ok, msg))

        threading.Thread(target=worker, daemon=True).start()

    def _pos(self, ok, msg):
        if ok:
            banco.registrar_candidatura(
                self.vaga.get("url", ""), self.vaga.get("titulo", ""),
                self.vaga.get("empresa", ""), self.email_dest, self.cv_path)
            messagebox.showinfo("Enviado!", msg, parent=self)
            self.on_ok()
            self.destroy()
        else:
            messagebox.showerror("Erro", msg, parent=self)
            self.btn_env.configure(text="Enviar Candidatura  📎", state="normal")


# ── Tela de Boas-vindas (primeira execução) ───────────────────────────────────

class PainelPrimeiroUso(ctk.CTkToplevel):
    """Exibida na primeira execução para configurar e-mail e cidade."""

    def __init__(self, parent, on_salvo):
        super().__init__(parent)
        self.title("Bem-vindo — Configuração inicial")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=BG2)
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # impede fechar sem salvar
        self.grab_set()
        self.on_salvo = on_salvo
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        pad = {"padx": 32, "sticky": "ew"}

        ctk.CTkLabel(self, text="Bem-vindo ao CaçaVagas!",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, **pad, pady=(28, 6))

        ctk.CTkLabel(self,
                     text="Informe seus dados abaixo para começar.\nVocê pode alterar isso a qualquer momento nas configurações.",
                     font=ctk.CTkFont(size=12), text_color=TEXT2,
                     justify="center", wraplength=400
                     ).grid(row=1, column=0, **pad, pady=(0, 18))

        Sep(self).grid(row=2, column=0, **pad, pady=(0, 20))

        # E-mail
        ctk.CTkLabel(self, text="Seu e-mail (Gmail):",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT, anchor="w").grid(row=3, column=0, **pad, pady=(0, 4))
        self.entry_email = ctk.CTkEntry(self, height=38, font=ctk.CTkFont(size=13),
                                         placeholder_text="exemplo@gmail.com",
                                         fg_color=CARD, border_color=BORDER)
        self.entry_email.grid(row=4, column=0, **pad, pady=(0, 14))

        # Cidade
        ctk.CTkLabel(self, text="Sua cidade:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT, anchor="w").grid(row=5, column=0, **pad, pady=(0, 4))
        self.entry_cidade = ctk.CTkEntry(self, height=38, font=ctk.CTkFont(size=13),
                                          placeholder_text="Ex: Rio de Janeiro",
                                          fg_color=CARD, border_color=BORDER)
        self.entry_cidade.grid(row=6, column=0, **pad, pady=(0, 14))

        # Estado
        ctk.CTkLabel(self, text="Estado (sigla de 2 letras):",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT, anchor="w").grid(row=7, column=0, **pad, pady=(0, 4))
        self.entry_estado = ctk.CTkEntry(self, height=38, font=ctk.CTkFont(size=13),
                                          placeholder_text="Ex: RJ",
                                          fg_color=CARD, border_color=BORDER)
        self.entry_estado.grid(row=8, column=0, **pad, pady=(0, 24))

        ctk.CTkButton(self, text="Salvar e Começar  →",
                      fg_color=GREEN, hover_color="#16a34a",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      height=42, corner_radius=8,
                      command=self._salvar).grid(row=9, column=0, **pad, pady=(0, 28))

    def _salvar(self):
        email  = self.entry_email.get().strip()
        cidade = self.entry_cidade.get().strip() or "São Paulo"
        estado = self.entry_estado.get().strip().upper()[:2] or "SP"

        if not email or "@" not in email:
            messagebox.showwarning("E-mail inválido",
                                   "Por favor, informe um e-mail válido.", parent=self)
            return

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"EMAIL_REMETENTE={email}\n")
            f.write(f"EMAIL_DESTINO={email}\n")
            f.write(f"GMAIL_APP_PASSWORD=\n")
            f.write(f"CIDADE={cidade}\n")
            f.write(f"ESTADO={estado}\n")
            f.write(f"GEMINI_API_KEY=\n")

        load_dotenv(env_path, override=True)
        self.on_salvo()
        self.destroy()


# ── Painel de Análise de Currículo ────────────────────────────────────────────

class PainelAnaliseCV(ctk.CTkToplevel):
    def __init__(self, parent, resultado: dict, on_aplicar):
        super().__init__(parent)
        self.title("Análise de Currículo com IA")
        self.geometry("600x720")
        self.resizable(True, True)
        self.configure(fg_color=BG2)
        self.grab_set()
        self.resultado  = resultado
        self.on_aplicar = on_aplicar
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        hdr = ctk.CTkFrame(self, fg_color=BG3, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        cargo = self.resultado.get("cargo_atual", "Cargo não detectado")
        nivel = self.resultado.get("nivel", "")
        anos  = self.resultado.get("anos_experiencia", 0)
        fonte = self.resultado.get("_fonte", "")

        ctk.CTkLabel(hdr, text="Análise de Currículo com IA",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, padx=20, pady=(16, 2), sticky="w")

        ctk.CTkLabel(hdr,
                     text=f"{cargo}  ·  {nivel.title()}  ·  {anos} anos de experiência",
                     font=ctk.CTkFont(size=12), text_color=TEXT2
                     ).grid(row=1, column=0, padx=20, pady=(0, 6), sticky="w")

        if fonte:
            if fonte == "gemini":
                fonte_txt = "Google Gemini AI"
                cor_f = GREEN
            elif fonte == "ollama":
                modelo = resultado.get("_modelo_ollama", "")
                fonte_txt = f"Ollama — IA local  ({modelo})" if modelo else "Ollama — IA local"
                cor_f = BLUE
            else:
                fonte_txt = "Análise local (sem IA)"
                cor_f = YELLOW
            ctk.CTkLabel(hdr, text=f"Fonte: {fonte_txt}",
                         font=ctk.CTkFont(size=10), text_color=cor_f
                         ).grid(row=2, column=0, padx=20, pady=(0, 14), sticky="w")

        # Conteúdo rolável
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        ri = [0]

        def sec(titulo, cor):
            f = ctk.CTkFrame(scroll, fg_color=BG3, corner_radius=6)
            f.grid(row=ri[0], column=0, padx=16, pady=(14, 2), sticky="ew")
            f.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(f, text=titulo,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=cor).grid(padx=12, pady=6, sticky="w")
            ri[0] += 1

        def item(texto, cor=TEXT2, bg="transparent", numerado=False, num=0):
            prefix = f"{num}.  " if numerado else "   • "
            lbl = ctk.CTkLabel(scroll,
                               text=f"{prefix}{texto}",
                               font=ctk.CTkFont(size=12), text_color=cor,
                               fg_color=bg, corner_radius=4,
                               anchor="w", wraplength=520, justify="left")
            lbl.grid(row=ri[0], column=0, padx=22, pady=2, sticky="ew")
            ri[0] += 1

        sec("✅  PONTOS FORTES", GREEN)
        for pf in self.resultado.get("pontos_fortes", []):
            item(pf, GREEN, GREEN_DIM)

        sec("💡  DICAS DE MELHORIA", YELLOW)
        for i, dica in enumerate(self.resultado.get("dicas_melhoria", []), 1):
            item(dica, YELLOW, YELLOW_DIM, numerado=True, num=i)

        sec("⚠  PALAVRAS-CHAVE AUSENTES", RED)
        ausentes = self.resultado.get("palavras_chave_ausentes", [])
        if ausentes:
            item(", ".join(ausentes), RED, RED_DIM)

        sec("🔧  HABILIDADES DETECTADAS", BLUE)
        habs = self.resultado.get("habilidades", [])
        if habs:
            item(", ".join(habs[:20]), TEXT2)

        sec("🔍  TERMOS DE BUSCA SUGERIDOS", TEXT3)
        for t in self.resultado.get("termos_busca_sugeridos", []):
            item(t, TEXT2)

        # Rodapé
        footer = ctk.CTkFrame(self, fg_color=BG3, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        btns = ctk.CTkFrame(footer, fg_color="transparent")
        btns.grid(row=0, column=0, padx=20, pady=14, sticky="e")

        ctk.CTkButton(btns, text="Aplicar Perfil à Busca  ✓",
                      fg_color=GREEN, hover_color="#16a34a",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      height=38, corner_radius=8,
                      command=self._aplicar).pack(side="left", padx=(0, 10))

        ctk.CTkButton(btns, text="Fechar",
                      fg_color=CARD2, hover_color=MUTED,
                      height=38, corner_radius=8,
                      command=self.destroy).pack(side="left")

    def _aplicar(self):
        self.on_aplicar(self.resultado)
        self.destroy()


# ── App Principal ─────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CaçaVagas — Diego Paixão")
        self.geometry("1180x820")
        self.minsize(960, 640)
        self.configure(fg_color=BG)

        # Ícone da janela
        _ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.ico")
        if os.path.isfile(_ico):
            try:
                self.iconbitmap(_ico)
            except Exception:
                pass

        self.senha_app   = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        self.cv_path     = CURRICULO_PADRAO if os.path.isfile(CURRICULO_PADRAO) else ""

        # Cache e estado da busca
        self.vagas_cache    : list[dict] = []
        self.cards          : list[CardVaga] = []
        self._urls_vistos   : set = set()
        self._tabs_cards_ok : dict = {"todas": False, "nac": False, "int": False}
        self._row_todas     : int = 0
        self._row_nac       : int = 0
        self._row_int       : int = 0

        # Perfil e localização
        self.coords_usuario      = None
        self.termos_busca_ativos : list = list(TERMOS_BUSCA)
        self.perfil_cv_resultado = None

        # Variáveis de filtro
        self.var_score          = ctk.IntVar(value=SCORE_MINIMO)
        self.var_remoto         = ctk.BooleanVar(value=True)
        self.var_hibrido        = ctk.BooleanVar(value=True)
        self.var_presencial     = ctk.BooleanVar(value=True)
        self.var_so_email       = ctk.BooleanVar(value=False)
        self.var_pt             = ctk.BooleanVar(value=True)
        self.var_inter          = ctk.BooleanVar(value=True)
        self.var_ocultar_req_en = ctk.BooleanVar(value=False)

        self._ui()
        self.after(300, self._verificar_primeiro_uso)
        threading.Thread(target=self._init_geocoding, daemon=True).start()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._header()
        self._body()

    def _header(self):
        hdr = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, height=68)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.grid(row=0, column=0, padx=20, pady=12)
        ctk.CTkLabel(left, text="CaçaVagas",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(left, text="  ·  Diego Paixão",
                     font=ctk.CTkFont(size=14), text_color=TEXT3).pack(side="left")

        self.lbl_status = ctk.CTkLabel(hdr, text="Nenhuma busca realizada.",
                                        font=ctk.CTkFont(size=12), text_color=TEXT3)
        self.lbl_status.grid(row=0, column=1, padx=8)

        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.grid(row=0, column=2, padx=20, pady=14)

        self.btn_buscar = ctk.CTkButton(btns, text="⟳  Buscar Vagas",
                                         fg_color=BLUE2, hover_color="#1d4ed8",
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         height=38, width=155, corner_radius=8,
                                         command=self._buscar)
        self.btn_buscar.pack(side="left", padx=(0, 8))

        ctk.CTkButton(btns, text="✉  Enviar Digest",
                      fg_color=CARD2, hover_color=MUTED,
                      font=ctk.CTkFont(size=13), height=38, width=140, corner_radius=8,
                      command=self._digest).pack(side="left")

    def _body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self._sidebar(body)
        self._content(body)

    def _sidebar(self, parent):
        sb = ctk.CTkFrame(parent, fg_color=BG2, corner_radius=0, width=272)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        scroll_sb = ctk.CTkScrollableFrame(sb, fg_color="transparent", width=252)
        scroll_sb.pack(fill="both", expand=True)
        scroll_sb.grid_columnconfigure(0, weight=1)

        def sec(row, txt):
            ctk.CTkLabel(scroll_sb, text=txt,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color=BLUE).grid(row=row, column=0, padx=16, sticky="w", pady=(16, 4))

        def sep(row):
            Sep(scroll_sb).grid(row=row, column=0, padx=16, sticky="ew", pady=6)

        # ── Currículo ──
        sec(0, "CURRÍCULO PARA CANDIDATURA")

        self.lbl_cv = ctk.CTkLabel(scroll_sb,
                                    text=os.path.basename(self.cv_path) if self.cv_path else "Nenhum selecionado",
                                    font=ctk.CTkFont(size=11), text_color=TEXT2, wraplength=220)
        self.lbl_cv.grid(row=1, column=0, padx=16, sticky="w")

        ctk.CTkButton(scroll_sb, text="📂  Selecionar arquivo",
                      fg_color=CARD2, hover_color=MUTED,
                      font=ctk.CTkFont(size=12), height=32, corner_radius=8,
                      command=self._sel_cv
                      ).grid(row=2, column=0, padx=16, sticky="ew", pady=(6, 4))

        self.btn_analisar = ctk.CTkButton(scroll_sb, text="🤖  Analisar com IA",
                                           fg_color=BLUE_DIM, hover_color=BLUE2,
                                           font=ctk.CTkFont(size=12, weight="bold"),
                                           height=32, corner_radius=8,
                                           state="normal" if self.cv_path else "disabled",
                                           command=self._analisar_cv)
        self.btn_analisar.grid(row=3, column=0, padx=16, sticky="ew", pady=(0, 4))

        self.lbl_perfil_status = ctk.CTkLabel(scroll_sb,
                                               text="Perfil: padrão (config.py)",
                                               font=ctk.CTkFont(size=10), text_color=TEXT3)
        self.lbl_perfil_status.grid(row=4, column=0, padx=16, sticky="w")

        sep(5)

        # ── Score ──
        sec(6, "PONTUAÇÃO MÍNIMA")
        self.lbl_sc = ctk.CTkLabel(scroll_sb, text=str(self.var_score.get()),
                                    font=ctk.CTkFont(size=22, weight="bold"), text_color=BLUE)
        self.lbl_sc.grid(row=7, column=0, padx=16, sticky="w")

        ctk.CTkSlider(scroll_sb, from_=0, to=80, number_of_steps=16,
                      variable=self.var_score,
                      command=lambda v: (self.lbl_sc.configure(text=str(int(v))), self._filtrar())
                      ).grid(row=8, column=0, padx=16, sticky="ew", pady=(2, 0))

        sep(9)

        # ── Modalidade ──
        sec(10, "MODALIDADE")
        for i, (txt, var) in enumerate([
            ("🌐  Remoto",     self.var_remoto),
            ("🔀  Híbrido",    self.var_hibrido),
            ("📍  Presencial", self.var_presencial),
        ], 11):
            ctk.CTkCheckBox(scroll_sb, text=txt, variable=var,
                            font=ctk.CTkFont(size=12),
                            command=self._filtrar
                            ).grid(row=i, column=0, padx=16, sticky="w", pady=3)

        sep(14)

        # ── Origem e idioma ──
        sec(15, "ORIGEM E IDIOMA")

        ctk.CTkCheckBox(scroll_sb, text="🇧🇷  Nacionais (Brasil)",
                        variable=self.var_pt,
                        font=ctk.CTkFont(size=12), command=self._filtrar
                        ).grid(row=16, column=0, padx=16, sticky="w", pady=3)

        ctk.CTkCheckBox(scroll_sb, text="🌍  Internacionais",
                        variable=self.var_inter,
                        font=ctk.CTkFont(size=12), command=self._filtrar
                        ).grid(row=17, column=0, padx=16, sticky="w", pady=3)

        ctk.CTkSwitch(scroll_sb, text="Ocultar inglês obrigatório",
                      variable=self.var_ocultar_req_en,
                      font=ctk.CTkFont(size=12), command=self._filtrar
                      ).grid(row=18, column=0, padx=16, sticky="w", pady=3)

        sep(19)

        # ── Opções ──
        sec(20, "OPÇÕES")
        ctk.CTkSwitch(scroll_sb, text="Só com e-mail direto",
                      variable=self.var_so_email,
                      font=ctk.CTkFont(size=12), command=self._filtrar
                      ).grid(row=21, column=0, padx=16, sticky="w", pady=3)

        sep(22)

        # ── Candidaturas ──
        sec(23, "CANDIDATURAS ENVIADAS")

        self.lbl_cand = ctk.CTkLabel(scroll_sb,
                                      text=str(banco.total_candidaturas()),
                                      font=ctk.CTkFont(size=32, weight="bold"),
                                      text_color=GREEN)
        self.lbl_cand.grid(row=24, column=0, padx=16, sticky="w")

        ctk.CTkLabel(scroll_sb, text="candidaturas via e-mail",
                     font=ctk.CTkFont(size=11), text_color=TEXT3
                     ).grid(row=25, column=0, padx=16, sticky="w", pady=(0, 16))

    def _content(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew")
        col.grid_rowconfigure(1, weight=1)
        col.grid_columnconfigure(0, weight=1)

        # Barra de estatísticas
        self.stats = ctk.CTkFrame(col, fg_color=BG3, corner_radius=0, height=48)
        self.stats.grid(row=0, column=0, sticky="ew")
        self.stats.grid_propagate(False)
        self.stats.grid_columnconfigure(0, weight=1)

        self.lbl_stats = ctk.CTkLabel(self.stats, text="Aguardando busca...",
                                       font=ctk.CTkFont(size=12), text_color=TEXT3)
        self.lbl_stats.grid(row=0, column=0, padx=20, sticky="w")

        # Abas
        self.tab_view = ctk.CTkTabview(col, fg_color="transparent",
                                        segmented_button_fg_color=BG3,
                                        segmented_button_selected_color=BLUE2,
                                        segmented_button_unselected_color=BG2,
                                        segmented_button_selected_hover_color="#1d4ed8",
                                        segmented_button_unselected_hover_color=BG3)
        self.tab_view.grid(row=1, column=0, sticky="nsew")

        for nome_aba in ["Todas", "Nacionais 🇧🇷", "Internacional 🌍"]:
            self.tab_view.add(nome_aba)
            aba = self.tab_view.tab(nome_aba)
            aba.grid_rowconfigure(0, weight=1)
            aba.grid_columnconfigure(0, weight=1)

        self.scroll_todas = ctk.CTkScrollableFrame(
            self.tab_view.tab("Todas"), fg_color="transparent")
        self.scroll_todas.grid(row=0, column=0, sticky="nsew")
        self.scroll_todas.grid_columnconfigure(0, weight=1)

        self.scroll_nac = ctk.CTkScrollableFrame(
            self.tab_view.tab("Nacionais 🇧🇷"), fg_color="transparent")
        self.scroll_nac.grid(row=0, column=0, sticky="nsew")
        self.scroll_nac.grid_columnconfigure(0, weight=1)

        self.scroll_int = ctk.CTkScrollableFrame(
            self.tab_view.tab("Internacional 🌍"), fg_color="transparent")
        self.scroll_int.grid(row=0, column=0, sticky="nsew")
        self.scroll_int.grid_columnconfigure(0, weight=1)

        # Placeholders iniciais
        for scroll, msg in [
            (self.scroll_todas, "Clique em  ⟳ Buscar Vagas  para iniciar."),
            (self.scroll_nac,   "Vagas nacionais aparecerão aqui após a busca."),
            (self.scroll_int,   "Vagas internacionais aparecerão aqui após a busca."),
        ]:
            ctk.CTkLabel(scroll, text=msg,
                         font=ctk.CTkFont(size=14), text_color=TEXT3
                         ).grid(row=0, column=0, pady=80)

        # Log
        self.log = ctk.CTkTextbox(col, height=100,
                                   font=ctk.CTkFont(family="Consolas", size=11),
                                   fg_color=BG, text_color=TEXT3,
                                   corner_radius=0, border_width=0)
        self.log.grid(row=2, column=0, sticky="ew")
        self.log.configure(state="disabled")

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _sel_cv(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        if p:
            self.cv_path = p
            self.lbl_cv.configure(text=os.path.basename(p))
            self.btn_analisar.configure(state="normal")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}]  {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _init_geocoding(self):
        """Geocodifica localização do usuário em background na inicialização."""
        try:
            from geolocalizador import geocodificar_usuario
            coords = geocodificar_usuario()
            self.coords_usuario = coords
            if coords:
                self.after(0, lambda: self._log(f"Localização geocodificada com sucesso."))
        except Exception as e:
            self.after(0, lambda err=str(e): self._log(f"[Geo] Erro ao geocodificar: {err}"))

    def _analisar_cv(self):
        if not self.cv_path or not os.path.isfile(self.cv_path):
            messagebox.showwarning("Sem currículo", "Selecione um currículo PDF primeiro.")
            return
        self.btn_analisar.configure(text="Analisando...", state="disabled")

        def worker():
            try:
                resultado = curriculo_parser.analisar_curriculo(self.cv_path)
                self.perfil_cv_resultado = resultado
                self.after(0, lambda r=resultado: self._pos_analise(r))
            except Exception as e:
                self.after(0, lambda err=str(e): (
                    messagebox.showerror("Erro na análise", err),
                    self.btn_analisar.configure(text="🤖  Analisar com IA", state="normal")
                ))

        threading.Thread(target=worker, daemon=True).start()

    def _pos_analise(self, resultado):
        self.btn_analisar.configure(text="🤖  Analisar com IA", state="normal")
        PainelAnaliseCV(self, resultado, self._aplicar_perfil_cv)

    def _aplicar_perfil_cv(self, resultado):
        from curriculo_parser import resultado_para_perfil
        from matcher import configurar_perfil
        perfil = resultado_para_perfil(resultado)
        configurar_perfil(perfil)

        novos_termos = resultado.get("termos_busca_sugeridos") or list(TERMOS_BUSCA)
        self.termos_busca_ativos = novos_termos[:15]

        cargo = resultado.get("cargo_atual", "")
        self.lbl_perfil_status.configure(
            text=f"Perfil: {cargo}" if cargo else "Perfil: CV analisado ✓",
            text_color=GREEN)

        self._log(f"Perfil aplicado: {cargo}  ·  {len(self.termos_busca_ativos)} termos de busca")

        # Atualiza localização a partir do CV se disponível
        loc = resultado.get("localizacao_extraida", "")
        if loc and "," in loc:
            def _update_geo():
                try:
                    from geolocalizador import geocodificar
                    coords = geocodificar(loc)
                    if coords:
                        self.coords_usuario = coords
                        self.after(0, lambda: self._log(f"Localização do CV: {loc}"))
                except Exception:
                    pass
            threading.Thread(target=_update_geo, daemon=True).start()

    # ── Busca ─────────────────────────────────────────────────────────────────

    def _buscar(self):
        self.vagas_cache        = []
        self.cards              = []
        self._urls_vistos       = set()
        self._tabs_cards_ok     = {"todas": False, "nac": False, "int": False}
        self._row_todas         = 0
        self._row_nac           = 0
        self._row_int           = 0

        self.btn_buscar.configure(text="Buscando...", state="disabled")
        self.lbl_status.configure(text="Buscando em 8 fontes...")
        self.lbl_stats.configure(text="Aguardando primeiros resultados...")

        for scroll, msg in [
            (self.scroll_todas, "Buscando vagas... os cards aparecem conforme cada fonte responde."),
            (self.scroll_nac,   "Aguardando vagas nacionais..."),
            (self.scroll_int,   "Aguardando vagas internacionais..."),
        ]:
            for w in scroll.winfo_children():
                w.destroy()
            ctk.CTkLabel(scroll, text=msg,
                         font=ctk.CTkFont(size=13), text_color=TEXT3
                         ).grid(row=0, column=0, pady=80)

        self._log("Iniciando busca em 8 fontes...")
        threading.Thread(target=self._worker_busca, daemon=True).start()

    def _worker_busca(self):
        from vagas import gupy, remotive, linkedin, programathor
        from vagas import weworkremotely, himalayas, infojobs, vagas_com

        termos = self.termos_busca_ativos

        FONTES = [
            ("Remotive",       lambda: remotive.buscar()),
            ("WeWorkRemotely", lambda: weworkremotely.buscar()),
            ("Himalayas",      lambda: himalayas.buscar()),
            ("Gupy",           lambda: gupy.buscar(termos)),
            ("InfoJobs",       lambda: infojobs.buscar()),
            ("ProgramaThor",   lambda: programathor.buscar(["rio de janeiro", "remoto"])),
            ("LinkedIn",       lambda: linkedin.buscar()),
            ("Vagas.com",      lambda: vagas_com.buscar()),
        ]

        for nome, fn in FONTES:
            try:
                r = fn()
                self.after(0, lambda n=nome, v=r: self._fonte_ok(n, v))
            except Exception as e:
                self.after(0, lambda n=nome, err=str(e): self._log(f"[{n}] Erro: {err}"))

        self.after(0, self._busca_completa)

    def _fonte_ok(self, nome, vagas_brutas):
        sc_min         = self.var_score.get()
        mods           = {m for m, v in [("Remoto", self.var_remoto), ("Hibrido", self.var_hibrido),
                                          ("Presencial", self.var_presencial)] if v.get()}
        so_email       = self.var_so_email.get()
        mostrar_pt     = self.var_pt.get()
        mostrar_int    = self.var_inter.get()
        ocultar_req_en = self.var_ocultar_req_en.get()

        novas = 0
        for v in vagas_brutas:
            url = v.get("url", "")
            if not url or url in self._urls_vistos:
                continue
            self._urls_vistos.add(url)
            v["score"] = calcular_score(v)
            v["_email_candidatura"] = aplicador.extrair_email_candidatura(v.get("descricao", ""))
            enriquecer_vaga(v)
            self.vagas_cache.append(v)

            pais         = v.get("pais", "BR")
            idioma_obrig = v.get("idioma_obrigatorio")

            if v.get("score", 0) < sc_min:
                continue
            if v.get("modalidade", "Presencial") not in mods:
                continue
            if so_email and not v.get("_email_candidatura"):
                continue
            if ocultar_req_en and idioma_obrig == "en":
                continue
            if pais == "BR" and not mostrar_pt:
                continue
            if pais == "WW" and not mostrar_int:
                continue

            # Aba "Todas"
            if not self._tabs_cards_ok["todas"]:
                for w in self.scroll_todas.winfo_children():
                    w.destroy()
                self._tabs_cards_ok["todas"] = True

            card_t = CardVaga(self.scroll_todas, v, self)
            card_t.grid(row=self._row_todas, column=0, sticky="ew", padx=16, pady=(0, 8))
            self._row_todas += 1
            self.cards.append(card_t)

            # Aba Nacionais ou Internacional
            if pais == "BR":
                if not self._tabs_cards_ok["nac"]:
                    for w in self.scroll_nac.winfo_children():
                        w.destroy()
                    self._tabs_cards_ok["nac"] = True
                card_n = CardVaga(self.scroll_nac, v, self)
                card_n.grid(row=self._row_nac, column=0, sticky="ew", padx=16, pady=(0, 8))
                self._row_nac += 1
            elif pais == "WW":
                if not self._tabs_cards_ok["int"]:
                    for w in self.scroll_int.winfo_children():
                        w.destroy()
                    self._tabs_cards_ok["int"] = True
                card_i = CardVaga(self.scroll_int, v, self)
                card_i.grid(row=self._row_int, column=0, sticky="ew", padx=16, pady=(0, 8))
                self._row_int += 1

            novas += 1

        self._log(f"[{nome}] {len(vagas_brutas)} encontradas  ·  {novas} cards adicionados")
        self._atualizar_stats()

    def _busca_completa(self):
        total = len(self.vagas_cache)
        self.btn_buscar.configure(text="⟳  Buscar Vagas", state="normal")
        self.lbl_status.configure(
            text=f"Última busca: {datetime.now().strftime('%d/%m  %H:%M')}  ·  {total} vagas")
        self._log(f"Busca concluída — {total} vagas únicas, {len(self.cards)} exibidas.")

        for scroll, key, msg in [
            (self.scroll_todas, "todas", "Nenhuma vaga encontrada. Reduza a pontuação mínima."),
            (self.scroll_nac,   "nac",   "Nenhuma vaga nacional encontrada."),
            (self.scroll_int,   "int",   "Nenhuma vaga internacional encontrada."),
        ]:
            if not self._tabs_cards_ok[key]:
                for w in scroll.winfo_children():
                    w.destroy()
                ctk.CTkLabel(scroll, text=msg,
                             font=ctk.CTkFont(size=14), text_color=TEXT3
                             ).grid(row=0, column=0, pady=80)

        threading.Thread(target=self._batch_geocodificar, daemon=True).start()

    def _batch_geocodificar(self):
        """Geocodifica distâncias de vagas presenciais/híbridas e re-renderiza ao final."""
        if not self.coords_usuario:
            return
        try:
            from geolocalizador import distancia_vaga
        except Exception:
            return
        changed = False
        for v in self.vagas_cache:
            if v.get("modalidade") in ("Presencial", "Hibrido") and "distancia_km" not in v:
                try:
                    dist = distancia_vaga(v, self.coords_usuario)
                    if dist is not None:
                        v["distancia_km"] = dist
                        changed = True
                except Exception:
                    pass
        if changed:
            self.after(0, self._filtrar)

    def _atualizar_stats(self):
        r = sum(1 for v in self.vagas_cache if v.get("modalidade") == "Remoto")
        h = sum(1 for v in self.vagas_cache if v.get("modalidade") == "Hibrido")
        p = sum(1 for v in self.vagas_cache if v.get("modalidade") not in ("Remoto", "Hibrido"))
        e = sum(1 for v in self.vagas_cache if v.get("_email_candidatura"))
        exibidas = sum(1 for w in self.scroll_todas.winfo_children() if isinstance(w, CardVaga))
        self.lbl_stats.configure(
            text=f"{exibidas} exibidas  ·  {r} remotas  ·  {h} híbridas  ·  {p} presenciais  ·  {e} c/ e-mail"
        )

    def _filtrar(self, *_):
        if not self.vagas_cache:
            return

        sc_min         = self.var_score.get()
        mods           = {m for m, v in [("Remoto", self.var_remoto), ("Hibrido", self.var_hibrido),
                                          ("Presencial", self.var_presencial)] if v.get()}
        so_email       = self.var_so_email.get()
        mostrar_pt     = self.var_pt.get()
        mostrar_int    = self.var_inter.get()
        ocultar_req_en = self.var_ocultar_req_en.get()

        base = [
            v for v in self.vagas_cache
            if v.get("score", 0) >= sc_min
            and v.get("modalidade", "Presencial") in mods
            and (not so_email or v.get("_email_candidatura"))
            and not (ocultar_req_en and v.get("idioma_obrigatorio") == "en")
        ]

        # "Todas" — Remoto primeiro, depois por score
        f_todas = sorted(base, key=lambda v: (
            {"Remoto": 0, "Hibrido": 1}.get(v.get("modalidade", ""), 2),
            -v.get("score", 0)
        ))

        # "Nacionais" — presencial/híbrido por distância ↑, remoto por score ↓
        def sort_nac(v):
            mod  = v.get("modalidade", "")
            prio = {"Presencial": 0, "Hibrido": 1}.get(mod, 2)
            dist = v.get("distancia_km", 9999) if mod in ("Presencial", "Hibrido") else 9999
            return (prio, dist, -v.get("score", 0))

        f_nac = sorted(
            [v for v in base if v.get("pais", "BR") == "BR" and mostrar_pt],
            key=sort_nac
        )

        # "Internacional" — por score ↓
        f_int = sorted(
            [v for v in base if v.get("pais") == "WW" and mostrar_int],
            key=lambda v: -v.get("score", 0)
        )

        def render(scroll, lista, msg_vazia):
            for w in scroll.winfo_children():
                w.destroy()
            if not lista:
                ctk.CTkLabel(scroll, text=msg_vazia,
                             font=ctk.CTkFont(size=13), text_color=TEXT3
                             ).grid(row=0, column=0, pady=80)
                return
            for i, v in enumerate(lista):
                card = CardVaga(scroll, v, self)
                card.grid(row=i, column=0, sticky="ew", padx=16, pady=(0, 8))

        render(self.scroll_todas, f_todas, "Nenhuma vaga com esses filtros. Reduza a pontuação ou mude a modalidade.")
        render(self.scroll_nac,   f_nac,   "Nenhuma vaga nacional com esses filtros.")
        render(self.scroll_int,   f_int,   "Nenhuma vaga internacional com esses filtros.")

        self.cards = [w for w in self.scroll_todas.winfo_children() if isinstance(w, CardVaga)]
        self._tabs_cards_ok = {"todas": bool(f_todas), "nac": bool(f_nac), "int": bool(f_int)}
        self._atualizar_stats()

    def abrir_candidatura(self, vaga, email_dest, card):
        if not self.cv_path or not os.path.isfile(self.cv_path):
            messagebox.showwarning("Currículo não selecionado",
                                   "Selecione o arquivo de currículo na barra lateral antes de enviar.")
            return
        if not self.senha_app:
            messagebox.showerror("Erro", "GMAIL_APP_PASSWORD não configurada no .env")
            return

        def on_ok():
            card.refresh()
            self.lbl_cand.configure(text=str(banco.total_candidaturas()))
            self._log(f"Candidatura enviada: {vaga.get('titulo','')}  →  {email_dest}")

        PainelCandidatura(self, vaga, email_dest, self.cv_path,
                          EMAIL_REMETENTE, self.senha_app, on_ok)

    def _digest(self):
        if not self.vagas_cache:
            messagebox.showinfo("Aviso", "Realize uma busca primeiro."); return
        if not self.senha_app:
            messagebox.showerror("Erro", "GMAIL_APP_PASSWORD não configurada."); return

        sc_min = self.var_score.get()
        novas  = [v for v in self.vagas_cache
                  if v.get("score", 0) >= sc_min and banco.is_nova(v.get("url", ""))]
        if not novas:
            messagebox.showinfo("Digest", "Todas as vagas já foram enviadas anteriormente."); return

        self._log(f"Enviando digest com {len(novas)} vagas...")

        def worker():
            try:
                notificador.enviar_digest(novas, EMAIL_DESTINO, EMAIL_REMETENTE, self.senha_app)
                for v in novas:
                    banco.marcar_vista(v["url"], v["titulo"], v.get("empresa",""), v["plataforma"], v["score"])
                self.after(0, lambda: (
                    self._log(f"Digest enviado: {len(novas)} vagas para {EMAIL_DESTINO}"),
                    messagebox.showinfo("Enviado!", f"{len(novas)} vagas enviadas para {EMAIL_DESTINO}")
                ))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Erro", err))

        threading.Thread(target=worker, daemon=True).start()

    def _verificar_primeiro_uso(self):
        """Exibe assistente de configuração na primeira execução."""
        email = os.getenv("EMAIL_REMETENTE", "").strip()
        if not email or email == "seu@gmail.com":
            PainelPrimeiroUso(self, lambda: None)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        import customtkinter
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter"], check=True)

    App().mainloop()
