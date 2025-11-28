# Fluxo de Execucao - Pipeline de Dados V-Credit

## Visao Geral

Este documento descreve a estrategia de execucao do pipeline de dados, dividida em **Setup Inicial** (executado uma unica vez) e **Pipeline Diario** (automatizado).

## Filosofia de Execucao

O projeto segue uma abordagem de **infraestrutura como codigo** com separacao clara entre:

1. **DDL (Data Definition Language)**: Criacao de estruturas (tabelas, views) - **EXECUTADO UMA VEZ**
2. **SRC (Source/Transformacao)**: Carga e transformacao de dados - **EXECUTADO DIARIAMENTE VIA PIPELINE**

## Pre-Requisitos

Antes de iniciar:

1. **Fivetran** configurado e sincronizando dados do Supabase para Databricks
2. **Schema Landing** `v_credit.postgres_public` deve existir e conter dados
3. **Permissoes** necessarias no Databricks (criar schemas, tabelas, views, jobs)
4. **Cluster Databricks** ativo e configurado
5. **Databricks CLI** instalado (para deploy dos jobs via YAML)

---

## Fase 1: Setup Inicial (EXECUTAR UMA VEZ)

Esta fase configura toda a infraestrutura do projeto. Deve ser executada apenas:
- Na primeira vez que o projeto e configurado
- Quando resetar o ambiente completo
- Quando adicionar novas tabelas ao modelo

### Passo 1: Inicializacao do Catalogo

**Notebook**: `init.ipynb`

**Como executar**: Manualmente no Databricks Workspace

**O que faz**: Cria catalogo `v_credit` e schemas (bronze, silver, gold, curated)

### Passo 2: Deploy dos Jobs no Databricks

**Localizacao**: Pasta `pipeline/`

**Como executar**: Usar Databricks CLI ou Asset Bundles para criar os jobs a partir dos arquivos YAML:

```bash
# Navegar ate a pasta do projeto
cd /caminho/para/Grupo-02---RocketLab

```

**Jobs criados**:

1. **V-Credit DDL Pipeline** - Job orquestrador do DDL (executar UMA VEZ)
   - V-Credit DDL - 01 Bronze Layer
   - V-Credit DDL - 02 Silver Layer
   - V-Credit DDL - 03 Gold Layer

2. **V-Credit SRC Pipeline** - Job orquestrador de carga diaria (AUTOMATIZADO)
   - V-Credit SRC - 01 Bronze Layer
   - V-Credit SRC - 02 Silver Layer
   - V-Credit SRC - 03 Gold Layer
   - V-Credit SRC - 04 Curated Layer

### Passo 3: Executar DDL Pipeline (UMA VEZ)

**Job**: `V-Credit DDL Pipeline`

**Como executar**: Trigger manual no Databricks Workflows UI

**O que faz**: Orquestra a criacao de todas as tabelas e views:

```
V-Credit DDL Pipeline
  ↓
  ├─ Bronze Layer: Cria tabelas Bronze (Delta Lake)
  ├─ Silver Layer: Cria tabelas Silver + tabelas de auditoria (*_invalidos)
  └─ Gold Layer: Cria dimensoes (dm_*) e fatos (ft_*)
```

**Importante**: Este job deve ser executado **apenas uma vez** no setup inicial ou quando houver mudancas de schema.

---

## Fase 2: Pipeline Diario (AUTOMATIZADO)

Esta fase processa dados diariamente atraves do job **V-Credit SRC Pipeline**.

### Configuracao do Agendamento

**Job**: `V-Credit SRC Pipeline`

**Frequencia Recomendada**: Diario (02:00 AM)

**Como agendar**:
1. Acessar Databricks Workflows UI
2. Selecionar job `V-Credit SRC Pipeline`
3. Configurar trigger agendado (cron: `0 2 * * *`)

### Fluxo do Pipeline SRC

O job `V-Credit SRC Pipeline` orquestra automaticamente 4 camadas com dependencias:

