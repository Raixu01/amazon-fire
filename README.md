# Pulso — focos na Amazônia Legal

## Pulso | .atm — edição curta de 2026

[Assistir ao vídeo de 90 segundos](https://raixu01.github.io/amazon-fire/video.html), com a marca Pulso | .atm, evolução dos dez meses de 2026 nos municípios da Amazônia Legal e análise diária da região de Altamira em 1–15/10/2026. [Nota técnica e auditoria](entregas/atm-2026/LEIA-ME.md). Sensor fixo NOAA-20; dia 15 parcial, corte às 18h40 de Brasília. A edição substitui as camadas a cada dia, sem acúmulo temporal.

## Vídeo Altamira (8–14 de outubro de 2026)

[Vídeo final em MP4 Full HD](entregas/altamira/altamira_2026-10-08_a_14_fullhd.mp4), [teste de um dia](entregas/altamira/teste_altamira_2026-10-14.mp4) e [camadas geográficas com nota metodológica](entregas/altamira/camadas_e_notas.zip). A [nota completa](entregas/altamira/LEIA-ME.md) registra fontes, fuso, recorte e limitações. Para reproduzir esta edição sem novos downloads, instale `requirements-video.txt` e execute `python scripts/video_altamira_dados.py --local`; para reconstruir a cena são necessários CesiumJS, serviços de imagem/relevo e um Chromium instalado.

A [edição em Remotion](entregas/altamira/altamira_2026-10-08_a_14_remotion.mp4) tem a mesma janela e os mesmos dados, com cenas e textos editáveis em [`remotion/`](remotion/README.md). Há também um [teste Remotion de um dia](entregas/altamira/teste_altamira_remotion.mp4).

Para assistir no navegador, abra o [player publicado no GitHub Pages](https://raixu01.github.io/amazon-fire/video.html). A página também oferece download direto do MP4.

Aplicação estática em `docs/`, com Leaflet e processamento Python. A abertura mostra os últimos 7 dias. O histórico de referência é independente dos dados operacionais recentes.

## Executar localmente

```powershell
uv --cache-dir .cache/uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe scripts/publicar_historico.py
.venv/Scripts/python.exe scripts/atualizar_focos_recentes.py
.venv/Scripts/python.exe -m http.server 8765 --directory docs
```

Abra http://localhost:8765. Se o ambiente virtual não existir, crie-o com `python -m venv .venv`. Os comandos de geração usam a malha já preparada em `dados-processados/territorio` e as partições históricas existentes. Para reconstruir os insumos, execute primeiro `scripts/preparar_territorio.py` e `scripts/processar_historico.py`.

`--local` na atualização recente permite usar os CSVs existentes sem acesso à internet. Esse modo não declara uma consulta online bem-sucedida.

## Interface e interpretação

- **Últimos dias:** 24 horas, 3, 7 ou 30 dias corridos a partir de agora; filtros de estado e nome de município; pontos agrupados por proximidade na tela ou totais municipais; gráfico diário e ranking. Agrupamento no viewport evita criar um marcador DOM por observação.
- **Histórico:** último ano completo validado por padrão; filtro mensal real; mapa de total, densidade, variação anual ou diferença da média; evolução mensal do ano e comparação do mesmo mês entre anos; animação iniciar/pausar.
- Cada área preserva os próprios filtros. A busca aceita nomes com ou sem acentos. O ranking também seleciona e aproxima municípios. Há tabela alternativa ao gráfico e navegação por teclado.
- Os dias e horários do monitoramento são exibidos em Brasília; a série histórica mantém os meses/anos UTC dos arquivos de referência. Um foco não equivale a um incêndio nem a uma área queimada. Séries de satélite de referência e de múltiplos satélites não são diretamente comparáveis.
- O dia atual é parcial. Arquivos ausentes são lacunas, não dias com zero focos. A consulta é sinalizada como atrasada após 60 minutos sem sucesso. A última consulta e a observação mais recente são informações distintas.

## Dados publicados

- `docs/data/historico.json`: metadados, anos completos, anos da média 2003–2025, colunas e caminho da série compactada. As linhas anuais são `[codigo_ibge, ano, focos]`; mensais são `[codigo_ibge, ano, mes, focos]`. Apenas `focos.parquet` da série de referência entra neste produto; `focos_recentes.parquet` não participa.
- `docs/data/recentes.json`: datas de geração/tentativa/última consulta bem-sucedida, observação mais recente, cobertura por dia UTC e caminhos das partições compactadas. Cada observação é `[data_hora_utc, latitude, longitude, satelite, municipio_ibge]`.
- Partições são imutáveis, identificadas por hash; o manifesto é substituído atomicamente após validação. Uma falha de coleta preserva a última versão publicada e atualiza o diagnóstico. Blobs anteriores são mantidos para abas já abertas.
- Atualização recente consulta `diario/Brasil/` e `10min/` no servidor oficial INPE. Usa requisições condicionais ETag/Last-Modified, repetição limitada e cache de espacialização por conteúdo e versão da malha. Deduplicação usa instante, coordenadas e satélite, pois o catálogo de 10 minutos não fornece identificador.
- A interface consulta o manifesto a cada 5 minutos enquanto visível, sem alterar filtros ou enquadramento do mapa. Datas UTC das partições são convertidas para os dias de Brasília no gráfico.

## Automação de referência / GitHub Pages

O arquivo `workflow-exemplos/atualizar-focos.yml` documenta o agendamento previsto nos minutos 17, 37 e 57. Ele coleta fontes, registra dados/diagnósticos e pode publicar `docs/` no GitHub Pages, inclusive o aviso quando há falha de atualização. O cache operacional não entra no Git. A publicação inicial deste repositório usa Pages a partir de `main/docs`; o agendamento ainda não está ativo. Para ativá-lo, mova o arquivo para `.github/workflows/` com uma autenticação que tenha permissão `workflow`, configure Pages para GitHub Actions e habilite o ambiente `github-pages`.

Quando ativado, o workflow declara as permissões necessárias. A execução pode atrasar conforme o agendador do GitHub; não há garantia de transmissão instantânea.

## Testes

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
node --test tests/*.test.cjs
node --check docs/app.js
```

Os testes verificam filtros mensais, janelas móveis, virada de mês/ano, dias ausentes, horário de Brasília, deduplicação entre fontes, validação de downloads, requisições condicionais, preservação do cache e isolamento dos agregados históricos.

## Experiência da proposta — outubro de 2026

A aba Histórico inclui calendário mensal com escala comum, tabela para selecionar meses e curva anual com mediana e faixa P25–P75. A referência exclui o ano selecionado e anos com lacunas no território filtrado. As tabelas permanecem disponíveis sem as bibliotecas de gráficos. A narrativa Scrollama destaca as visualizações durante a leitura e pode ser pausada; movimento reduzido desativa sua condução automática.

Escolha uma sugestão na busca, um município no mapa ou no ranking para abrir o recorte municipal. O parâmetro `?municipio=1506807` permite compartilhar o município. Use “Voltar ao território completo” para sair. Em telas de até 850 px, o mapa é inicializado apenas ao pressionar “Carregar mapa”. As bibliotecas são locais; somente os tiles do OpenStreetMap exigem conexão externa durante a navegação.

Dependências fixadas em `docs/vendor/`: D3 7.9.0, Observable Plot 0.6.17, Scrollama 3.2.0, Leaflet 1.9.4 e pako 2.1.0. Referências de implementação: https://observablehq.github.io/plot/features/marks e https://github.com/russellsamora/scrollama.
