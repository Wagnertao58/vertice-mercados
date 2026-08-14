# V?rtice Market API

Servi?o Python da camada operacional do V?rtice. Ele mant?m o cat?logo de
a??es, BDRs, ?ndices, ETFs e moedas; coleta hist?rico di?rio; persiste pre?os;
calcula m?tricas de risco; e exp?e a API consumida pelo dashboard.

## Execu??o local

O modo local usa SQLite automaticamente quando `DATABASE_URL` estiver vazio.

```powershell
python -m pip install -r requirements.txt
python -m uvicorn vertice_api.main:app --reload --port 8000
```

A documenta??o interativa fica em `http://localhost:8000/docs`.

## Modo gratuito da Fase 1

A API funciona sem banco externo. Quando `DATABASE_URL` não for definida, ela
usa SQLite e cria automaticamente as tabelas, os índices e o catálogo de ativos.
O endpoint `/health` informa se o backend ativo é `sqlite` ou `postgresql`.

No serviço gratuito do Render, o arquivo SQLite é temporário. O cache pode ser
reconstruído após uma reinicialização ou nova implantação. Isso é aceitável
para validar a Fase 1, mas não é o armazenamento histórico definitivo.

## PostgreSQL opcional

Quando precisarmos preservar séries históricas, carteiras e resultados de
modelos, basta definir `DATABASE_URL` com a conexão segura de qualquer
PostgreSQL compatível. A URL deve permanecer nos segredos do provedor e nunca
deve ser salva no GitHub.

## Render

O arquivo `render.yaml` da raiz prepara o serviço web gratuito e seu health
check. Nesta fase ele não exige banco externo. O painel continua separado e
recebe apenas a URL pública da API.

## Fonte de desenvolvimento

O conector inicial usa um endpoint p?blico n?o oficial do Yahoo Chart para
valida??o sem credenciais. Ele n?o deve ser a fonte final de produ??o. A
interface do provedor est? isolada para permitir a troca por um feed licenciado
sem alterar o banco, a API ou o dashboard.
