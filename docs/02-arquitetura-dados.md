# Arquitetura de Dados - V-Credit Lakehouse

## Visao Geral da Arquitetura

Este projeto implementa uma arquitetura de Data Lakehouse moderna, seguindo o padrao Medallion Architecture (Bronze/Silver/Gold) com uma camada adicional Curated para consumo em ferramentas de BI.

```
[Supabase PostgreSQL]
        ↓
   [Fivetran ETL]
        ↓
[Databricks - Landing Zone (postgres_public)]
        ↓
   [BRONZE LAYER] ← Dados brutos + metadata
        ↓
   [SILVER LAYER] ← Validacao + Limpeza + Auditoria
        ↓
    [GOLD LAYER] ← Modelagem Dimensional (Star Schema)
        ↓
  [CURATED LAYER] ← Views para consumo
        ↓
    [Power BI] ← Dashboards e Relatorios
```

## Componentes da Arquitetura

### 1. Origem dos Dados: Supabase (PostgreSQL)

**O que e**: Banco de dados PostgreSQL gerenciado na nuvem que armazena os dados transacionais do sistema de atendimento da V-Credit.

**Tabelas Fonte**:
- `base_atendentes`: Cadastro de funcionarios (20 atendentes)
- `base_motivos`: Catalogo de motivos de contato
- `canais`: Canais de atendimento disponiveis
- `chamados`: Tickets de atendimento (transacoes)
- `chamados_hora`: Log de timestamps (abertura, inicio, fim)
- `clientes`: Base de clientes
- `custos`: Custos associados a cada chamado
- `pesquisa_satisfacao`: Notas de satisfacao (CSAT)

**Localizacao**: Supabase Cloud (PostgreSQL 17.6)

### 2. Camada de Ingestao: Fivetran

**O que e**: Ferramenta de ELT (Extract, Load, Transform) que sincroniza automaticamente os dados do Supabase para o Databricks.

**Funcao**:
- Conecta ao banco PostgreSQL do Supabase
- Extrai dados das tabelas fonte
- Carrega no Databricks em um schema chamado `postgres_public` (Landing Zone)
- Mantem sincronizacao automatica (CDC - Change Data Capture)

**Por que Fivetran?**
- Simula um **cenario real de producao** onde dados vem de sistemas externos (bancos de dados)
- Replica a arquitetura empresarial moderna de ingestao de dados
- Evita abordagens simplistas como upload manual de CSVs em volumes do Databricks
- Demonstra integracao real entre sistemas (Supabase ↔ Databricks)

**Schema no Databricks**: `v_credit.postgres_public` (Landing Zone)

### 3. Data Platform: Databricks

**O que e**: Plataforma unificada de analytics e IA baseada em Apache Spark e Delta Lake.

**Catalogo**: `v_credit`

**Schemas**:
1. **postgres_public** (Landing Zone - gerenciado pelo Fivetran)
2. **bronze** (Raw data com metadata)
3. **silver** (Dados limpos e validados)
4. **gold** (Modelagem dimensional)
5. **curated** (Views para BI)

**Tecnologias Utilizadas**:
- **Delta Lake**: Formato de storage ACID para lakehouse
- **PySpark**: Engine de processamento distribuido
- **Databricks Notebooks**: Ambiente de desenvolvimento
- **Delta Tables**: Suporte a MERGE, time travel, CDC

### 4. Camada Bronze (Raw + Metadata)

**Objetivo**: Armazenar dados brutos com adicao de metadados de rastreabilidade.

**Processo**:
- Le dados do schema `postgres_public` (Landing Zone do Fivetran)
- Adiciona colunas de metadados:
  - `ingestion_timestamp`: Timestamp da carga
  - `origem`: Identificador da origem (ex: "supabase")
- Salva em formato Delta com propriedades otimizadas

**Caracteristicas**:
- Dados identicos a origem (schema preservado)
- Estrategia de carga: Full Overwrite
- Delta properties:
  - `enableChangeDataFeed = true`
  - `autoOptimize.optimizeWrite = true`
  - `autoOptimize.autoCompact = true`

**Notebooks**:
- `ddl/bronze/ddl_tabelas_bronze.ipynb`: Cria estrutura das tabelas
- `src/bronze/ingestion_landing_to_bronze.ipynb`: Executa a ingestao

### 5. Camada Silver (Clean + Validated)

**Objetivo**: Dados limpos, validados e prontos para consumo analitico, com auditoria de qualidade.

**Processo de Transformacao**:
1. **Extracao Incremental**: Le apenas registros com `ingestion_timestamp` mais recente
2. **Limpeza**: Remove espacos, converte tipos, renomeia colunas para padrao
3. **Validacao**: Aplica regras de qualidade de dados
   - Validacao de PK (nao nulo)
   - Validacao de ranges (ex: nivel 1-2, nota 1-5)
   - Validacao de integridade (tamanho de strings, formatos)
4. **Split de Dados**:
   - **Validos**: MERGE na tabela principal
   - **Invalidos**: Overwrite na tabela de auditoria `*_invalidos`
5. **Deduplicacao**: Remove duplicatas por PK

**Nomenclatura**:
- Tabelas principais: `tb_<entidade>` (ex: `tb_chamado`, `tb_cliente`)
- Tabelas de auditoria: `tb_<entidade>_invalidos`

**Estrategia de Carga**: MERGE (Upsert) baseado em PK

**Notebooks**:
- DDL: `ddl/silver/ddl_tb_*.ipynb` (tabelas principais e auditoria)
- Transformacao: `src/silver/src_tb_*.ipynb`

### 6. Camada Gold (Dimensional Model)

**Objetivo**: Modelagem dimensional (Star Schema) otimizada para analytics e BI.

