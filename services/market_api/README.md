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

## Neon PostgreSQL

Em produ??o, defina `DATABASE_URL` com a conex?o direta copiada do bot?o
**Connect** do projeto Neon. A conex?o deve manter `sslmode=require`. Nunca
salve a URL real em arquivos versionados ou no GitHub.

Na primeira inicializa??o, a API cria as tabelas e ?ndices necess?rios e
registra o cat?logo de ativos. O endpoint `/health` confirma a conex?o e informa
se o backend ativo ? `sqlite` ou `postgresql`.

## Render

O arquivo `render.yaml` da raiz prepara o servi?o web, o health check e solicita
o valor secreto de `DATABASE_URL` durante a cria??o. O painel continua separado
e recebe apenas a URL p?blica da API.

## Fonte de desenvolvimento

O conector inicial usa um endpoint p?blico n?o oficial do Yahoo Chart para
valida??o sem credenciais. Ele n?o deve ser a fonte final de produ??o. A
interface do provedor est? isolada para permitir a troca por um feed licenciado
sem alterar o banco, a API ou o dashboard.
