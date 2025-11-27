# Documentacao do Projeto V-Credit Data Lakehouse

Bem-vindo a documentacao completa do projeto de Data Lakehouse da V-Credit. Esta documentacao fornece uma visao abrangente da arquitetura, processos e decisoes tecnicas do projeto.

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
