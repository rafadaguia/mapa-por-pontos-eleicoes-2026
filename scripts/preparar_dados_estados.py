"""Versão por UF do mapa de pontos: votos para Presidente (1º turno 2026)
somados por estado e espalhados por toda a área do estado.

Reaproveita a leitura de votos e a geometria de preparar_dados.py e gera
dados/estados.js no mesmo formato de dados/municipios.js, com uma "região" por UF:
  munis:  [[nome do estado, sigla, [Lula, Flávio, Cury, Renan, Outros], [[tam. anel, ...], ...]], ...]

Malha: fontes/ufs_ibge.json (API de malhas v3 do IBGE, intrarregiao=UF, qualidade intermediária).
"""
import base64, gzip, json
from pathlib import Path

import numpy as np
from shapely.geometry import shape

from preparar_dados import CATS, ler_municipios, ler_votos, poligonos

REPO = Path(__file__).resolve().parent.parent
MALHA = REPO / "fontes" / "ufs_ibge.json"
SAIDA = REPO / "dados" / "estados.js"

UFS = {
    "11": ("RO", "Rondônia"), "12": ("AC", "Acre"), "13": ("AM", "Amazonas"), "14": ("RR", "Roraima"),
    "15": ("PA", "Pará"), "16": ("AP", "Amapá"), "17": ("TO", "Tocantins"), "21": ("MA", "Maranhão"),
    "22": ("PI", "Piauí"), "23": ("CE", "Ceará"), "24": ("RN", "Rio Grande do Norte"), "25": ("PB", "Paraíba"),
    "26": ("PE", "Pernambuco"), "27": ("AL", "Alagoas"), "28": ("SE", "Sergipe"), "29": ("BA", "Bahia"),
    "31": ("MG", "Minas Gerais"), "32": ("ES", "Espírito Santo"), "33": ("RJ", "Rio de Janeiro"),
    "35": ("SP", "São Paulo"), "41": ("PR", "Paraná"), "42": ("SC", "Santa Catarina"),
    "43": ("RS", "Rio Grande do Sul"), "50": ("MS", "Mato Grosso do Sul"), "51": ("MT", "Mato Grosso"),
    "52": ("GO", "Goiás"), "53": ("DF", "Distrito Federal"),
}


def main():
    votos = ler_votos()
    muns = ler_municipios()
    votos = votos[votos.index.isin(muns.index)]  # tira o exterior
    por_uf = votos.groupby(muns.loc[votos.index, "uf"].to_numpy()).sum()

    munis, coords = [], []
    for f in json.load(open(MALHA))["features"]:
        sigla, nome = UFS[f["properties"]["codarea"]]
        geom = shape(f["geometry"]).simplify(0.005, preserve_topology=True)  # ~500 m
        estrutura = []
        for aneis in poligonos(geom):
            estrutura.append([len(a) for a in aneis])
            coords.extend(aneis)
        r = por_uf.loc[sigla]
        munis.append([nome, sigla, [int(r[c]) for c in CATS], estrutura])

    # Coordenadas em décimos de milésimo de grau (~11 m), codificadas como diferenças
    q = np.round(np.vstack(coords) * 1e4).astype(np.int64)
    d = np.diff(q, axis=0, prepend=np.zeros((1, 2), np.int64)).astype("<i4")
    verts_b64 = base64.b64encode(gzip.compress(d.tobytes(), 9)).decode()
    print("UFs:", len(munis), "vértices:", len(q))

    totais = {c: int(por_uf[c].sum()) for c in CATS}
    SAIDA.write_text(
        f"window.DADOS={{totais:{json.dumps(totais)},"
        f"munis:{json.dumps(munis, ensure_ascii=False, separators=(',', ':'))},"
        f"verts:\"{verts_b64}\"}};\n")
    print(totais, f"{SAIDA.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
