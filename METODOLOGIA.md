# Metodologia

Este documento explica como os mapas "Um ponto, um voto" são construídos: de onde vêm os números, como cada
voto ganha uma posição no mapa e o que os pontos podem e não podem dizer.

## 1. O que o mapa mostra

Cada ponto é **um voto nominal para Presidente em 2026**, registrado numa seção eleitoral no Brasil. Há
mapas do 1º turno (4 de outubro) e do 2º turno (25 de outubro), cada um em duas versões: por município e por
estado. A cor é a do candidato que recebeu o voto.

**2º turno**

| Cor | Candidato | Votos no mapa | % dos votos no mapa |
|---|---|---:|---:|
| Vermelho | Lula | 64.056.078 | 51,8% |
| Azul | Flávio Bolsonaro | 59.654.544 | 48,2% |
| | **Total** | **123.710.622** | |

**1º turno**

| Cor | Candidato | Votos no mapa | % dos votos no mapa |
|---|---|---:|---:|
| Vermelho | Lula | 53.722.151 | 45,2% |
| Azul | Flávio Bolsonaro | 55.960.603 | 47,0% |
| Verde | Augusto Cury | 3.438.835 | 2,9% |
| Amarelo | Renan Santos | 2.667.307 | 2,2% |
| Cinza | Demais candidatos (8) | 3.186.133 | 2,7% |
| | **Total** | **118.975.029** | |

Os "demais candidatos" são Ronaldo Caiado, Romeu Zema, Samara, Hertz Dias, Clariana Barão, Edmilson Costa,
Wilson Grassi e Rui Costa Pimenta.

**Ficam fora do mapa:**
- votos **brancos e nulos**, que não são votos em candidato;
- os votos do **exterior** (331.005 no 1º turno e 371.651 no 2º), que não têm um lugar no território
  brasileiro onde ser desenhados.

## 2. Fonte dos votos

### 1º turno

Os votos vêm do arquivo de dados abertos do TSE **`votacao_secao_2026_BR`**, que traz uma linha por seção
eleitoral e candidato (gerado em 06/10/2026). Somando todas as seções, inclusive as do exterior, o total por
candidato coincide com a totalização oficial do TSE para Lula, Flávio Bolsonaro, Augusto Cury e Renan Santos.

### 2º turno

Quando os mapas do 2º turno foram feitos, a votação por seção do 2º turno ainda não estava nos dados
abertos do TSE. A fonte são os **arquivos oficiais de divulgação de resultados** (`resultados.tse.jus.br`,
eleição 6258): um arquivo por par município-zona eleitoral, 6.292 no total, todos gerados em 25/10/2026.

O script confere que **todas as zonas estão com totalização final e 100% das seções apuradas** antes de
usar os números. A soma das zonas de cada UF coincide com o arquivo da UF, e a soma de todas coincide com o
total nacional divulgado pelo TSE: 64.256.232 votos para Lula e 59.826.041 para Flávio Bolsonaro, contando
o exterior.

Para os mapas, a zona é um nível intermediário: os votos das zonas são somados por município e por UF, que
é o que os mapas usam. O resultado é o mesmo que se obteria somando as seções.

### Nos dois turnos

No 1º turno, os votos foram agrupados em cinco categorias (as quatro candidaturas destacadas e "outros");
no 2º, em duas (Lula e Flávio Bolsonaro). Depois foram somados por **município** (mapa por município) ou por
**unidade da federação** (mapa por estado). O código de município do TSE foi convertido para o código do IBGE
usando os arquivos de resultado por município do próprio TSE.

## 3. Onde cada voto é desenhado

O voto é secreto, e o TSE só informa **em que seção** ele foi registrado. Não existe a informação de onde o
eleitor mora. Por isso o mapa **sorteia** uma posição para cada voto dentro de uma área conhecida:

- **Mapa por município:** a área é o território inteiro do município onde fica a seção (malha municipal do
  IBGE).
- **Mapa por estado:** a área é o território inteiro da UF onde fica a seção (malha estadual do IBGE).

O sorteio é **uniforme por área**: todo quilômetro quadrado do município (ou do estado) tem a mesma chance de
receber um voto. Assim, a densidade de pontos dentro de cada área é constante, e a mistura de cores reproduz
exatamente a proporção de votos daquela área.

### Passo a passo

1. **Contornos.** As malhas do IBGE (API de malhas v3, qualidade intermediária) são simplificadas, com
   tolerância proporcional ao tamanho de cada município (de ~50 m a ~1 km) e de ~500 m para os estados. As
   coordenadas são arredondadas a 0,0001° (~11 m).
