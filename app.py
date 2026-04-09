# app.py — Automacao de Vagas — interface CustomTkinter moderna

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

# ── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Paleta
BG       = "#080e1a"
BG2      = "#0d1527"
BG3      = "#111d35"
CARD     = "#131e32"
CARD2    = "#182644"
BORDER   = "#1e2f4a"
BLUE     = "#3b82f6"
BLUE2    = "#2563eb"
BLUE_DIM = "#1e3a5f"
GREEN    = "#22c55e"
GREEN_DIM= "#14532d"
YELLOW   = "#f59e0b"
YELLOW_DIM="#78350f"
RED      = "#ef4444"
RED_DIM  = "#7f1d1d"
MUTED    = "#334155"
TEXT     = "#e2e8f0"
TEXT2    = "#94a3b8"
TEXT3    = "#64748b"

CURRICULO_PADRAO = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "curriculo_diego_paixao.pdf"
))

# ── Helpers ───────────────────────────────────────────────────────────────────

def cor_score(s):
    if s >= 70: return GREEN,   GREEN_DIM
    if s >= 40: return BLUE,    BLUE_DIM
    if s >= 20: return YELLOW,  YELLOW_DIM
    return TEXT3, MUTED

def cor_modalidade(m):
    return {
        "Remoto":    (GREEN,  GREEN_DIM,  "🌐 Remoto"),
        "Hibrido":   (BLUE,   BLUE_DIM,   "🔀 Híbrido"),
        "Presencial":(YELLOW, YELLOW_DIM, "📍 Presencial"),
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
        v           = self.vaga
        score       = v.get("score", 0)
        modalidade  = v.get("modalidade", "")
        email_app   = v.get("_email_candidatura")
        ja_aplic    = banco.ja_aplicou(v.get("url", ""))
        sc, sc_bg   = cor_score(score)
        mc, mc_bg, mlabel = cor_modalidade(modalidade)
        pc          = plat_cor(v.get("plataforma", ""))
        titulo_orig = v.get("_titulo_original", "")

        # Barra lateral colorida por score
        bar = ctk.CTkFrame(self, width=4, fg_color=sc, corner_radius=0)
        bar.grid(row=0, column=0, rowspan=6, sticky="ns", padx=(0, 0))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=1, sticky="nsew", padx=(12, 14), pady=(12, 10))
        inner.grid_columnconfigure(0, weight=1)

        # ── Linha de badges ──
        badges = ctk.CTkFrame(inner, fg_color="transparent")
        badges.grid(row=0, column=0, sticky="ew")

        # Score
        ctk.CTkLabel(badges, text=f"  {score}  ",
                     fg_color=sc_bg, text_color=sc,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     corner_radius=6).pack(side="left", padx=(0, 6))

        # Modalidade
        ctk.CTkLabel(badges, text=f"  {mlabel}  ",
                     fg_color=mc_bg, text_color=mc,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     corner_radius=6).pack(side="left", padx=(0, 6))

        # Plataforma
        ctk.CTkLabel(badges, text=f"  {v.get('plataforma','')}  ",
                     fg_color=pc, text_color="white",
                     font=ctk.CTkFont(size=10),
                     corner_radius=6).pack(side="left", padx=(0, 6))

        # Badge "Aplicado"
        if ja_aplic:
            ctk.CTkLabel(badges, text="  ✓ Aplicado  ",
                         fg_color=GREEN_DIM, text_color=GREEN,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="right")

        # Badge "E-mail direto"
        elif email_app:
            ctk.CTkLabel(badges, text="  📧 E-mail direto  ",
                         fg_color="#1e3a5f", text_color="#60a5fa",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         corner_radius=6).pack(side="right")

        # ── Título ──
        titulo_display = v.get("titulo", "")[:90]
        ctk.CTkLabel(inner, text=titulo_display,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT, anchor="w", wraplength=540,
                     justify="left"
                     ).grid(row=1, column=0, sticky="ew", pady=(6, 0))

        # Título original (se traduzido)
        if titulo_orig and titulo_orig != titulo_display:
            ctk.CTkLabel(inner, text=f"Original: {titulo_orig[:70]}",
                         font=ctk.CTkFont(size=10),
                         text_color=TEXT3, anchor="w"
                         ).grid(row=2, column=0, sticky="ew")

        # ── Meta (empresa · local · data) ──
        meta_partes = [p for p in [v.get("empresa"), v.get("local"), (v.get("data") or "")[:10]] if p]
        ctk.CTkLabel(inner, text="  ·  ".join(meta_partes),
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT2, anchor="w"
                     ).grid(row=3, column=0, sticky="ew", pady=(2, 0))

        # ── E-mail de candidatura ──
        if email_app:
            ctk.CTkLabel(inner, text=f"📧  {email_app}",
                         font=ctk.CTkFont(size=11),
                         text_color="#60a5fa", anchor="w"
                         ).grid(row=4, column=0, sticky="ew", pady=(4, 0))

        # ── Botões ──
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.grid(row=5, column=0, sticky="w", pady=(8, 0))

        if email_app and not ja_aplic:
            ctk.CTkButton(btns,
                          text="Aplicar por E-mail  📎",
                          fg_color=GREEN, hover_color="#16a34a",
                          font=ctk.CTkFont(size=12, weight="bold"),
                          height=32, width=190, corner_radius=8,
                          command=lambda: self.app.abrir_candidatura(self.vaga, email_app, self)
                          ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btns,
                      text="Ver Vaga  →",
                      fg_color=BLUE2, hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=12),
                      height=32, width=110, corner_radius=8,
                      command=lambda: webbrowser.open(v.get("url", ""))
                      ).pack(side="left")

    def refresh(self):
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

        self.vaga      = vaga
        self.email_dest = email_dest
        self.cv_path   = cv_path
        self.remetente = remetente
        self.senha     = senha
        self.on_ok     = on_ok
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

        # Currículo
        cv_row = ctk.CTkFrame(self, fg_color="transparent")
        cv_row.grid(row=4, column=0, **pad, pady=(0, 10))
        cv_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cv_row, text="Currículo anexado:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT).grid(row=0, column=0, sticky="w")

        self.lbl_cv = ctk.CTkLabel(cv_row,
                                   text=os.path.basename(self.cv_path),
                                   font=ctk.CTkFont(size=12), text_color=BLUE)
        self.lbl_cv.grid(row=1, column=0, sticky="w")

        ctk.CTkButton(cv_row, text="Trocar", width=80, height=28,
                      fg_color=CARD2, corner_radius=6,
                      command=self._trocar).grid(row=1, column=1, padx=(8, 0))

        # Assunto
        ctk.CTkLabel(self, text="Assunto:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT).grid(row=5, column=0, **pad, pady=(4, 0))

        self.entry_assunto = ctk.CTkEntry(self, height=36, font=ctk.CTkFont(size=12),
                                          fg_color=CARD, border_color=BORDER)
        self.entry_assunto.insert(0, aplicador.montar_assunto(aplicador.ASSUNTO_PADRAO, self.vaga))
        self.entry_assunto.grid(row=6, column=0, **pad, pady=(4, 10))

        # Corpo
        ctk.CTkLabel(self, text="Corpo:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT).grid(row=7, column=0, **pad)

        self.txt = ctk.CTkTextbox(self, height=190, font=ctk.CTkFont(size=11),
                                   fg_color=CARD, border_color=BORDER, border_width=1)
        self.txt.insert("0.0", aplicador.montar_corpo(aplicador.CORPO_PADRAO, self.vaga))
        self.txt.grid(row=8, column=0, **pad, pady=(4, 14))

        # Botões
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


# ── App Principal ─────────────────────────────────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Automação de Vagas — Diego Paixão")
        self.geometry("1180x820")
        self.minsize(960, 640)
        self.configure(fg_color=BG)

        self.senha_app    = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        self.cv_path      = CURRICULO_PADRAO if os.path.isfile(CURRICULO_PADRAO) else ""
        self.vagas_cache  : list[dict] = []
        self.cards        : list[CardVaga] = []
        self._urls_vistos : set = set()
        self._cards_ok    : bool = False   # True após primeira remoção do placeholder

        self.var_score      = ctk.IntVar(value=SCORE_MINIMO)
        self.var_remoto     = ctk.BooleanVar(value=True)
        self.var_hibrido    = ctk.BooleanVar(value=True)
        self.var_presencial = ctk.BooleanVar(value=True)
        self.var_so_email   = ctk.BooleanVar(value=False)

        self._ui()

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

        # Título
        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.grid(row=0, column=0, padx=20, pady=12)
        ctk.CTkLabel(left, text="Automação de Vagas",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(left, text="  ·  Diego Paixão",
                     font=ctk.CTkFont(size=14), text_color=TEXT3).pack(side="left")

        # Status
        self.lbl_status = ctk.CTkLabel(hdr, text="Nenhuma busca realizada.",
                                        font=ctk.CTkFont(size=12), text_color=TEXT3)
        self.lbl_status.grid(row=0, column=1, padx=8)

        # Botões
        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.grid(row=0, column=2, padx=20, pady=14)

        self.btn_buscar = ctk.CTkButton(btns, text="⟳  Buscar Vagas",
                                         fg_color=BLUE2, hover_color="#1d4ed8",
                                         font=ctk.CTkFont(size=13, weight="bold"),
                                         height=38, width=150, corner_radius=8,
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
        scroll_sb.pack(fill="both", expand=True, padx=0, pady=0)
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
                      ).grid(row=2, column=0, padx=16, sticky="ew", pady=(6, 0))

        sep(3)

        # ── Score ──
        sec(4, "SCORE MÍNIMO")
        self.lbl_sc = ctk.CTkLabel(scroll_sb, text=str(self.var_score.get()),
                                    font=ctk.CTkFont(size=22, weight="bold"), text_color=BLUE)
        self.lbl_sc.grid(row=5, column=0, padx=16, sticky="w")

        ctk.CTkSlider(scroll_sb, from_=0, to=80, number_of_steps=16,
                      variable=self.var_score,
                      command=lambda v: (self.lbl_sc.configure(text=str(int(v))), self._filtrar())
                      ).grid(row=6, column=0, padx=16, sticky="ew", pady=(2, 0))

        sep(7)

        # ── Modalidade ──
        sec(8, "MODALIDADE")
        for i, (txt, var) in enumerate([
            ("🌐  Remoto",     self.var_remoto),
            ("🔀  Híbrido",    self.var_hibrido),
            ("📍  Presencial", self.var_presencial),
        ], 9):
            ctk.CTkCheckBox(scroll_sb, text=txt, variable=var,
                            font=ctk.CTkFont(size=12),
                            command=self._filtrar
                            ).grid(row=i, column=0, padx=16, sticky="w", pady=3)

        sep(12)

        # ── Opções ──
        sec(13, "OPÇÕES")
        ctk.CTkSwitch(scroll_sb, text="Só com e-mail direto",
                      variable=self.var_so_email,
                      font=ctk.CTkFont(size=12), command=self._filtrar
                      ).grid(row=14, column=0, padx=16, sticky="w", pady=3)

        sep(15)

        # ── Estatísticas ──
        sec(16, "CANDIDATURAS ENVIADAS")

        self.lbl_cand = ctk.CTkLabel(scroll_sb,
                                      text=str(banco.total_candidaturas()),
                                      font=ctk.CTkFont(size=32, weight="bold"),
                                      text_color=GREEN)
        self.lbl_cand.grid(row=17, column=0, padx=16, sticky="w")

        ctk.CTkLabel(scroll_sb, text="candidaturas via e-mail",
                     font=ctk.CTkFont(size=11), text_color=TEXT3
                     ).grid(row=18, column=0, padx=16, sticky="w", pady=(0, 16))

    def _content(self, parent):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.grid(row=0, column=1, sticky="nsew")
        col.grid_rowconfigure(1, weight=1)
        col.grid_columnconfigure(0, weight=1)

        # ── Stats bar ──
        self.stats = ctk.CTkFrame(col, fg_color=BG3, corner_radius=0, height=48)
        self.stats.grid(row=0, column=0, sticky="ew")
        self.stats.grid_propagate(False)
        self.stats.grid_columnconfigure(0, weight=1)

        self.lbl_stats = ctk.CTkLabel(self.stats, text="Aguardando busca...",
                                       font=ctk.CTkFont(size=12), text_color=TEXT3)
        self.lbl_stats.grid(row=0, column=0, padx=20, sticky="w")

        # ── Lista ──
        self.scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll.grid_columnconfigure(0, weight=1)

        self.lbl_vazio = ctk.CTkLabel(self.scroll,
                                       text="Clique em  ⟳ Buscar Vagas  para iniciar.",
                                       font=ctk.CTkFont(size=15), text_color=TEXT3)
        self.lbl_vazio.grid(row=0, column=0, pady=80)

        # ── Log ──
        self.log = ctk.CTkTextbox(col, height=100,
                                   font=ctk.CTkFont(family="Consolas", size=11),
                                   fg_color=BG, text_color=TEXT3,
                                   corner_radius=0, border_width=0)
        self.log.grid(row=2, column=0, sticky="ew")
        self.log.configure(state="disabled")

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _sel_cv(self):
        p = filedialog.askopenfilename(filetypes=[("PDF/Word", "*.pdf *.docx *.doc"), ("Todos", "*.*")])
        if p:
            self.cv_path = p
            self.lbl_cv.configure(text=os.path.basename(p))

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}]  {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _buscar(self):
        # Reseta estado
        self.vagas_cache  = []
        self.cards        = []
        self._urls_vistos = set()
        self._cards_ok    = False

        self.btn_buscar.configure(text="Buscando...", state="disabled")
        self.lbl_status.configure(text="Buscando em 8 fontes...")
        self.lbl_stats.configure(text="Aguardando primeiros resultados...")

        for w in self.scroll.winfo_children():
            w.destroy()
        self._lbl_aguard = ctk.CTkLabel(
            self.scroll, text="Buscando vagas... os cards aparecerao conforme cada fonte responde.",
            font=ctk.CTkFont(size=13), text_color=TEXT3)
        self._lbl_aguard.grid(row=0, column=0, pady=80)

        self._log("Iniciando busca em 8 fontes...")
        threading.Thread(target=self._worker_busca, daemon=True).start()

    def _worker_busca(self):
        from vagas import gupy, remotive, linkedin, programathor
        from vagas import weworkremotely, himalayas, infojobs, vagas_com

        # APIs rápidas primeiro
        FONTES = [
            ("Remotive",       lambda: remotive.buscar()),
            ("WeWorkRemotely", lambda: weworkremotely.buscar()),
            ("Himalayas",      lambda: himalayas.buscar()),
            ("Gupy",           lambda: gupy.buscar(TERMOS_BUSCA)),
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
        """Chamado no main thread após cada fonte terminar — adiciona cards ao vivo."""
        sc_min   = self.var_score.get()
        mods     = {m for m, v in [("Remoto", self.var_remoto), ("Hibrido", self.var_hibrido),
                                    ("Presencial", self.var_presencial)] if v.get()}
        so_email = self.var_so_email.get()

        novas = 0
        for v in vagas_brutas:
            url = v.get("url", "")
            if not url or url in self._urls_vistos:
                continue
            self._urls_vistos.add(url)
            v["score"] = calcular_score(v)
            v["_email_candidatura"] = aplicador.extrair_email_candidatura(v.get("descricao", ""))
            self.vagas_cache.append(v)

            if (v.get("score", 0) >= sc_min
                    and v.get("modalidade", "Presencial") in mods
                    and (not so_email or v.get("_email_candidatura"))):

                # Remove placeholder na primeira vaga relevante
                if not self._cards_ok:
                    for w in self.scroll.winfo_children():
                        w.destroy()
                    self._cards_ok = True

                row = len(self.cards)
                card = CardVaga(self.scroll, v, self)
                card.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 8))
                self.cards.append(card)
                novas += 1

        self._log(f"[{nome}] {len(vagas_brutas)} encontradas · {novas} cards adicionados")
        self._atualizar_stats()

    def _busca_completa(self):
        total = len(self.vagas_cache)
        self.btn_buscar.configure(text="⟳  Buscar Vagas", state="normal")
        self.lbl_status.configure(
            text=f"Última busca: {datetime.now().strftime('%d/%m  %H:%M')}  ·  {total} vagas")
        self._log(f"Busca concluida — {total} vagas unicas, {len(self.cards)} exibidas.")

        if not self._cards_ok:
            for w in self.scroll.winfo_children():
                w.destroy()
            ctk.CTkLabel(self.scroll,
                         text="Nenhuma vaga encontrada. Reduza o score minimo.",
                         font=ctk.CTkFont(size=14), text_color=TEXT3
                         ).grid(row=0, column=0, pady=80)

    def _atualizar_stats(self):
        r = sum(1 for v in self.vagas_cache if v.get("modalidade") == "Remoto")
        h = sum(1 for v in self.vagas_cache if v.get("modalidade") == "Hibrido")
        p = sum(1 for v in self.vagas_cache if v.get("modalidade") not in ("Remoto","Hibrido"))
        e = sum(1 for v in self.vagas_cache if v.get("_email_candidatura"))
        self.lbl_stats.configure(
            text=f"{len(self.cards)} exibidas  ·  {r} remotas  ·  {h} hibridas  ·  {p} presenciais  ·  {e} c/ e-mail"
        )

    def _filtrar(self, *_):
        """Re-renderiza do cache — chamado quando usuario muda filtros."""
        if not self.vagas_cache:
            return
        sc_min   = self.var_score.get()
        mods     = {m for m, v in [("Remoto", self.var_remoto), ("Hibrido", self.var_hibrido),
                                    ("Presencial", self.var_presencial)] if v.get()}
        so_email = self.var_so_email.get()

        filtradas = [
            v for v in self.vagas_cache
            if v.get("score", 0) >= sc_min
            and v.get("modalidade", "Presencial") in mods
            and (not so_email or v.get("_email_candidatura"))
        ]
        filtradas.sort(key=lambda v: (
            {"Remoto": 0, "Hibrido": 1}.get(v.get("modalidade", ""), 2),
            -v.get("score", 0)
        ))

        for w in self.scroll.winfo_children():
            w.destroy()
        self.cards.clear()
        self._cards_ok = bool(filtradas)

        if not filtradas:
            ctk.CTkLabel(self.scroll,
                         text="Nenhuma vaga com esses filtros. Reduza o score ou mude modalidade.",
                         font=ctk.CTkFont(size=13), text_color=TEXT3
                         ).grid(row=0, column=0, pady=80)
        else:
            for i, v in enumerate(filtradas):
                card = CardVaga(self.scroll, v, self)
                card.grid(row=i, column=0, sticky="ew", padx=16, pady=(0, 8))
                self.cards.append(card)

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
            self._log(f"Candidatura enviada: {vaga.get('titulo','')} → {email_dest}")

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
            messagebox.showinfo("Digest", "Todas as vagas já foram enviadas antes."); return

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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        import customtkinter
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter"], check=True)

    App().mainloop()
