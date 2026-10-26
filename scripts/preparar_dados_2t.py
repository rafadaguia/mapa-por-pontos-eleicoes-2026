"""Gera os dados do 2º turno (Presidente, 25/10/2026) para os mapas por município e por estado.

O TSE ainda não publicou a votação por seção do 2º turno nos dados abertos. Por isso a fonte são os
arquivos oficiais de divulgação de resultados (resultados.tse.jus.br, eleição 6258), um JSON por par
município-zona, baixados por "analise final/a01_baixar_2t.py" no projeto "analise-2t - por bairro".
Somando as zonas chega-se ao total exato de cada município; o script confere que todas as zonas têm
totalização final e 100% das seções apuradas.

Saídas: dados/municipios-2t.js e dados/estados-2t.js, no mesmo formato dos arquivos do 1º turno,
com duas categorias: Lula e Flávio.
"""
import collections, glob, gzip, json, re

import pandas as pd

from preparar_dados import RAIZ, REPO, gravar_municipios
from preparar_dados_estados import gravar_estados

ZONAS = RAIZ / "analise-2t - por bairro" / "analise final" / "dados" / "2t_divulgacao" / "zona"
CATS = ["lula", "flavio"]
NUM = {"13": "lula", "22": "flavio"}


def ler_votos_2t():
    votos = collections.defaultdict(collections.Counter)
    arquivos = sorted(glob.glob(str(ZONAS / "*" / "*.json.gz")))
    for f in arquivos:
        d = json.load(gzip.open(f))
        assert d["ele"] == "6258" and d["t"] == "2", f
        assert d["tf"] == "s" and d["s"]["st"] == d["s"]["ts"], f"zona sem totalização final: {f}"
        cd_tse = int(re.search(r"/[a-z]{2}(\d{5})-z\d{4}\.json\.gz$", f).group(1))
        for c in d["carg"]:
            for a in c["agr"]:
                for p in a["par"]:
                    for k in p["cand"]:
                        votos[cd_tse][NUM[k["n"]]] += int(k["vap"])
    print("arquivos de zona:", len(arquivos))
    return pd.DataFrame.from_dict(votos, orient="index")[CATS].fillna(0).astype(int).sort_index()


def main():
    votos = ler_votos_2t()
    print("votos nominais:", votos.sum().to_dict(), int(votos.to_numpy().sum()))
    gravar_municipios(votos, CATS, REPO / "dados" / "municipios-2t.js")
    gravar_estados(votos, CATS, REPO / "dados" / "estados-2t.js")


if __name__ == "__main__":
    main()
