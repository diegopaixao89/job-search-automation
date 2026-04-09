# vagas/base.py — estrutura padrao de uma vaga

# Formato padrao de vaga retornado por todos os scrapers:
# {
#   "titulo":     str,
#   "empresa":    str,
#   "local":      str,       # cidade/estado ou "Remoto"
#   "modalidade": str,       # "Remoto" | "Hibrido" | "Presencial" | ""
#   "url":        str,       # link para candidatura
#   "descricao":  str,       # texto da descricao (pode ser vazio)
#   "data":       str,       # data de publicacao (ISO ou texto livre)
#   "plataforma": str,       # "Gupy" | "Remotive" | "Indeed" | "Vagas.com" | "ProgramaThor"
# }

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
