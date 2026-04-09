# banco.py — SQLite para deduplicacao de vagas ja vistas

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "vagas_vistas.db")


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
    c.commit()
    return c


def is_nova(url: str) -> bool:
    with _conn() as c:
        r = c.execute("SELECT 1 FROM vagas_vistas WHERE url = ?", (url,)).fetchone()
        return r is None


def marcar_vista(url: str, titulo: str, empresa: str, plataforma: str, score: int):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO vagas_vistas (url, titulo, empresa, plataforma, score, data_vista) VALUES (?,?,?,?,?,?)",
            (url, titulo, empresa, plataforma, score, datetime.now().isoformat()),
        )
        c.commit()


def total_vistas() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM vagas_vistas").fetchone()[0]


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
