"""Gera os dados do mapa de pontos: votos para Presidente (1º turno 2026),
somados por município e espalhados por toda a área do município.

Entradas:
  - analise-2t - por bairro/dados_bairros/tse/votacao_secao_2026_BR.zip   votos por seção (TSE)
  - dados-tse-2026-1T/csv/candidatos/municipio/presidente/*.csv           código TSE -> IBGE e nomes
  - fontes/municipios_ibge.json   malha municipal do IBGE (API de malhas v3, qualidade intermediária)
  - proc/locais_geo_2026.parquet  locais de votação, para município ainda sem malha

O navegador triangula cada município, subdivide os triângulos até terem
poucos votos esperados e reparte os votos de cada candidato entre eles na
proporção da área. A posição de cada voto é sorteada dentro do triângulo.

Saída: dados/municipios.js
  totais: votos por candidato no mapa
  munis:  [[nome, uf, [Lula, Flávio, Cury, Renan, Outros], [[tam. anel, ...], ...]], ...]
          a última lista dá, por polígono, o número de vértices de cada anel
  verts:  gzip+base64 de pares int32 (lon, lat) * 1e4, como diferença do vértice anterior
"""
import base64, glob, gzip, io, json, zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.csv as pacsv
from shapely.geometry import shape, MultiPoint, Polygon, MultiPolygon
from shapely.validation import make_valid

REPO = Path(__file__).resolve().parent.parent
# Os arquivos do TSE ficam fora do repositório (são grandes); ajuste RAIZ se estiverem em outro lugar
RAIZ = REPO.parent
ZIP = RAIZ / "analise-2t - por bairro" / "dados_bairros" / "tse" / "votacao_secao_2026_BR.zip"
MUN_CSV = RAIZ / "dados-tse-2026-1T" / "csv" / "candidatos" / "municipio" / "presidente"
MALHA = REPO / "fontes" / "municipios_ibge.json"
LOCAIS = RAIZ / "analise-2t - por bairro" / "dados_bairros" / "proc" / "locais_geo_2026.parquet"
SAIDA = REPO / "dados" / "municipios.js"

CATS = ["lula", "flavio", "cury", "renan", "outros"]


def ler_votos():
    with zipfile.ZipFile(ZIP) as z, z.open("votacao_secao_2026_BR.csv") as f:
        tab = pacsv.read_csv(
            f,
            read_options=pacsv.ReadOptions(encoding="latin1", block_size=1 << 26),
            parse_options=pacsv.ParseOptions(delimiter=";"),
            convert_options=pacsv.ConvertOptions(include_columns=[
                "NR_TURNO", "CD_CARGO", "SG_UF", "CD_MUNICIPIO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS"]),
        )
    df = tab.to_pandas()
    df = df[(df.NR_TURNO == 1) & (df.CD_CARGO == 1) & ~df.NR_VOTAVEL.isin([95, 96])]
    cat = {13: 0, 22: 1}
    for n, nome in df.groupby("NR_VOTAVEL").NM_VOTAVEL.first().items():
        if "CURY" in nome: cat[n] = 2
        if "RENAN" in nome: cat[n] = 3
    df["cat"] = df.NR_VOTAVEL.map(cat).fillna(4).astype(int)
    v = df.pivot_table(index="CD_MUNICIPIO", columns="cat", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    v = v.reindex(columns=range(5), fill_value=0)
    v.columns = CATS
    return v


def ler_municipios():
    cols = ["uf", "cd_municipio_tse", "cd_municipio_ibge", "municipio"]
    m = pd.concat(pd.read_csv(f, usecols=cols, dtype=str) for f in glob.glob(str(MUN_CSV / "*.csv")))
    m = m.drop_duplicates("cd_municipio_tse")
    m = m[m.uf != "ZZ"]
    m["cd_municipio_tse"] = m.cd_municipio_tse.astype(int)
    return m.set_index("cd_municipio_tse")


def poligonos(geom):
    """Lista de polígonos, cada um uma lista de anéis (exterior primeiro), em lon/lat."""
    geom = make_valid(geom)
    if isinstance(geom, Polygon): partes = [geom]
    elif isinstance(geom, MultiPolygon): partes = list(geom.geoms)
    else:
        partes = []
        for g in getattr(geom, "geoms", []):
            if isinstance(g, Polygon): partes.append(g)
            elif isinstance(g, MultiPolygon): partes.extend(g.geoms)
    out = []
    for p in partes:
        aneis = [np.asarray(p.exterior.coords)[:-1]] + [np.asarray(r.coords)[:-1] for r in p.interiors]
        aneis = [a for a in aneis if len(a) >= 3]
        if aneis: out.append(aneis)
    return out


def gravar_municipios(votos, cats, saida):
    """Grava o arquivo de dados por município.

    votos: DataFrame indexado pelo código TSE do município, uma coluna por categoria de `cats`.
    Municípios fora da tabela do TSE (exterior) ficam de fora.
    """
    muns = ler_municipios()
    malha = {f["properties"]["codarea"]: f["geometry"] for f in json.load(open(MALHA))["features"]}
    locais = pd.read_parquet(LOCAIS, columns=["cd_mun_tse", "lat", "lon"]).dropna()

    munis, coords = [], []
    for cd_tse, r in votos.iterrows():
        if cd_tse not in muns.index: continue  # exterior
        info = muns.loc[cd_tse]
        g = malha.get(info.cd_municipio_ibge)
        if g is not None:
            geom = shape(g)
            # Simplifica conforme o tamanho do município (~0,4% do lado equivalente, 50 m a 1 km)
            geom = geom.simplify(float(np.clip(np.sqrt(geom.area) * 0.004, 0.0005, 0.01)), preserve_topology=True)
        else:
            # Município novo, ainda fora da malha do IBGE: área ao redor dos seus locais de votação
            l = locais[locais.cd_mun_tse == cd_tse]
            geom = MultiPoint(l[["lon", "lat"]].to_numpy()).convex_hull.buffer(0.12).simplify(0.005)
            print("sem malha, usando entorno dos locais:", info.municipio, info.uf)
        polis = poligonos(geom)
        estrutura = []
        for aneis in polis:
            estrutura.append([len(a) for a in aneis])
            coords.extend(aneis)
        nome = info.municipio.title() if info.municipio.isupper() else info.municipio
        munis.append([nome, info.uf, [int(r[c]) for c in cats], estrutura])
    print("municípios:", len(munis))

    totais = {c: int(votos.loc[votos.index.isin(muns.index), c].sum()) for c in cats}
    escrever(saida, totais, munis, coords)


def escrever(saida, totais, munis, coords):
    # Coordenadas em décimos de milésimo de grau (~11 m), codificadas como diferenças
    q = np.round(np.vstack(coords) * 1e4).astype(np.int64)
    d = np.diff(q, axis=0, prepend=np.zeros((1, 2), np.int64)).astype("<i4")
    verts_b64 = base64.b64encode(gzip.compress(d.tobytes(), 9, mtime=0)).decode()
    saida.write_text(
        f"window.DADOS={{totais:{json.dumps(totais)},"
        f"munis:{json.dumps(munis, ensure_ascii=False, separators=(',', ':'))},"
        f"verts:\"{verts_b64}\"}};\n")
    print("vértices:", len(q), totais, f"{saida.stat().st_size / 1e6:.2f} MB")


def main():
    votos = ler_votos()
    print("votos nominais:", int(votos.to_numpy().sum()))
    gravar_municipios(votos, CATS, SAIDA)


if __name__ == "__main__":
    main()
