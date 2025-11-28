# Documentacao do Projeto V-Credit Data Lakehouse

Bem-vindo a documentacao completa do projeto de Data Lakehouse da V-Credit. Esta documentacao fornece uma visao abrangente da arquitetura, processos e decisoes tecnicas do projeto.

## Links do Grupo 2
* [Arquitetura do Sistema](https://excalidraw.com/#room=155f71a11a4c58eb80e4,ToNOtl9yxLZZQQoi7tVE6A)
* [dicionário de dados](https://docs.google.com/spreadsheets/d/1A_ZCraoZs97ySkYHRmj2wAcLwEFpf-EljVoA4hD-2VU/edit?gid=1419684504#gid=1419684504)
* [relatório das dailys](https://docs.google.com/document/d/16cR93gWBPUY5p74dm8d3jnf8Mi2HiF7qI5Q_kfNKUoc/edit?usp=sharing)
* [Proposta de solução](https://docs.google.com/document/d/1nLOW8hzSt6CcC94RLKzp7kIRkY869Hcc0Z6qGIhWgUg/edit?tab=t.0)
* [Trello](https://trello.com/invite/b/691f8bc73bf6e386d27d8642/ATTI9c410a14997fde7225dc873d44e3482027BD868E/pypynoel-rocketlab)

## Indice da Documentacao

### 1. [Visao Geral do Projeto](./01-visao-geral-projeto.md)
Introducao ao projeto, objetivos de negocio e contexto da V-Credit.

### 2. [Arquitetura de Dados](./02-arquitetura-dados.md)
Arquitetura end-to-end desde o Supabase ate o Power BI, incluindo Fivetran e Databricks.

### 3. [Modelo de Dados](./03-modelo-dados.md)
Detalhamento das camadas Bronze, Silver, Gold e Curated, incluindo esquemas e relacionamentos.

### 4. [Caso de Negocio](./04-caso-negocio.md)
Analise das dores de negocio e como os dados fornecem evidencias para tomada de decisao.

### 5. [Fluxo de Execucao](./05-fluxo-execucao.md)
Ordem de execucao dos notebooks e dependencias entre processos.

### 6. [Qualidade de Dados](./06-qualidade-dados.md)
Estrategia de validacao, auditoria e monitoramento da qualidade dos dados.

## Estrutura do Repositorio

```
.
├── init.ipynb                          # Inicializacao do catalogo e schemas
├── ddl/                               # Notebooks de DDL
│   ├── bronze/                        # Criacao de tabelas Bronze
│   ├── silver/                        # Criacao de tabelas Silver e auditoria
│   └── gold/                          # Criacao de dimensoes e fatos
├── src/                               # Notebooks de processamento
│   ├── bronze/                        # Ingestao Landing → Bronze
│   ├── silver/                        # Transformacao Bronze → Silver
│   ├── gold/                          # Modelagem Silver → Gold
│   └── curated/                       # Views para consumo
└── docs/                              # Esta documentacao
```

## Como Usar Esta Documentacao

1. Se voce e novo no projeto, comece pela [Visao Geral](./01-visao-geral-projeto.md)
2. Para entender a arquitetura tecnica, leia [Arquitetura de Dados](./02-arquitetura-dados.md)
3. Para trabalhar com os dados, consulte o [Modelo de Dados](./03-modelo-dados.md)
4. Para executar o pipeline, siga o [Fluxo de Execucao](./05-fluxo-execucao.md)

## Links Rapidos

- **Catalogo Databricks**: `v_credit`
- **Schemas**: `bronze`, `silver`, `gold`, `curated`
- **Banco Origem**: Supabase (PostgreSQL)
- **ETL**: Fivetran
- **BI**: Power BI
