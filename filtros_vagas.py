"""Normalizacao e elegibilidade geografica das vagas."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote


FONTES_REMOTAS_CONFIAVEIS = {"Remotive", "WeWorkRemotely", "Himalayas"}
FONTES_ESTRUTURADAS = {"Gupy"}
FONTES_LOCAL_DE_CONSULTA = {"Indeed", "InfoJobs", "LinkedIn", "ProgramaThor", "Vagas.com"}

# Algumas plataformas publicam apenas o bairro. A lista e deliberadamente
# conservadora: um nome desconhecido continua rejeitado para nao confundir uma
# cidade do estado com a capital.
BAIRROS_RIO = {
    "barra da tijuca",
    "botafogo",
    "campo grande",
    "centro",
    "copacabana",
    "flamengo",
    "gavea",
    "ilha do governador",
    "ipanema",
    "jacarepagua",
    "jardim botanico",
    "laranjeiras",
    "leblon",
    "maracana",
    "meier",
    "recreio dos bandeirantes",
    "sao conrado",
    "tijuca",
    "vila isabel",
}


def normalizar_texto(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    texto = re.sub(r"[^a-z0-9+#]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def detectar_modalidade(texto: str = "", local: str = "") -> str:
    """Detecta regime sem confundir 'suporte remoto' com vaga remota."""
    bruto = str(texto or "")
    t = normalizar_texto(f"{texto} {local}")
    local_n = normalizar_texto(local)

    if re.search(r"\b(hibrid[oa]|hybrid)\b", t):
        return "Hibrido"
    if re.search(r"\bpresencial\s+(?:e|ou)\s+remot[oa]\b", t):
        return "Hibrido"

    escalas_hibridas = [
        r"\bhome office\s+(?:uma|duas|tres|quatro|cinco|\d+)\s*(?:x|vez(?:es)?|dia(?:s)?)?\s*(?:por|na) semana\b",
        r"\bpossibilidade de home office(?:\s+(?:uma|duas|tres|\d+)\s*(?:x|vez(?:es)?|dia(?:s)?)?\s*(?:por|na) semana)?\b",
        r"\b(?:uma|dois|duas|tres|quatro|\d+) dias? presenciais?[^.;]{0,60}\bhome office\b",
        r"\bhome office[^.;]{0,60}\b(?:uma|dois|duas|tres|quatro|\d+) dias? presenciais?\b",
    ]
    if any(re.search(p, t) for p in escalas_hibridas):
        return "Hibrido"

    # Um marcador presencial explicito tem precedencia sobre expressoes como
    # "suporte remoto", "acesso remoto" ou "usuarios em trabalho remoto".
    sinais_presenciais = [
        r"\b(?:vaga|modelo|regime|trabalho|atuacao|posicao|atendimento) presencial\b",
        r"\bpresencial em\b",
        r"\b100\s+presencial\b",
    ]
    if "presencial" in local_n or any(re.search(p, t) for p in sinais_presenciais):
        return "Presencial"

    # Beneficio eventual nao transforma uma vaga presencial em remota.
    if re.search(r"\bhome office (?:eventual|ocasional|parcial)\b", t):
        return "Presencial"

    local_remoto = (
        local_n in {"remoto", "remote", "worldwide", "anywhere", "home office"}
        or local_n.startswith("remote ")
        or local_n.endswith(" remote")
    )
    texto_remoto_exato = normalizar_texto(bruto) in {
        "remoto", "remota", "remote", "home office", "worldwide", "anywhere",
    }
    marcador_remoto = bool(re.search(
        r"(?:[-–—|(/:]\s*)(?:100\s*%?\s*)?(?:remot[oa]|remote|home\s+office)\s*\)?\s*$",
        bruto,
        re.IGNORECASE,
    ))
    marcador_remoto_no_titulo = bool(
        re.search(r"^\s*(?:remot[oa]|remote)\b", bruto, re.IGNORECASE)
        or re.search(
            r"[\[(]\s*(?:remot[oa]|remote)\b[^\])]{0,30}[\])]",
            bruto,
            re.IGNORECASE,
        )
        or re.search(
            r"(?:^|\s[-–—|]\s*)(?:remot[oa]|remote)\s*[:\-–—]",
            bruto,
            re.IGNORECASE,
        )
    )
    sinais_remotos = [
        r"\b100\s+remot[oa]\b",
        r"\btrabalho remot[oa]\b",
        r"\bvaga remot[oa]\b",
        r"\bmodelo remot[oa]\b",
        r"\bregime remot[oa]\b",
        r"\batuacao remot[oa]\b",
        r"\bposicao remot[oa]\b",
        r"\bhome office\b",
        r"\bfully remote\b",
        r"\bremote (?:position|role|job|work)\b",
        r"\bwork from (?:home|anywhere)\b",
        r"\banywhere in the world\b",
    ]
    if (
        local_remoto
        or texto_remoto_exato
        or marcador_remoto
        or marcador_remoto_no_titulo
        or any(re.search(padrao, t) for padrao in sinais_remotos)
    ):
        return "Remoto"
    return "Presencial"


def normalizar_modalidade_vaga(vaga: dict) -> str:
    plataforma = vaga.get("plataforma", "")
    informada = normalizar_texto(vaga.get("modalidade", ""))

    if plataforma in FONTES_REMOTAS_CONFIAVEIS:
        return "Remoto"

    if vaga.get("modalidade_confiavel") or plataforma in FONTES_ESTRUTURADAS:
        if informada in {"remoto", "remote"}:
            return "Remoto"
        if informada in {"hibrido", "hybrid"}:
            return "Hibrido"
        return "Presencial"

    texto = " ".join([
        vaga.get("titulo", "") or "",
        vaga.get("descricao", "") or "",
        vaga.get("modalidade", "") or "",
    ])
    return detectar_modalidade(texto, vaga.get("local", "") or "")


def _local_da_url(url: str) -> str:
    caminho = normalizar_texto(unquote(url).replace("_", " "))
    if " em rio de janeiro " in f" {caminho} ":
        return "Rio de Janeiro, RJ"

    bruto = unquote(url).lower()
    encontrados = re.findall(r"-em-([a-z0-9-]+?)(?:__|\.aspx|[/?#]|$)", bruto)
    if encontrados:
        return encontrados[-1].replace("-", " ").title()
    return ""


def extrair_localizacao_anuncio(texto: str, url: str = "") -> str:
    """Extrai apenas local indicado pelo anuncio, nunca o parametro da busca."""
    t = str(texto or "")

    # Um campo rotulado e mais confiavel do que cidades mencionadas no restante
    # da descricao (por exemplo, a area de atendimento da empresa).
    rotulado = re.search(
        r"(?:^|[\n;|])\s*(?:local|localidade|cidade)\s*[:\-]\s*([^\n;|]+)",
        t,
        re.IGNORECASE,
    )
    if rotulado:
        return rotulado.group(1).strip(" -–—,.")

    # Captura a localidade imediatamente anterior a UF, sem engolir o titulo do
    # card. Se houver duas cidades distintas, o anuncio e ambiguo e sera
    # rejeitado em vez de escolher a mencao mais conveniente.
    pares = re.findall(
        r"\b([A-ZÀ-Ý][A-Za-zÀ-ÿ'’]*(?:[ \t]+(?:d[aeo]s?|D[aeo]s?|[A-ZÀ-Ý][A-Za-zÀ-ÿ'’]*)){0,4})"
        r"\s*[/\-–—]\s*(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b",
        t,
    )
    unicos: dict[str, tuple[str, str]] = {}
    for cidade, uf in pares:
        unicos[normalizar_texto(cidade)] = (cidade.strip(), uf)
    if len(unicos) > 1:
        return ""
    if unicos:
        cidade, uf = next(iter(unicos.values()))
        return f"{cidade}, {uf}"

    if re.search(
        r"\bRio\s+de\s+Janeiro\s*,\s*(?:Rio\s+de\s+Janeiro|Brazil|Brasil)\b",
        t,
        re.IGNORECASE,
    ):
        return "Rio de Janeiro, RJ"

    return _local_da_url(url)


def localizacao_confirmada(vaga: dict) -> str:
    local_real = (vaga.get("local_real") or "").strip()
    if local_real:
        return local_real

    local = (vaga.get("local") or "").strip()
    if vaga.get("local_confiavel"):
        return local

    plataforma = vaga.get("plataforma", "")
    if plataforma in FONTES_LOCAL_DE_CONSULTA:
        texto = " ".join([
            vaga.get("titulo", "") or "",
            vaga.get("descricao", "") or "",
        ])
        return extrair_localizacao_anuncio(texto, vaga.get("url", "") or "")

    if plataforma in FONTES_ESTRUTURADAS:
        return ""

    return local


def eh_cidade_rio(local: str) -> bool:
    n = normalizar_texto(local)
    if not n or n in {"rj", "rio de janeiro estado", "estado do rio de janeiro"}:
        return False
    if (
        "regiao metropolitana" in n
        or "rio de janeiro e regiao" in n
        or "greater rio de janeiro" in n
    ):
        return False

    # Em "Niteroi, Rio de Janeiro, Brazil", Rio de Janeiro e o estado. A
    # primeira parte precisa ser a cidade da capital (ou um bairro conhecido).
    partes = [
        normalizar_texto(p)
        for p in re.split(r"\s*[,/|]\s*|\s+[\-–—]\s+", str(local or ""))
        if normalizar_texto(p)
    ]
    primeiro = partes[0] if partes else n
    if primeiro == "rio de janeiro":
        return True
    if re.fullmatch(
        r"rio de janeiro(?:\s+(?:rj|rio de janeiro|brazil|brasil)){1,3}",
        n,
    ):
        return True
    if primeiro in BAIRROS_RIO:
        complemento = " ".join(partes[1:])
        return bool(re.search(r"\b(?:rj|rio de janeiro)\b", complemento))
    return False


def preparar_vaga(vaga: dict) -> dict:
    vaga["modalidade"] = normalizar_modalidade_vaga(vaga)
    if vaga["modalidade"] != "Remoto":
        confirmado = localizacao_confirmada(vaga)
        vaga["local_confirmado"] = confirmado
        if confirmado:
            vaga["local"] = confirmado
    return vaga


def vaga_elegivel_geograficamente(vaga: dict) -> bool:
    preparar_vaga(vaga)
    if vaga.get("modalidade") == "Remoto":
        return True
    return eh_cidade_rio(vaga.get("local_confirmado", ""))
