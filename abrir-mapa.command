#!/bin/zsh
# Abre o mapa num servidor local (o OpenStreetMap recusa tiles pedidos de file://)
cd "$(dirname "$0")"
( sleep 1; open "http://localhost:8765/" ) &
python3 -m http.server 8765
