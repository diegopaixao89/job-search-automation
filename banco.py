# banco.py — SQLite para deduplicacao de vagas ja vistas

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "vagas_vistas.db")


def _adicionar_coluna_se_nao_existe(conn, tabela: str, coluna: str, tipo: str):
    try:
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
    except sqlite3.OperationalError:
        pass  # coluna ja existe


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vagas_vistas (
            url TEXT PRIMARY KEY,
            titulo TEXT,
            empresa TEXT,
            plataforma TEXT,
            score INTEGER,
            data_vista TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidaturas (
            url TEXT PRIMARY KEY,
            titulo TEXT,
            empresa TEXT,
            email_destino TEXT,
            curriculo TEXT,
            data_envio TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS geocoding_cache (
            endereco_norm TEXT PRIMARY KEY,
            lat REAL,
            lon REAL,
            data_cache TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS curriculo_cache (
            cv_hash TEXT PRIMARY KEY,
            cv_path TEXT,
            data_analise TEXT,
            texto_extraido TEXT,
            resultado_json TEXT
        )
    """)
    # Migration segura: adiciona colunas novas em vagas_vistas sem quebrar dados existentes
    _adicionar_coluna_se_nao_existe(c, "vagas_vistas", "idioma", "TEXT DEFAULT 'pt'")
    _adicionar_coluna_se_nao_existe(c, "vagas_vistas", "idioma_obrigatorio", "TEXT")
    _adicionar_coluna_se_nao_existe(c, "vagas_vistas", "pais", "TEXT DEFAULT 'BR'")
    _adicionar_coluna_se_nao_existe(c, "vagas_vistas", "distancia_km", "REAL")
    c.commit()
    return c


# ---------------------------------------------------------------------------
# Vagas vistas
# ---------------------------------------------------------------------------

def is_nova(url: str) -> bool:
    with _conn() as c:
        r = c.execute("SELECT 1 FROM vagas_vistas WHERE url = ?", (url,)).fetchone()
        return r is None


def marcar_vista(
    url: str, titulo: str, empresa: str, plataforma: str, score: int,
    idioma: str = "pt",
    idioma_obrigatorio: str | None = None,
    pais: str = "BR",
    distancia_km: float | None = None,
):
    with _conn() as c:
        c.execute(
            """INSERT OR IGNORE INTO vagas_vistas
               (url, titulo, empresa, plataforma, score, data_vista,
                idioma, idioma_obrigatorio, pais, distancia_km)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (url, titulo, empresa, plataforma, score,
             datetime.now().isoformat(),
             idioma, idioma_obrigatorio, pais, distancia_km),
        )
        c.commit()


def total_vistas() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM vagas_vistas").fetchone()[0]


# ---------------------------------------------------------------------------
# Candidaturas
# ---------------------------------------------------------------------------

def ja_aplicou(url: str) -> bool:
    with _conn() as c:
        r = c.execute("SELECT 1 FROM candidaturas WHERE url = ?", (url,)).fetchone()
        return r is not None


def registrar_candidatura(url: str, titulo: str, empresa: str,
                          email_destino: str, curriculo: str, status: str = "enviado"):
    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO candidaturas
               (url, titulo, empresa, email_destino, curriculo, data_envio, status)
               VALUES (?,?,?,?,?,?,?)""",
            (url, titulo, empresa, email_destino, curriculo,
             datetime.now().isoformat(), status),
        )
        c.commit()


def total_candidaturas() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM candidaturas").fetchone()[0]


def listar_candidaturas() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT url, titulo, empresa, email_destino, data_envio, status FROM candidaturas ORDER BY data_envio DESC"
        ).fetchall()
        return [
            {"url": r[0], "titulo": r[1], "empresa": r[2],
             "email_destino": r[3], "data_envio": r[4], "status": r[5]}
            for r in rows
        ]


# ---------------------------------------------------------------------------
# Cache geocoding
# ---------------------------------------------------------------------------

def geocode_get(endereco_norm: str) -> tuple[float, float] | None:
    with _conn() as c:
        r = c.execute(
            "SELECT lat, lon FROM geocoding_cache WHERE endereco_norm = ?",
            (endereco_norm,)
        ).fetchone()
        return (r[0], r[1]) if r else None


def geocode_set(endereco_norm: str, lat: float, lon: float):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO geocoding_cache (endereco_norm, lat, lon, data_cache) VALUES (?,?,?,?)",
            (endereco_norm, lat, lon, datetime.now().isoformat()),
        )
        c.commit()
