"""Regressoes da janela de deduplicacao do historico."""

from datetime import datetime, timedelta

import banco


def _usar_banco_temporario(monkeypatch, tmp_path):
    caminho = tmp_path / "vagas_teste.db"
    monkeypatch.setattr(banco, "DB_PATH", str(caminho))
    return caminho


def test_historico_padrao_continua_permanente(monkeypatch, tmp_path):
    _usar_banco_temporario(monkeypatch, tmp_path)
    url = "https://example.test/vaga-antiga"
    banco.marcar_vista(url, "Analista de Suporte", "Empresa", "Teste", 50)

    antiga = (datetime.now() - timedelta(days=60)).isoformat()
    with banco._conn() as conn:
        conn.execute("UPDATE vagas_vistas SET data_vista = ? WHERE url = ?", (antiga, url))
        conn.commit()

    assert not banco.is_nova(url)


def test_digest_pode_usar_janela_de_trinta_dias(monkeypatch, tmp_path):
    _usar_banco_temporario(monkeypatch, tmp_path)
    url = "https://example.test/vaga-antiga"
    banco.marcar_vista(url, "Analista de Suporte", "Empresa", "Teste", 50)

    antiga = (datetime.now() - timedelta(days=60)).isoformat()
    with banco._conn() as conn:
        conn.execute("UPDATE vagas_vistas SET data_vista = ? WHERE url = ?", (antiga, url))
        conn.commit()

    assert banco.is_nova(url, janela_dias=30)
