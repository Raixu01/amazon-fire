# Pulso | .ATM — Amazônia Legal e região de Altamira

Edição curta de 60 segundos, 1920 × 1080, 30 fps, MP4/H.264, sem narração. A marca original foi fornecida em `pulso.png_20260922115227.jpeg` e permanece sem alteração; seu enquadramento é feito na composição como **Pulso | .atm**. Projeto editável: `remotion/src/atm-video.jsx`.

No primeiro mapa, aparecem os contornos de todos os municípios da Amazônia Legal e a legenda “Focos de Calor na Amazônia — 2026”. Durante a aproximação, esses contornos se apagam; permanecem Altamira e os cinco vizinhos destacados, com a legenda “Primeira quinzena de outubro de 2026 — Região de Altamira-Pará”.

## Recortes e corte temporal

- Amazônia Legal brasileira: 1º de janeiro a 15 de outubro de 2026. Janeiro a setembro são meses completos; outubro é parcial.
- Região: Altamira e os cinco municípios limítrofes com maiores contagens de 1º a 15 de outubro: Uruará, São Félix do Xingu, Placas, Itaituba e Novo Progresso.
- Datas em Brasília (UTC−3). Última observação de qualquer sensor nos arquivos consultados: **15/10/2026 às 18h40**. Última observação nacional do sensor selecionado: **15/10 às 14h52**. Esses horários não garantem completude das passagens nem são o horário de publicação dos arquivos. O dia 15 aparece como parcial.
- Seleção fixa **NOAA-20** nos dois recortes, para não somar sensores com frequências e resoluções diferentes. É uma seleção editorial, **não a série oficial do satélite de referência do INPE**. Mesmo com sensor constante, nuvens, cobertura e horários de aquisição afetam as detecções.

## Fonte e identificação dos arquivos

**INPE / Programa Queimadas — Focos de Queimadas e Incêndios, CSV Brasil.** Página: https://data.inpe.br/queimadas/dados-abertos/.

Mensais: `focos_mensal_br_202601.csv` a `focos_mensal_br_202609.csv`, do diretório https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/mensal/Brasil/.

Diários: `focos_diario_br_20261001.csv` a `focos_diario_br_20261015.csv`, do diretório https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/.

São 24 arquivos consultados diretamente na origem. O nome de cada arquivo, URL, SHA-256, quantidade de linhas, intervalo UTC, data de consulta e Last-Modified estão em `auditoria.json`. Os CSVs originais e metadados estão arquivados localmente em `.cache/atm-2026/`; não são substituídos automaticamente durante a reprodução local. `camadas/focos_amazonia_NOAA20.csv.gz` preserva os registros usados na análise e permite conferir as contagens sem novo download.

## Auditoria realizada

1. Verificação do formato dos 24 CSVs, timestamps e coordenadas; nenhum registro inválido.
2. Remoção de **8 duplicações técnicas** no conjunto Brasil antes do recorte, pela chave horário UTC + latitude + longitude + satélite. Observações legítimas de horários diferentes são preservadas.
3. Conversão UTC → Brasília antes de definir mês e dia, incluindo as três primeiras horas UTC do mês seguinte no mês civil anterior.
4. Conferência dos sensores por mês e presença de NOAA-20 em todos os dias completos do ano até 14/10. A presença de registros nacionais não garante cobertura integral de cada município.
5. Recorte na geometria original da Amazônia Legal e atribuição municipal por coordenadas. Vizinhos definidos pela divisa compartilhada na malha original; não por proximidade visual. Zero pontos com empate nas divisas dos municípios analisados.
6. Reconciliação de totais mensais, diários e municipais; arquivos gráficos diários com 15 hashes distintos. Nenhum registro idêntico entre dias consecutivos. As camadas são substituídas, sem sobreposição temporal, nos trechos mensais e diários.
7. Recontagem independente da edição antiga nos novos downloads: os sete totais de 8–14/10 conferem. Os sete PNGs antigos são distintos. O código anterior mantinha as camadas de dias anteriores em cinza; a persistência visual foi removida nesta edição. As novas contagens não devem ser comparadas diretamente às antigas: mudaram o período, os municípios e o filtro de satélite.

## Resultado regional

| Município | Detecções NOAA-20 |
|---|---:|
| Uruará | 5.850 |
| Altamira | 5.039 |
| São Félix do Xingu | 2.676 |
| Placas | 2.107 |
| Itaituba | 2.105 |
| Novo Progresso | 905 |
| **Total** | **18.682** |

Maior contagem diária conjunta: **10/10, 2.265 detecções**. São contagens absolutas, não taxas ajustadas pela área. O ranking de todos os vizinhos está em `ranking_todos_vizinhos.csv`; as contagens por dia e município estão em `contagens_diarias_municipios.csv`.

## Cartografia e interpretação

Limites: IBGE, **Limites da Amazônia Legal 2024** e **Municípios da Amazônia Legal 2024**, disponíveis em https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/amazonia_legal/2024/. Geometrias completas para análise e simplificadas somente para desenho. Renderização em Web Mercator (EPSG:3857); arquivos de pontos em WGS84 (EPSG:4326).

Fundo: **Esri World Imagery — Esri, Vantor, Earthstar Geographics e GIS User Community**. É um mosaico de datas diversas, não uma fotografia do período. URLs, coordenadas do enquadramento, créditos e hashes estão em `fundo.json` e `mapa.json`. A aproximação é uma animação cartográfica em Remotion; não é filmagem aérea. Não há variável ambiental modelada nesta edição.

Pontos laranja: detecções do mês/dia indicado. Amarelo: Altamira; limites claros: municípios vizinhos. O acumulado aparece apenas na comparação e na síntese. O tamanho dos pontos é gráfico e não representa área queimada. Sobreposição espacial reduz a quantidade de pontos distinguíveis em relação ao contador. Detecções não equivalem a incêndios únicos; ausência de detecções não comprova ausência de fogo.

## Reprodução

```powershell
.venv/Scripts/python.exe scripts/video_atm_auditar.py --download
.venv/Scripts/python.exe scripts/video_atm_fundo.py
cd remotion
npm ci
npm run render:atm:preview
npm run render:atm
```

Para manter exatamente o snapshot, omita `--download`. O manifesto permite detectar mudanças das fontes em novas consultas. Se necessário, acrescente `-- --browser-executable "C:/Program Files/Google/Chrome/Application/chrome.exe"` ao comando npm. A marca e os assets para renderizar offline já estão em `remotion/public/atm/`. A reconstrução dos dados requer as duas malhas ZIP originais do IBGE na raiz do projeto.

O script `scripts/video_atm_verificar.py` confere os dados entregues e decodifica os dois vídeos, verificando duração, tamanho e diferenças entre os mapas diários no MP4 final.

## Validação da entrega

Concluída a decodificação integral dos dois MP4s: 19 e 100 segundos, ambos H.264, 1920 × 1080, 30 fps. Conferidas as contagens contra CSV/GeoJSON e os 15 mapas efetivamente renderizados: todos os pares de dias consecutivos têm distribuições visuais diferentes. Resultados e hashes dos vídeos em `verificacao.json`. O player foi testado em Chromium, com reprodução, avanço até 1min11s e layout de 390 pixels sem rolagem horizontal; resultado em `player-qa.json`.

`camadas-e-auditoria.zip` reúne camadas, tabelas, nota e relatórios. Os MP4s publicados estão em `docs/media/`, e a edição anterior continua acessível no player.
