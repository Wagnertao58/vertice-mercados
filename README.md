# V?rtice Mercados

Dashboard privado para acompanhar a??es brasileiras e norte-americanas, BDRs,
?ndices e moedas. A primeira fase re?ne pre?os di?rios, m?tricas de retorno e
risco e compara??es de paridade entre a??es no exterior e seus BDRs na B3.

## Estrutura

- `app/`: dashboard publicado no Sites.
- `app/api/market/`: liga??o segura entre o dashboard e a API de mercado.
- `services/market_api/`: servi?o Python/FastAPI de coleta, persist?ncia e an?lise.
- `services/market_api/tests/`: testes das m?tricas e do armazenamento.

## Dashboard

Requer Node.js 22.13 ou superior.

```powershell
pnpm install
pnpm dev
```

Para conectar o dashboard ? API, configure:

```text
MARKET_API_URL=http://localhost:8000
```

## API de mercado

```powershell
cd services/market_api
python -m pip install -r requirements.txt
python -m uvicorn vertice_api.main:app --reload --port 8000
```

A documenta??o interativa fica em `http://localhost:8000/docs`.

## Valida??o

```powershell
pnpm test
cd services/market_api
python -m unittest discover -s tests -v
```

## Fonte de dados

O conector inicial usa uma fonte p?blica n?o oficial exclusivamente para o
prot?tipo. Antes de uso em produ??o, ele dever? ser substitu?do por uma fonte
est?vel e licenciada. A separa??o por provedores permite essa troca sem alterar
o dashboard ou os contratos da API.

## Aviso

O V?rtice ? uma ferramenta de an?lise e acompanhamento. As informa??es e
m?tricas apresentadas n?o constituem recomenda??o de investimento.