2. **Triangulação.** No navegador, cada contorno é dividido em triângulos (algoritmo *earcut*), respeitando
   ilhas e buracos.
3. **Subdivisão.** Todo triângulo com mais de **1.500 votos esperados** é cortado ao meio pelo lado mais
   longo, até que nenhum passe desse limite. Isso não muda a distribuição; serve para o navegador desenhar só
   os pontos dos triângulos que estão na tela.
4. **Repartição dos votos.** Os votos de cada candidato na área são repartidos entre os triângulos na
   proporção da área de cada um, pelo método dos **maiores restos**: cada triângulo recebe a parte inteira da
   sua cota, e as sobras vão para os triângulos com as maiores frações. O total de cada candidato fecha
   exatamente.
5. **Posição do ponto.** Dentro do triângulo, cada voto recebe uma posição uniforme a partir de dois números
   pseudoaleatórios (coordenadas baricêntricas com raiz quadrada, que não concentram pontos nos vértices).

### O sorteio é fixo

Os números "aleatórios" vêm de uma função de *hash* aplicada ao número do triângulo, ao candidato e ao número
do voto. Por isso **o mesmo voto aparece sempre no mesmo lugar**: ao recarregar a página, ao mudar o zoom e
ao passar de um pedaço do mapa para outro.

## 4. Zoom e escala

Desenhar 119 milhões de pontos de uma vez travaria qualquer navegador. Por isso o mapa desenha uma **fração
dos votos** que cresce com o zoom:

| Zoom | 1 ponto ≈ |
|---:|---:|
| 4 (Brasil inteiro) | 97 votos |
| 6 | 42 votos |
| 8 | 18 votos |
| 10 | 8 votos |
| 12 | 3,5 votos |
| 14 | 1,5 voto |
| 15 ou mais | **1 voto** |

A fração é `2^(-0,6 × (15 − zoom))`. Em cada triângulo, o número de pontos de cada candidato é a fração
aplicada aos seus votos, com arredondamento estocástico (um sorteio fixo decide se a sobra vira mais um
ponto). Assim, na média, **as proporções entre candidatos se mantêm em qualquer zoom**, e um ponto que
aparece num zoom continua no mesmo lugar nos zooms seguintes. O painel mostra a escala atual.

Os pontos são desenhados em blocos de 256 × 256 pixels, só para a área visível, numa ordem embaralhada:
nenhum candidato fica sistematicamente por cima dos outros.

## 5. Como ler o mapa (e como não ler)

- **A posição de um ponto não diz onde o eleitor mora nem onde votou.** Dentro do município (ou do estado),
  ela é sorteada.
- **A cor de uma região reflete o resultado do município ou do estado inteiro.** Bairros diferentes de uma
  mesma cidade aparecem com a mesma mistura de cores.
- **A densidade de pontos é votos por área.** Cidades populosas e pequenas aparecem como manchas densas, e
  municípios grandes e pouco habitados, como os da Amazônia, aparecem ralos. No mapa por estado, a Grande São
  Paulo tem a mesma densidade que o interior paulista.
- **Áreas sem habitantes também recebem pontos.** Represas, parques e áreas de floresta dentro do município
  são tratados como o resto do território.

## 6. Casos particulares

- **Boa Esperança do Norte (MT)**, município instalado recentemente, ainda não está na malha do IBGE. Para
  ele, a área é a envoltória dos seus três locais de votação ampliada em ~13 km, que se sobrepõe em parte a
  Sorriso e Nova Ubiratã.
- **Brasília/DF** é um único "município" na malha do IBGE, e todo o Distrito Federal funciona como uma área.
- A simplificação dos contornos pode deixar pequenas frestas ou sobreposições nas divisas entre municípios,
  da ordem de dezenas de metros. Não afeta a contagem.

## 7. Reprodutibilidade

O código que gera os dados está em `scripts/`. Ele lê os arquivos do TSE, soma os votos, simplifica os
contornos e grava os arquivos de `dados/`: `municipios.js` e `estados.js` para o 1º turno
(`preparar_dados.py` e `preparar_dados_estados.py`) e `municipios-2t.js` e `estados-2t.js` para o 2º
(`preparar_dados_2t.py`). Os dois turnos usam os mesmos contornos e o mesmo código de geometria.

A triangulação, a subdivisão, a repartição e o sorteio dos pontos acontecem no navegador
(`mapa-*.html`), de forma determinística: qualquer pessoa que abra o mapa vê exatamente os mesmos pontos.
Os pontos de um turno não correspondem aos do outro: o mesmo eleitor não está no mesmo lugar nos dois mapas.
