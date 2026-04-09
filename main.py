# main.py — orquestrador da automacao de vagas

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from config import EMAIL_DESTINO, EMAIL_REMETENTE, TERMOS_BUSCA, SCORE_MINIMO
from matcher import calcular_score
import banco
import notificador
from vagas import gupy, remotive, linkedin, programathor, weworkremotely, himalayas, infojobs, vagas_com


FONTES = [
    ("Gupy",            lambda: gupy.buscar(TERMOS_BUSCA)),
    ("LinkedIn",        lambda: linkedin.buscar()),
    ("Remotive",        lambda: remotive.buscar()),
    ("WeWorkRemotely",  lambda: weworkremotely.buscar()),
    ("Himalayas",       lambda: himalayas.buscar()),
    ("InfoJobs",        lambda: infojobs.buscar()),
    ("ProgramaThor",    lambda: programathor.buscar(["rio de janeiro", "remoto"])),
    ("Vagas.com",       lambda: vagas_com.buscar()),
]


def coletar() -> list[dict]:
    todas = []
    for i, (nome, fn) in enumerate(FONTES, 1):
        print(f"[{i}/{len(FONTES)}] {nome}...")
        try:
            resultado = fn()
            print(f"      {len(resultado)} vagas encontradas")
            todas.extend(resultado)
        except Exception as e:
            print(f"      Erro: {e}")
    return todas


def processar(todas: list[dict]) -> list[dict]:
    # Deduplicacao por URL
    urls_vistas = set()
    sem_dup = []
    for v in todas:
        url = v.get("url", "")
        if url and url not in urls_vistas:
            urls_vistas.add(url)
            sem_dup.append(v)

    # Scoring
    for v in sem_dup:
        v["score"] = calcular_score(v)

    # Filtrar por score minimo
    filtradas = [v for v in sem_dup if v["score"] >= SCORE_MINIMO]

    # Ordenar: remoto > hibrido > presencial, depois por score
    filtradas.sort(key=lambda v: (
        {"Remoto": 0, "Hibrido": 1}.get(v.get("modalidade", ""), 2),
        -v.get("score", 0)
    ))

    return filtradas


def main():
    print("=" * 60)
    print("Automacao de Vagas - iniciando busca")
    print("=" * 60)

    senha_app = os.getenv("GMAIL_APP_PASSWORD")
    if not senha_app:
        print("[ERRO] GMAIL_APP_PASSWORD nao definida no .env")
        sys.exit(1)

    todas     = coletar()
    filtradas = processar(todas)

    novas = [v for v in filtradas if banco.is_nova(v["url"])]

    remotas    = len([v for v in filtradas if v.get("modalidade") == "Remoto"])
    hibridas   = len([v for v in filtradas if v.get("modalidade") == "Hibrido"])
    presenciais = len([v for v in filtradas if v.get("modalidade") not in ("Remoto", "Hibrido")])

    print(f"\nTotal bruto: {len(todas)} | Unicas: {len(filtradas)} relevantes")
    print(f"Remotas: {remotas} | Hibridas: {hibridas} | Presenciais: {presenciais}")
    print(f"Vagas novas (nao enviadas antes): {len(novas)}")

    if not novas:
        print("\nNenhuma vaga nova. Nada a enviar.")
        return

    print(f"\nEnviando digest para {EMAIL_DESTINO}...")
    notificador.enviar_digest(novas, EMAIL_DESTINO, EMAIL_REMETENTE, senha_app)

    for v in novas:
        banco.marcar_vista(v["url"], v["titulo"], v.get("empresa", ""), v["plataforma"], v["score"])

    print(f"\nConcluido. {len(novas)} vagas novas enviadas.")
    print(f"Total historico no banco: {banco.total_vistas()} vagas")


if __name__ == "__main__":
    main()
