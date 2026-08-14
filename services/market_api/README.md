# Vértice Market API

Serviço Python da camada operacional do Vértice. Ele mantém o catálogo de
ações, BDRs, índices, ETFs e moedas; coleta histórico diário; persiste preços;
calcula métricas de risco; e expõe a API consumida pelo dashboard.

## Supabase PostgreSQL

Em produção, defina `DATABASE_URL` com a URI do **Session pooler** copiada do
Supabase. A conexão usa a porta `5432` e deve preservar os parâmetros de
segurança fornecidos pelo painel. Se a URI exibir `[YOUR-PASSWORD]`, substitua
esse trecho pela senha do banco antes de cadastrá-la no Render.

A URI real deve permanecer somente nos segredos do provedor. Nunca salve a
senha, a URI completa ou qualquer chave do Supabase no GitHub.

Na primeira inicialização, a API cria as tabelas e os índices necessários e
registra o catálogo de ativos. O endpoint `/health` confirma a conexão e informa
se o backend ativo é `sqlite` ou `postgresql`.

## Execução local

O modo local usa SQLite automaticamente quando `DATABASE_URL` estiver vazio.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn vertice_api.main:app --reload --port 8000
```

A documentação interativa fica em `http://localhost:8000/docs`.

## Render

O arquivo `render.yaml` da raiz prepara o serviço web gratuito, configura o
health check e solicita o valor secreto de `DATABASE_URL` durante a criação. O
painel continua separado e recebe apenas a URL pública da API.

## Fonte de desenvolvimento

O conector inicial usa um endpoint público não oficial do Yahoo Chart para
validação sem credenciais. Ele não deve ser a fonte final de produção. A
interface do provedor está isolada para permitir a troca por um feed licenciado
sem alterar o banco, a API ou o dashboard.
