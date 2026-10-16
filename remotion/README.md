# Altamira em Remotion

## Nova edição Pulso | .ATM

`npm run render:atm:curto` produz a edição principal de **90 segundos**, com a evolução mensal de janeiro a outubro nos municípios da Amazônia Legal, aproximação para Altamira e análise diária dos quinze dias. O render usa uma única instância do navegador para limitar memória e GPU. `npm run render:atm` preserva a edição de 100 segundos; `npm run render:atm:preview` produz a prévia de 19 segundos. Todas usam a logo fornecida e os assets offline em `public/atm/`.

Composição: `src/atm-video.jsx`; dados auditados: `src/atm-dados.json`. Fontes, filtro NOAA-20, corte parcial e reprodução dos dados estão na [nota técnica](../entregas/atm-2026/LEIA-ME.md). A edição anterior permanece disponível abaixo.

Composição editável do vídeo de 8–14/10/2026. O enquadramento e o relevo foram capturados com CesiumJS; Remotion compõe os pontos, textos, gráficos, créditos e as cenas. As duas composições têm 1920 × 1080 pixels, 30 fps e nenhuma faixa de áudio.

## Renderizar

Instale Node.js e, nesta pasta:

```powershell
npm ci
npm run studio
npm run render
npm run render:test
```

Os comandos `render` e `render:test` gravam os MP4s em `../entregas/altamira/`. Em uma máquina sem navegador Chromium detectável, acrescente `-- --browser-executable "C:/caminho/para/chrome.exe"` ao comando npm.

`src/video.jsx` define o roteiro e os textos; `src/dados.json` contém contagens e percentuais auditados. `public/` contém o sobrevoo sem textos, o mosaico de fundo e as camadas transparentes dos focos, de forma que o projeto possa ser aberto e renderizado após clonar o repositório. `scripts/preparar_remotion.py` regenera esses assets a partir de `cena.json`, `projecao.json`, `paisagem.png` e 48 quadros Cesium locais. Para refazer essas entradas, consulte `../entregas/altamira/LEIA-ME.md` e os scripts `video_altamira_dados.py` e `video_altamira_render.py`.

O fundo Esri é um mosaico de datas diversas. Os focos são observações do período, enquanto o risco de fogo é modelado e aparece somente nos locais das detecções. As imagens recentes MODIS/VIIRS avaliadas tinham nuvens e lacunas extensas; por isso, a cena de 44–52 s detalha a distribuição dos focos. Créditos completos e limitações constam da nota da entrega.
