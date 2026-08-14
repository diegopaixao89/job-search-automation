# config.py - perfil profissional + configuracoes da automacao
# Dados pessoais (email, cidade) sao lidos do .env para facilitar distribuicao.

import os

from dotenv import load_dotenv

from perfis_busca import (
    DESCRICAO_PESOS_COMPAT,
    PENALIZACOES_COMPAT,
    TERMOS_BUSCA as TERMOS_CURRICULOS,
    TITULO_PESOS_COMPAT,
)

load_dotenv()

EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "seu@gmail.com")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "seu@gmail.com")

CIDADE = os.getenv("CIDADE", "Rio de Janeiro")
ESTADO = os.getenv("ESTADO", "RJ")

# Presencial/hibrido e validado depois como cidade do Rio; remoto e global.
LOCAIS_BUSCA = [CIDADE, "remoto"]

# Termos sanitizados derivados dos dois curriculos (Infra + Dev).
TERMOS_BUSCA = list(TERMOS_CURRICULOS)

# Uma vaga precisa ter aderencia tecnica; modalidade so serve como bonus leve.
SCORE_MINIMO = 40

# Formato legado usado pela analise interativa de um unico CV. A busca padrao
# usa os dois perfis separados definidos em perfis_busca.py.
TITULO_PESOS = dict(TITULO_PESOS_COMPAT)
DESCRICAO_PESOS = dict(DESCRICAO_PESOS_COMPAT)
PENALIZACOES = dict(PENALIZACOES_COMPAT)

BONUS_REMOTO = 4
BONUS_HIBRIDO = 3
BONUS_PRESENCIAL = 3
