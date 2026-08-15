# Vértice Mercados

Plataforma de inteligência de mercado para acompanhar ações brasileiras e norte-americanas, BDRs, índices e moedas. O projeto combina coleta, histórico, métricas de risco e visualização em um dashboard privado.

## Estado atual

- Dashboard publicado no Sites.
- API Python/FastAPI hospedada no Render.
- Histórico persistido em PostgreSQL no Supabase.
- Atualização visual a cada 5 minutos.
- Coleta diária automatizada às 19h30, em dias úteis.
- Ranking de valorização consistente e consulta histórica de 1 dia a 5 anos.
- Indicadores macroeconômicos oficiais do Brasil e dos Estados Unidos.
- Matriz de correlação mensal entre mercado, juros, inflação e câmbio.

## Estrutura

- `app/`: dashboard e rotas intermediárias publicadas no Sites.
- `services/market_api/`: coleta, persistência, métricas e contratos da API.
- `.github/workflows/`: agenda automática de atualização do histórico.
- `docs/ROADMAP.md`: fases, entregas e próximos marcos do produto.
- `services/market_api/tests/`: testes de métricas, banco e coleta.

## Coleta automática

O GitHub Actions chama a rota protegida da API de segunda a sexta-feira. A mesma chave deve ser cadastrada em dois lugares, sem ser incluída no código:

1. Render: variável secreta `SYNC_API_KEY`.
2. GitHub: segredo do repositório `VERTICE_SYNC_API_KEY`.

A tela “Saúde dos dados” apresenta cobertura, quantidade de registros e ativos atrasados, ausentes ou com falha.

## Macroeconomia e correlações

A Fase 2 conecta Selic, CDI, IPCA e IGP-M pelo SGS do Banco Central. Nos Estados Unidos, usa as fontes oficiais do Federal Reserve Bank of New York (Fed Funds), BLS (CPI), U.S. Treasury (Treasury de 10 anos) e Federal Reserve Board (dólar amplo). O serviço preserva as observações originais, normaliza as frequências por mês e calcula correlações usando retornos mensais dos ativos e variações mensais dos indicadores.

Correlação é uma medida histórica de associação e não representa causalidade nem previsão.

## Desenvolvimento local

Requer Node.js 22.13 ou superior e Python 3.11 ou superior.

```powershell
pnpm install
pnpm dev
```

Para executar a API:

```powershell
cd services/market_api
python -m pip install -r requirements.txt
python -m uvicorn vertice_api.main:app --reload --port 8000
```

Use os arquivos `.env.example` como referência. Nunca envie senhas ou chaves para o repositório.

## Validação

```powershell
pnpm test
cd services/market_api
python -m unittest discover -s tests -v
```

## Fonte de dados

O conector inicial usa uma fonte pública não oficial para o protótipo. Antes de uso profissional ou comercial, ele deverá ser substituído por uma fonte estável e licenciada. A arquitetura por provedores permite essa troca sem alterar o dashboard.

## Aviso

O Vértice é uma ferramenta de análise e acompanhamento. As informações e métricas apresentadas não constituem recomendação de investimento.