```
V-Credit SRC Pipeline (Diario)
  ↓
  ├─ 01 Bronze Layer (Landing → Bronze)
  │   └─ ingestion_landing_to_bronze.ipynb
  │
  ├─ 02 Silver Layer (Bronze → Silver + Validacao) [depende: Bronze Layer]
  │   ├─ src_tb_atendente.ipynb
  │   ├─ src_tb_cliente.ipynb
  │   ├─ src_tb_canal.ipynb
  │   ├─ src_tb_motivo.ipynb
  │   ├─ src_tb_custo_chamado.ipynb
  │   ├─ src_tb_pesquisa.ipynb
  │   ├─ src_tb_chamado_log.ipynb
  │   └─ src_tb_chamado.ipynb
  │
  ├─ 03 Gold Layer (Silver → Star Schema) [depende: Silver Layer]
  │   ├─ Dimensoes:
  │   │   ├─ src_dm_atendente.ipynb
  │   │   ├─ src_dm_cliente.ipynb
  │   │   ├─ src_dm_canal.ipynb
  │   │   ├─ src_dm_motivo.ipynb
  │   │   └─ src_dm_chamado.ipynb
  │   └─ Fatos:
  │       ├─ src_ft_atendimento_geral.ipynb
  │       ├─ src_ft_custo_operacional.ipynb
  │       └─ src_ft_performance_agente.ipynb
  │
  └─ 04 Curated Layer (Gold → Views Consumo) [depende: Gold Layer]
      ├─ vw_dm_atendente.ipynb
      ├─ vw_dm_cliente.ipynb
      ├─ vw_dm_canal.ipynb
      ├─ vw_dm_motivo.ipynb
      ├─ vw_dm_chamado.ipynb
      ├─ vw_ft_atendimento_geral.ipynb
      ├─ vw_ft_custo_operacional.ipynb
      └─ vw_ft_performance_agente.ipynb
```

### Caracteristicas do Pipeline

1. **Idempotencia**: Pode ser re-executado sem gerar duplicatas (usa MERGE)
2. **Incremental**: Silver processa apenas `max(ingestion_timestamp)` do Bronze
3. **Auditoria Automatica**: Registros invalidos vao automaticamente para tabelas `*_invalidos`
4. **Dependencias Automaticas**: Cada camada aguarda a anterior completar com sucesso
5. **Paralelizacao**: Tasks dentro da mesma camada rodam em paralelo

### Monitoramento

**Databricks Workflows UI** exibe:
- Status de cada task (Success, Failed, Running)
- Tempo de execucao de cada notebook
- Logs de erro detalhados
- Historico de execucoes

---



### Alertas Recomendados

| Condicao | Acao |
|----------|------|
| Pipeline falha | Notificacao imediata (email/Slack) |
| Qtd Bronze = 0 | Verificar Fivetran sync |
| Qtd Invalidos > 5% | Investigar qualidade dos dados origem |
| Execucao > 30min | Otimizar queries ou aumentar cluster |

---

## Reprocessamento

### Quando Reprocessar

- Correcao de bugs em transformacoes
- Adicao de novas colunas derivadas
- Mudancas em regras de negocio
- Correcao de dados na origem (Supabase)

### Como Reprocessar

**Reprocessar Camada Especifica**:
```python
# Re-executar notebooks SRC necessarios
# Exemplo: reprocessar apenas Silver
dbutils.notebook.run("/src/silver/src_tb_chamado", timeout_seconds=600)
```

**Reprocessar Tudo (desde Bronze)**:
```python
# Executar pipeline completo manualmente
# Ou: Trigger manual do Databricks Workflow
```

**Nota**: Graças ao uso de MERGE, reprocessamento e seguro e nao gera duplicatas.

---

## Validacao Pos-Execucao

### Checklist Diario

- [ ] Fivetran sync completou com sucesso
- [ ] Pipeline Databricks executou sem erros
- [ ] Volumetria Bronze condiz com expectativa
- [ ] Tabelas `*_invalidos` nao cresceram anormalmente
- [ ] Fatos Gold foram carregados

---

## Troubleshooting

### Problema: Pipeline Bronze falha

**Causa Comum**: Fivetran nao sincronizou ou Landing vazio

**Solucao**:
1. Verificar Fivetran dashboard
2. Testar query: `SELECT COUNT(*) FROM v_credit.postgres_public.chamados`
3. Re-executar sync Fivetran se necessario

### Problema: Alta volumetria em `*_invalidos`

**Causa Comum**: Mudanca de schema na origem ou dados corrompidos

**Solucao**:
1. Query: `SELECT * FROM v_credit.silver.tb_chamado_invalidos LIMIT 10`
2. Identificar qual flag esta FALSE
3. Corrigir dados na origem (Supabase)
4. Reprocessar Silver

### Problema: Gold vazio apos execucao

**Causa Comum**: Silver nao tem dados validos ou joins falharam

**Solucao**:
1. Verificar se Silver tem dados: `SELECT COUNT(*) FROM v_credit.silver.tb_chamado`
2. Verificar logs do notebook Gold
3. Testar joins manualmente

---

## Conclusao

O pipeline V-Credit e projetado para ser:
- **Simples**: DDL uma vez, SRC automatizado
- **Confiavel**: Idempotente e com auditoria
- **Escalavel**: Pronto para crescer com o negocio
- **Manutenivel**: Facil de debugar e reprocessar

Para mais detalhes sobre a arquitetura, consulte [Arquitetura de Dados](./02-arquitetura-dados.md).
