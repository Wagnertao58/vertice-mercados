# Roteiro do projeto Vértice

Este documento mantém a evolução do Vértice independente de qualquer conversa ou ferramenta de desenvolvimento.

## Fase 1 — Fundação de mercado

### Concluído

- Infraestrutura com GitHub, Render, Supabase e Sites.
- Catálogo de ações dos EUA e Brasil, BDRs, moedas e índices.
- Histórico diário persistido e consulta de 1 dia a 5 anos.
- Métricas de retorno, volatilidade, beta e drawdown.
- Ranking relativo de valorização com menor variância.
- Paridade teórica de BDRs.
- Coleta automática em dias úteis.
- Registro de sucesso e falha por ativo.
- Monitor de cobertura e saúde dos dados.

## Fase 2 — Macroeconomia e correlações

### Primeiro bloco implementado

- Brasil: Selic, CDI, IPCA e IGP-M por séries oficiais do Banco Central.
- Estados Unidos: Fed Funds, CPI, Treasury de 10 anos e índice amplo do dólar via FRED.
- Calendário mensal e normalização de frequências diárias e mensais.
- Matriz de correlação entre ações, moedas, índices e indicadores.

### Próximo bloco

- Curva de juros brasileira com fonte estável e documentada.
- Correlação móvel e análise de defasagens.

## Fase 3 — Pesquisa quantitativa

- Comparador de ativos e carteiras.
- Retorno ajustado ao risco e decomposição de exposição.
- Backtesting com custos e períodos fora da amostra.
- Alertas de mudança de regime e anomalias.

## Fase 4 — Predições

- Modelos-base transparentes antes de modelos complexos.
- Separação rigorosa entre treino, validação e teste.
- Comparação contra benchmarks ingênuos.
- Intervalos de incerteza e acompanhamento de erro.
- Nenhuma previsão será apresentada como recomendação de investimento.

## Critério de avanço

Cada fase só avança quando os dados necessários estão contínuos, documentados e monitorados, e quando os cálculos têm testes reproduzíveis.
