# Um ponto, um voto · Eleições 2026

Mapas interativos dos votos para **Presidente no 1º turno de 2026** (4 de outubro), em que cada voto
nominal é um ponto colorido sobre o mapa do Brasil (OpenStreetMap).

| Cor | Candidato |
|---|---|
| 🔴 Vermelho | Lula |
| 🔵 Azul | Flávio Bolsonaro |
| 🟢 Verde | Augusto Cury |
| 🟡 Amarelo | Renan Santos |
| ⚪ Cinza | Demais candidatos |

> Produção independente e exclusiva da [Estel Tecnologia](https://estel.tec.br). Esta ferramenta não tem
> relação com a campanha oficial de Lula, com o PT ou com qualquer partido, federação, coligação ou
> candidatura, e não foi encomendada nem paga por eles.

## Os mapas

- **Página inicial:** https://rafadaguia.github.io/mapa-por-pontos-eleicoes-2026/
- **Por município:** https://rafadaguia.github.io/mapa-por-pontos-eleicoes-2026/mapa-municipios.html
  Cada voto é sorteado em qualquer ponto do município onde foi registrado.
- **Por estado:** https://rafadaguia.github.io/mapa-por-pontos-eleicoes-2026/mapa-estados.html
  Cada voto é sorteado em qualquer ponto do estado onde foi registrado.

Com o Brasil inteiro na tela, cada ponto vale cerca de 100 votos. Os pontos vão sendo acrescentados conforme
o zoom aumenta e, a partir do zoom 15, cada ponto é exatamente um voto. Clique no mapa para ver o resultado do
município ou do estado. Os detalhes estão em [METODOLOGIA.md](METODOLOGIA.md).

## Como embutir em qualquer site

Cole um dos códigos abaixo no HTML da página (no WordPress, use um bloco "HTML personalizado").

**Mapa por município**

```html
<iframe src="https://rafadaguia.github.io/mapa-por-pontos-eleicoes-2026/mapa-municipios.html"
  title="Um ponto, um voto: presidente 2026 por município"
  style="width:100%;height:min(80vh,720px);border:0" loading="lazy" allowfullscreen></iframe>
```

**Mapa por estado**

```html
<iframe src="https://rafadaguia.github.io/mapa-por-pontos-eleicoes-2026/mapa-estados.html"
  title="Um ponto, um voto: presidente 2026 por estado"
  style="width:100%;height:min(80vh,720px);border:0" loading="lazy" allowfullscreen></iframe>
```

No celular e no tablet, um dedo rola a página e o mapa só se move e aproxima com **dois dedos**; ao arrastar
com um dedo, aparece o aviso "Use dois dedos para mover o mapa". Um toque simples continua mostrando o
resultado do lugar. No computador, dentro de um iframe, a roda do mouse só passa a dar zoom depois que o
leitor clica no mapa. Assim o mapa não atrapalha a leitura da página. Em espaços com menos de 560 px de altura ou 600 px de largura, o painel de legenda começa
fechado e abre com um toque no título.

**Atenção ao tráfego.** O mapa de fundo vem dos servidores públicos do OpenStreetMap, que têm uma
[política de uso](https://operations.osmfoundation.org/policies/tiles/) para tráfego alto. Se o mapa for
embutido num site de grande audiência, troque a URL dos tiles em `mapa-*.html` (procure por
`tile.openstreetmap.org`) por um provedor comercial de tiles OSM.

## Estrutura

```
index.html               página inicial com links e códigos de embed
mapa-municipios.html     mapa por município
mapa-estados.html        mapa por estado
dados/municipios.js      contornos simplificados + votos de 5.571 municípios (2,2 MB)
dados/estados.js         contornos simplificados + votos das 27 UFs (60 KB)
assets/estel-logo.png    logo da Estel Tecnologia
fontes/                  malhas do IBGE usadas (API de malhas v3)
scripts/                 scripts Python que geram os arquivos de dados/
METODOLOGIA.md           como os mapas são feitos
```

O site é estático: não há etapa de build. Para ver localmente, sirva a pasta por HTTP (o OpenStreetMap recusa
tiles pedidos de `file://`):

```bash
python3 -m http.server 8765
# abra http://localhost:8765/
```

No macOS, `abrir-mapa.command` faz isso com dois cliques.

## Refazer os dados

Os scripts leem os arquivos brutos do TSE, que não estão no repositório por causa do tamanho
(`votacao_secao_2026_BR.zip` tem 160 MB). Eles esperam a estrutura de pastas do projeto de origem, ao lado
deste repositório; ajuste as constantes no topo de `scripts/preparar_dados.py` se estiverem em outro lugar.

```bash
pip install numpy pandas pyarrow shapely
python scripts/preparar_dados.py           # gera dados/municipios.js
python scripts/preparar_dados_estados.py   # gera dados/estados.js
```

## Fontes

- **Votos:** TSE, dados abertos, `votacao_secao_2026_BR` (votação por seção eleitoral, gerado em 06/10/2026).
- **Código TSE → IBGE e nomes dos municípios:** arquivos de resultado por município do TSE (eleição 6257).
- **Contornos:** IBGE, API de malhas v3, qualidade intermediária (municípios e UFs).
- **Locais de votação** (só para Boa Esperança do Norte/MT, ainda fora da malha do IBGE): TSE, `eleitorado_local_votacao_2026`.
- **Mapa base:** © colaboradores do OpenStreetMap.
- **Bibliotecas:** Leaflet 1.9.4 e earcut 2.2.4, carregados de CDN.