**Arquitetura**: Star Schema
- **Dimensoes (dm_*)**: Tabelas de referencia desnormalizadas
- **Fatos (ft_*)**: Tabelas de metricas transacionais

**Dimensoes Implementadas**:
- `dm_atendente`: Funcionarios com descricao de perfil
- `dm_cliente`: Clientes com demographics
- `dm_canal`: Canais de atendimento
- `dm_motivo`: Motivos com classificacao de automacao
- `dm_chamado`: Dimensao de tickets (se necessario)

**Fatos Implementados**:
- `ft_atendimento_geral`: Fato principal com todas as metricas
- `ft_custo_operacional`: Fato focado em custos
- `ft_performance_agente`: Fato de desempenho individual

**Caracteristicas**:
- Chaves surrogate (hash MD5 de natural keys)
- Dimensoes degeneradas (ex: `cd_chamado` no fato)
- Flags booleanas convertidas para SMALLINT (0/1)
- Metricas com tratamento de NULL (F.coalesce)

**Estrategia de Carga**: MERGE baseado em surrogate key

**Notebooks**:
- DDL: `ddl/gold/ddl_dm_*.ipynb` e `ddl/gold/ddl_ft_*.ipynb`
- Transformacao: `src/gold/src_dm_*.ipynb` e `src/gold/src_ft_*.ipynb`

### 7. Camada Curated (Views para BI)

**Objetivo**: Exposicao de objetos Gold atraves de views simples para consumo no Power BI.

**Processo**:
- Cria views 1:1 apontando para tabelas Gold
- Views nao possuem logica adicional (apenas SELECT *)
- Facilita governanca e permissionamento

**Nomenclatura**: `vw_<objeto>` (ex: `vw_dm_atendente`, `vw_ft_atendimento_geral`)

**Notebooks**: `src/curated/vw_*.ipynb`

### 8. Consumo: Power BI

**O que e**: Ferramenta de Business Intelligence da Microsoft para criacao de dashboards interativos.

**Conexao**:
- Conecta ao Databricks via conector nativo
- Consome views da camada `curated`
- Modo de importacao ou DirectQuery (dependendo do volume)

**Dashboards Implementados**:
1. **Visao Financeira**: Custo por motivo, potencial de economia
2. **Visao CX**: CSAT, tendencias, experiencia negativa
3. **Visao Operacional**: Tempos de espera, comparacao Bot vs Humano
4. **Visao Tecnologica**: Taxa de transbordo, analise demografica

## Fluxo de Dados Detalhado

### Fluxo Completo (End-to-End)

```
1. [Usuario] → [Sistema Transacional] → [Supabase PostgreSQL]
2. [Fivetran] sincroniza → [Databricks: postgres_public]
3. [Bronze Notebook] le → [Landing] → salva → [v_credit.bronze.*]
4. [Silver Notebook] le → [Bronze] → valida → split → [v_credit.silver.tb_* + tb_*_invalidos]
5. [Gold Notebook] le → [Silver] → modela → [v_credit.gold.dm_* + ft_*]
6. [Curated Notebook] cria views → [v_credit.curated.vw_*]
7. [Power BI] conecta → [Curated] → renderiza → [Dashboard]
```

### Frequencia de Atualizacao

| Camada | Frequencia Sugerida | Tipo |
|--------|---------------------|------|
| Fivetran → Landing | Continuo (CDC) | Near Real-Time |
| Landing → Bronze | Diario (cron) | Batch |
| Bronze → Silver | Diario (pos-Bronze) | Batch |
| Silver → Gold | Diario (pos-Silver) | Batch |
| Gold → Curated | Sob demanda | Instantaneo (views) |
| Curated → Power BI | Refresh diario | Scheduled |

## Decisoes Tecnicas

### Por que Delta Lake?
- **ACID Transactions**: Garante consistencia mesmo em ambientes distribuidos
- **Time Travel**: Permite auditoria e rollback
- **MERGE**: Suporte nativo a upserts
- **Schema Evolution**: Facilita evolucao de schemas
- **Performance**: Otimizacoes automaticas (compaction, Z-ordering)

### Por que Medallion Architecture?
- **Separacao de Conceitos**: Cada camada tem proposito unico
- **Reprocessamento**: Facil reprocessar camadas superiores
- **Qualidade**: Validacao progressiva de qualidade
- **Performance**: Otimizacao especifica por camada

### Por que Fivetran?
- **Cenario Realista**: Simula ambiente de producao onde dados vem de sistemas externos
- **Arquitetura Empresarial**: Replica pipeline moderno de ingestao de dados
- **Integracao Real**: Demonstra conexao entre banco de dados (Supabase) e lakehouse (Databricks)
- **Evita Simplificacoes**: Nao usa upload manual de CSVs em volumes, que nao reflete realidade empresarial

## Seguranca e Governanca

### Controle de Acesso
- Databricks: Unity Catalog para governanca
- Schemas: Permissoes por camada (Bronze = restrito, Curated = leitura)
- Power BI: RLS (Row-Level Security) se necessario

### Auditoria
- Tabelas `*_invalidos` rastreiam dados rejeitados
- `ingestion_timestamp` permite rastreabilidade
- Delta Lake time travel para versioning

## Monitoramento

### Metricas Criticas
- **Pipeline Health**: Fivetran sync status
- **Data Quality**: Volume de registros em `*_invalidos`
- **Performance**: Tempo de execucao dos notebooks
- **Freshness**: Latencia entre evento e disponibilidade no BI

## Proximos Passos

1. Consulte o [Modelo de Dados](./03-modelo-dados.md) para detalhes das tabelas
2. Veja o [Fluxo de Execucao](./05-fluxo-execucao.md) para ordem de processamento
3. Leia [Qualidade de Dados](./06-qualidade-dados.md) para estrategia de validacao
