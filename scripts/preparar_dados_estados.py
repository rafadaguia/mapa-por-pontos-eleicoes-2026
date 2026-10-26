"""Versão por UF do mapa de pontos: votos para Presidente (1º turno 2026)
somados por estado e espalhados por toda a área do estado.

Reaproveita a leitura de votos e a geometria de preparar_dados.py e gera
dados/estados.js no mesmo formato de dados/municipios.js, com uma "região" por UF:
  munis:  [[nome do estado, sigla, [Lula, Flávio, Cury, Renan, Outros], [[tam. anel, ...], ...]], ...]

Malha: fontes/ufs_ibge.json (API de malhas v3 do IBGE, intrarregiao=UF, qualidade intermediária).
"""
import json
from pathlib import Path

from shapely.geometry import shape

from preparar_dados import CATS, escrever, ler_municipios, ler_votos, poligonos

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


def gravar_estados(votos, cats, saida):
    """Grava o arquivo de dados por UF.

    votos: DataFrame indexado pelo código TSE do município, uma coluna por categoria de `cats`.
    Os votos são somados por UF; o exterior fica de fora.
    """
    muns = ler_municipios()
    votos = votos[votos.index.isin(muns.index)]
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
        munis.append([nome, sigla, [int(r[c]) for c in cats], estrutura])
    print("UFs:", len(munis))

    escrever(saida, {c: int(por_uf[c].sum()) for c in cats}, munis, coords)


def main():
    gravar_estados(ler_votos(), CATS, SAIDA)


if __name__ == "__main__":
    main()
