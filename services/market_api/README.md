# Vertice Market API

Serviço Python da primeira camada operacional do Vértice. Ele mantém um catálogo de ações, BDRs, índices, ETFs e moedas; coleta histórico diário; persiste preços em SQLite; calcula métricas de risco; e expõe uma API compatível com o dashboard.

## Execução local

```powershell
python -m pip install -r requirements.txt
python -m uvicorn vertice_api.main:app --reload --port 8000
```

A documentação interativa fica em `http://localhost:8000/docs`.

## Aviso sobre a fonte de desenvolvimento

O conector inicial usa um endpoint público não oficial do Yahoo Chart para permitir validação sem credenciais. Ele não deve ser a fonte final de produção. A interface do provedor foi isolada para substituição por um feed licenciado sem alterar API, banco ou dashboard.
