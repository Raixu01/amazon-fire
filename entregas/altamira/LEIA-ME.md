# Altamira — focos de fogo ativo

Primeira edição sem narração: 60 segundos, 1920 × 1080, 30 fps, MP4/H.264, sem faixa de áudio. O arquivo `teste_altamira_2026-10-14.mp4` tem 6 segundos e mostra somente as detecções do dia 14. A sequência completa está em `altamira_2026-10-08_a_14_fullhd.mp4`.

## Período e método

8 a 14 de outubro de 2026, dias civis completos em Brasília (UTC−3). Intervalo UTC usado: 08/10 às 03h inclusive até 15/10 às 03h exclusive. Os oito CSVs diários oficiais foram consultados em 15/10/2026. O arquivo de 15/10, ainda parcial, foi usado exclusivamente para fechar as três últimas horas UTC necessárias ao dia 14 de Brasília.

Recorte espacial de Altamira (IBGE 1500602), pela geometria original da malha Amazônia Legal 2024. A simplificação é usada somente na visualização. Os municípios próximos ao limite aparecem como contexto. A conferência com a malha original corrigiu a classificação de 29 registros próximos às divisas (5 incluídos e 24 excluídos em relação ao recorte simplificado preliminar). Os dados originais baixados, hashes SHA-256 e metadados HTTP permitem reproduzir a seleção. A ausência de arquivo não foi tratada como zero: os oito arquivos necessários estavam disponíveis. Isso não comprova completude das aquisições de cada sensor.

Foram encontradas **11.922 detecções**. Deduplicação por horário UTC, latitude, longitude e satélite: nenhuma duplicata nessa chave no recorte. Detecções em horários ou sensores distintos são preservadas, inclusive quando correspondem à mesma área de fogo. Os registros não representam 11.922 incêndios independentes.

| Dia, Brasília | Detecções |
|---|---:|
| 08/10 | 3.034 |
| 09/10 | 2.418 |
| 10/10 | 1.795 |
| 11/10 | 1.050 |
| 12/10 | 730 |
| 13/10 | 1.110 |
| 14/10 | 1.785 |

## Ambiente e interpretação visual

Cobertura nos registros selecionados: precipitação e dias sem chuva, 99,44%; risco de fogo, 99,21%; FRP, 96,38%. Valores ausentes ou negativos foram considerados indisponíveis. A variável escolhida é **risco de fogo**, índice modelado pelo INPE, exibido nos locais das detecções, na escala numérica 0–1. Não foi interpolado um campo ambiental para todo o município. Sobreposição de pontos e passagens repetidas impedem interpretar a área colorida como área queimada. Valores modelados não são uma previsão feita por este vídeo.

Na evolução diária, coral indica detecções do dia exibido e azul acinzentado indica dias anteriores. A atenuação é somente um recurso visual; não informa extinção do fogo. Contadores incluem os registros sobrepostos. Não se deduz ausência de fogo a partir da ausência de detecções.

## Imagem de fundo e observações recentes

O Earth Studio redirecionou para autenticação; não foi possível validar uma sessão utilizável pela conexão de navegador disponível. Foi adotada a alternativa CesiumJS 1.127, com Esri World Elevation e Esri World Imagery. **O fundo é um mosaico de datas diversas, não uma imagem da semana analisada.** A aproximação usa 48 quadros de câmera com terreno carregado, interpolados visualmente para a saída a 30 fps.

Foram baixadas e inspecionadas imagens NASA GIBS em cores naturais: MODIS Terra de 14/10 e VIIRS NOAA-20 de 08, 11 e 14/10. O MODIS apresenta uma extensa faixa sem dados; as três imagens VIIRS apresentam ampla nebulosidade. Não foi feita uma classificação quantitativa de nuvens ou fumaça, nem uma busca exaustiva de todas as passagens. Essas imagens não foram usadas como paisagem do vídeo. Conforme a alternativa prevista no roteiro, os segundos 44–52 detalham a distribuição das detecções. A data diária dos produtos GIBS é a data UTC do produto, não um horário de aquisição convertido para Brasília.

## Roteiro

0–8 s: aproximação regional até Altamira; 8–32 s: sete dias de focos; 32–44 s: risco modelado nos focos; 44–52 s: distribuição espacial; 52–60 s: síntese e fontes.

## Fontes e créditos

- Focos e campos ambientais: [INPE / Programa Queimadas — arquivos diários](https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/Brasil/) e [dados abertos](https://data.inpe.br/queimadas/dados-abertos/).
- Limites: [IBGE — Amazônia Legal 2024](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/amazonia_legal/2024/).
- Fundo: [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer). Crédito retornado pelo serviço: Esri, Vantor, Earthstar Geographics e GIS User Community.
- Relevo: [Esri World Elevation / Terrain3D](https://elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer).
- Visualização: [CesiumJS](https://cesium.com/platform/cesiumjs/).
- Imagens recentes avaliadas: [NASA GIBS](https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi), camadas `MODIS_Terra_CorrectedReflectance_TrueColor` e `VIIRS_NOAA20_CorrectedReflectance_TrueColor`. Recorte WGS84: oeste −57°, sul −11°, leste −49°, norte −1°.

## Arquivos e reprodução

`camadas/` contém os GeoJSON diários, o conjunto do período, limites, CSV com os atributos e KML do teste. `auditoria.json` contém contagens, cobertura e proveniência. `fontes_inpe_2026-10-08_a_15.zip` preserva os oito CSVs oficiais baixados. Os scripts `scripts/video_altamira_dados.py`, `scripts/video_altamira_render.py` e `scripts/video_altamira_montar.py` reproduzem, respectivamente, dados, cena e codificação. Instale `requirements-video.txt` além do Chrome ou outro Chromium e execute o script de dados com `--local` para usar o ZIP arquivado. Os scripts usam o período fixado nesta edição; uma nova semana exige atualizar as datas e os textos.
