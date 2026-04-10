"""
Testes para matcher.py — cálculo de score de aderência de vagas.
"""
import pytest
from matcher import calcular_score, keywords_encontradas

# Perfil de teste isolado (não depende do config.py real)
PERFIL_TESTE = {
    "TITULO_PESOS":    {"python": 25, "automacao": 25, "devops": 18, "suporte": 15},
    "DESCRICAO_PESOS": {"docker": 10, "api": 8, "linux": 5},
    "PENALIZACOES":    {"react": -8, "frontend": -10, "java": -10},
    "BONUS_REMOTO":    15,
    "BONUS_HIBRIDO":   10,
}


class TestCalcularScore:

    def test_vaga_perfeita_retorna_score_alto(self):
        vaga = {
            "titulo": "Desenvolvedor Python Automacao",
            "descricao": "Trabalha com docker e api rest",
            "modalidade": "Remoto",
        }
        score = calcular_score(vaga, PERFIL_TESTE)
        assert score >= 60

    def test_vaga_sem_match_retorna_zero(self):
        vaga = {
            "titulo": "Designer Gráfico",
            "descricao": "Criação de layouts e artes para redes sociais",
            "modalidade": "Presencial",
        }
        score = calcular_score(vaga, PERFIL_TESTE)
        assert score == 0

    def test_penalizacao_reduz_score(self):
        vaga_sem_pen = {
            "titulo": "Desenvolvedor Python",
            "descricao": "Automação de processos",
            "modalidade": "Presencial",
        }
        vaga_com_pen = {
            "titulo": "Desenvolvedor Python React",
            "descricao": "Automação de processos frontend",
            "modalidade": "Presencial",
        }
        score_sem = calcular_score(vaga_sem_pen, PERFIL_TESTE)
        score_com = calcular_score(vaga_com_pen, PERFIL_TESTE)
        assert score_com < score_sem

    def test_bonus_remoto_aumenta_score(self):
        base = {"titulo": "Analista Python", "descricao": "", "modalidade": "Presencial"}
        remoto = {"titulo": "Analista Python", "descricao": "", "modalidade": "Remoto"}
        assert calcular_score(remoto, PERFIL_TESTE) > calcular_score(base, PERFIL_TESTE)

    def test_bonus_hibrido_aumenta_score(self):
        base = {"titulo": "Analista Python", "descricao": "", "modalidade": "Presencial"}
        hibrido = {"titulo": "Analista Python", "descricao": "", "modalidade": "Híbrido"}
        assert calcular_score(hibrido, PERFIL_TESTE) > calcular_score(base, PERFIL_TESTE)

    def test_score_nunca_negativo(self):
        vaga = {
            "titulo": "Frontend React Java",
            "descricao": "React frontend java spring",
            "modalidade": "Presencial",
        }
        assert calcular_score(vaga, PERFIL_TESTE) >= 0

    def test_score_nunca_acima_100(self):
        vaga = {
            "titulo": "Python automacao devops suporte",
            "descricao": "docker api linux python automacao devops",
            "modalidade": "Remoto",
        }
        assert calcular_score(vaga, PERFIL_TESTE) <= 100

    def test_vaga_vazia_retorna_zero(self):
        assert calcular_score({}, PERFIL_TESTE) == 0

    def test_case_insensitive(self):
        vaga_lower = {"titulo": "python developer", "descricao": "", "modalidade": ""}
        vaga_upper = {"titulo": "PYTHON DEVELOPER", "descricao": "", "modalidade": ""}
        assert calcular_score(vaga_lower, PERFIL_TESTE) == calcular_score(vaga_upper, PERFIL_TESTE)


class TestKeywordsEncontradas:

    def test_retorna_keywords_presentes(self):
        vaga = {"titulo": "Python Automacao", "descricao": "usa docker e api"}
        kws = keywords_encontradas(vaga, PERFIL_TESTE)
        assert "python" in kws
        assert "automacao" in kws

    def test_nao_retorna_keywords_ausentes(self):
        vaga = {"titulo": "Python Developer", "descricao": ""}
        kws = keywords_encontradas(vaga, PERFIL_TESTE)
        assert "devops" not in kws
        assert "docker" not in kws

    def test_limite_de_8_keywords(self):
        vaga = {
            "titulo": "python automacao devops suporte",
            "descricao": "docker api linux react frontend java",
        }
        kws = keywords_encontradas(vaga, PERFIL_TESTE)
        assert len(kws) <= 8

    def test_sem_duplicatas(self):
        vaga = {"titulo": "python python python", "descricao": "python python"}
        kws = keywords_encontradas(vaga, PERFIL_TESTE)
        assert len(kws) == len(set(kws))

    def test_vaga_vazia_retorna_lista_vazia(self):
        assert keywords_encontradas({}, PERFIL_TESTE) == []
