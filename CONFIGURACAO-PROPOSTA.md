# Configuração de execução proposta para o Pulso

Esta proposta mantém a aplicação estática e o processamento Python existentes, acrescentando **Observable Plot para gráficos e Scrollama para a narrativa guiada**. O Leaflet continua responsável pelo mapa.

**Status:** implementada localmente em 15/10/2026. Calendário Observable Plot, faixa histórica P25–P75, narrativa Scrollama e seleção municipal por código IBGE integrados em `docs/`. Publicação externa não executada.

## Componentes da execução

| Camada | Ferramenta | Responsabilidade |
|---|---|---|
| Processamento | Python + pandas/GeoPandas | Validar, agregar e preparar os dados |
| Dados publicados | JSON e JSON compactado | Fornecer séries históricas, registros recentes e limites municipais |
| Interface | HTML, CSS e JavaScript | Navegação, filtros e páginas municipais |
| Mapa | Leaflet existente | Exibir municípios e observações |
| Gráficos | `@observablehq/plot` | Calendário mensal e comparações históricas |
| Narrativa | `scrollama` | Atualizar visualizações conforme a leitura |
| Hospedagem | GitHub Pages | Publicar a aplicação estática |
| Atualização | GitHub Actions existente | Executar coleta, validação e publicação |

## Organização sugerida dos arquivos

```text
amazon-fire/
├── scripts/                      # Processamento Python existente
├── tests/
└── docs/
    ├── index.html                # Entrada e narrativa
    ├── styles.css                # Layout responsivo
    ├── app.js                    # Inicialização e navegação
    ├── model.js                  # Regras e filtros existentes
    ├── components/
    │   ├── calendario.js         # Meses × anos
    │   ├── comparacao.js         # Curva e faixa histórica
    │   ├── municipio.js          # Visão do município
    │   └── narrativa.js          # Etapas do Scrollama
    ├── vendor/                   # Bibliotecas com versões fixadas
    └── data/                     # Dados publicados existentes
```

Recomenda-se distribuir as bibliotecas em `vendor/`, com versões fixadas, para reduzir a dependência de servidores externos durante o carregamento. Node.js não precisa participar da execução pública; pode ser usado apenas na preparação das dependências e nos testes JavaScript.

## Configuração inicial da experiência

| Recurso | Configuração proposta |
|---|---|
| Tela inicial | Resumo recente, identificação do período e busca municipal |
| Calendário | Histórico mensal, anos nas linhas e meses nas colunas |
| Comparação histórica | Ano completo mais recente validado; comparação entre meses equivalentes |
| Faixa histórica | Intervalo entre percentis 25 e 75, acompanhado da mediana e de explicação |
| Referência estatística | Anos completos válidos; excluir o ano selecionado da referência |
| Município | Seleção pela busca, mapa ou ranking; endereço compartilhável com código IBGE |
| Escalas | Mesmos limites de cor nos períodos comparados |
| Dados ausentes | Identificação própria, diferente de zero |
| Animações | Opcionais, com pausa e respeito à preferência por movimento reduzido |
| Celular | Conteúdo em uma coluna, gráficos adaptados e mapa carregado sob demanda |
| Alternativa acessível | Resumo textual e tabela junto de cada gráfico |

A comparação histórica usará exclusivamente a série de referência. O monitoramento recente continuará separado, pois reúne observações de diferentes satélites.

## Execução local

Com o ambiente virtual e os insumos já preparados, os comandos existentes continuam válidos. Execute-os na pasta do projeto:

```powershell
.venv/Scripts/python.exe scripts/publicar_historico.py
.venv/Scripts/python.exe scripts/atualizar_focos_recentes.py
.venv/Scripts/python.exe -m http.server 8765 --directory docs
```

Acesse a interface em [http://localhost:8765](http://localhost:8765).

O servidor Python é necessário apenas para servir os arquivos durante o desenvolvimento. Em produção, o GitHub Pages assume essa função.

## Ordem de implementação e validação

1. **Calendário e município:** reutilizar os agregados publicados, adicionar seleção de períodos e resumo local.
2. **Comparação histórica:** calcular mediana e percentis, explicitar a referência e validar lacunas e períodos incompletos.
3. **Narrativa guiada:** conectar textos e visualizações, com leitura completa mesmo sem animação.
4. **Validação final:** conferir consistência dos números, teclado, celular, carregamento e escalas comparáveis.

Os testes existentes permanecem como base:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
node --test tests/*.test.cjs
node --check docs/app.js
```

Serão acrescentados testes para os cálculos históricos e a seleção municipal. MapLibre, deck.gl e hexágonos ficam para uma segunda etapa, sem aumentar a complexidade desta primeira entrega.
