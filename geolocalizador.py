# geolocalizador.py — geocodificacao e calculo de distancia

import os
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))
import banco
import config

_ultimo_request: float = 0.0
_RATE_LIMIT = 1.1  # segundos entre chamadas Nominatim


def _geocodificar_raw(endereco: str) -> tuple[float, float] | None:
    """Chama Nominatim respeitando rate limit de 1 req/seg."""
    global _ultimo_request
    try:
        from geopy.geocoders import Nominatim
        agora = time.time()
        espera = _RATE_LIMIT - (agora - _ultimo_request)
        if espera > 0:
            time.sleep(espera)
        _ultimo_request = time.time()
        geo = Nominatim(user_agent="cacavagas-diegopaixao/2.0", timeout=10)
        loc = geo.geocode(endereco)
        if loc:
            return (loc.latitude, loc.longitude)
        return None
    except Exception:
        return None


def geocodificar(endereco: str) -> tuple[float, float] | None:
    """
    Geocodifica um endereco com cache SQLite.
    Retorna (lat, lon) ou None.
    """
    if not endereco:
        return None
    norm = endereco.strip().lower()
    # Checar cache
    cached = banco.geocode_get(norm)
    if cached:
        return cached
    # Chamar API
    coords = _geocodificar_raw(endereco)
    if coords:
        banco.geocode_set(norm, coords[0], coords[1])
    return coords


def geocodificar_usuario(cidade: str | None = None, estado: str | None = None) -> tuple[float, float] | None:
    """
    Geocodifica a localizacao do usuario.
    Usa config.CIDADE + config.ESTADO como padrao.
    """
    cidade = cidade or getattr(config, "CIDADE", "Rio de Janeiro")
    estado = estado or getattr(config, "ESTADO", "RJ")
    endereco = f"{cidade}, {estado}, Brasil"
    return geocodificar(endereco)


def normalizar_local_para_geo(local: str, modalidade: str, pais: str) -> str | None:
    """
    Converte o campo `local` de uma vaga em endereco geocodificavel.
    Retorna None para vagas remotas ou com local indeterminado.
    """
    if not local:
        return None
    mod = modalidade.lower() if modalidade else ""
    if "remot" in mod or "remote" in mod:
        return None
    local_l = local.lower().strip()
    if local_l in ("worldwide", "remoto", "remote", "brazil", "brasil", "", "—", "-"):
        return None

    # Ja tem formato geocodificavel?
    if "," in local and len(local) > 6:
        # Ex: "Rio de Janeiro, RJ, Brasil" — usar como esta
        if pais == "BR" and "brasil" not in local_l and "brazil" not in local_l:
            return f"{local}, Brasil"
        return local

    # Formato simples: "Rio de Janeiro" -> "Rio de Janeiro, RJ, Brasil"
    if pais == "BR":
        return f"{local}, Brasil"
    return local


def distancia_vaga(vaga: dict, coords_usuario: tuple[float, float]) -> float | None:
    """
    Calcula a distancia em km entre o usuario e a localizacao de uma vaga.
    Retorna None para vagas remotas ou se geocoding falhar.
    """
    if not coords_usuario:
        return None
    modalidade = vaga.get("modalidade", "")
    if modalidade == "Remoto":
        return None

    local = vaga.get("local", "")
    pais = vaga.get("pais", "BR")
    endereco = normalizar_local_para_geo(local, modalidade, pais)
    if not endereco:
        return None

    # Verificar cache no dict da vaga
    if "_coords" in vaga:
        coords_vaga = vaga["_coords"]
    else:
        coords_vaga = geocodificar(endereco)
        vaga["_coords"] = coords_vaga

    if not coords_vaga:
        return None

    try:
        from haversine import haversine, Unit
        dist = haversine(coords_usuario, coords_vaga, unit=Unit.KILOMETERS)
        return round(dist, 1)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Teste direto
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Teste geolocalizador.py\n" + "=" * 40)
    print("Geocodificando usuario (Rio de Janeiro, RJ)...")
    coords = geocodificar_usuario()
    print(f"Coords usuario: {coords}")

    enderecos_teste = [
        "Niterói, RJ, Brasil",
        "São Paulo, SP, Brasil",
        "Belo Horizonte, MG, Brasil",
        "Rio de Janeiro, Brasil",
    ]
    for end in enderecos_teste:
        coords_end = geocodificar(end)
        if coords and coords_end:
            from haversine import haversine, Unit
            dist = haversine(coords, coords_end, unit=Unit.KILOMETERS)
            print(f"{end}: {dist:.1f} km")
        else:
            print(f"{end}: falhou")
