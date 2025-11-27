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
3. **Permissoes** necessarias no Databricks (criar schemas, tabelas, views)
4. **Cluster Databricks** ativo e configurado

---

## Fase 1: Setup Inicial (EXECUTAR UMA VEZ)

Esta fase cria toda a infraestrutura de dados (schemas, tabelas, views). Deve ser executada apenas:
- Na primeira vez que o projeto e configurado
- Quando resetar o ambiente completo
- Quando adicionar novas tabelas ao modelo

### 1.1 Inicializacao

**Notebook**: `init.ipynb`

**O que faz**: Cria catalogo `v_credit` e schemas (bronze, silver, gold, curated)

### 1.2 DDL Bronze

**Notebook**: `ddl/bronze/ddl_tabelas_bronze.ipynb`

**O que faz**: Cria todas as tabelas Bronze com schema Delta Lake

### 1.3 DDL Silver

**Notebooks**: `ddl/silver/ddl_tb_*.ipynb` e `ddl/silver/ddl_tb_*_invalidos.ipynb`

**O que faz**:
- Cria tabelas Silver principais
- Cria tabelas de auditoria (*_invalidos)

### 1.4 DDL Gold

**Notebooks**: `ddl/gold/ddl_dm_*.ipynb` e `ddl/gold/ddl_ft_*.ipynb`

**O que faz**:
- Cria dimensoes (dm_*)
- Cria fatos (ft_*)

### 1.5 DDL Curated

**Notebooks**: `src/curated/vw_*.ipynb`

**O que faz**: Cria views apontando para tabelas Gold

**Nota sobre ordem**: Nao e necessario executar em ordem especifica, os notebooks DDL sao idependêntes (podem ser re-executados sem problemas).

---

## Fase 2: Pipeline Diario (AUTOMATIZADO)

Esta fase processa dados diariamente atraves de um pipeline automatizado (Databricks Workflows).

### Frequencia de Execucao

| Processo | Frequencia | Horario Sugerido |
|----------|------------|------------------|
| Fivetran Sync | Continuo (CDC) | 24/7 |
| Pipeline Databricks | Diario | 02:00 AM |

### Fluxo do Pipeline Diario

```
1. BRONZE INGESTION
   → src/bronze/ingestion_landing_to_bronze.ipynb
   (Landing → Bronze)

2. SILVER TRANSFORMATION
   → src/silver/src_tb_*.ipynb (todos os notebooks)
   (Bronze → Silver com validacao)

3. GOLD DIMENSIONS
   → src/gold/src_dm_*.ipynb (todos os notebooks)
   (Silver → Gold Dimensions)

4. GOLD FACTS
   → src/gold/src_ft_*.ipynb (todos os notebooks)
   (Silver → Gold Facts)

```

### Caracteristicas do Pipeline

1. **Idempotencia**: Pode ser re-executado sem gerar duplicatas (usa MERGE)
2. **Incremental**: Silver processa apenas `max(ingestion_timestamp)` do Bronze
3. **Auditoria Automatica**: Registros invalidos vao automaticamente para tabelas `*_invalidos`

---

## Orquestracao com Databricks Workflows

### Estrutura do Workflow

```yaml
Pipeline V-Credit (Diario - 02:00 AM):

  Task Group 1: Bronze
    - ingestion_landing_to_bronze

  Task Group 2: Silver (depende de Task Group 1)
    - src_tb_atendente
    - src_tb_cliente
    - src_tb_canal
    - src_tb_motivo
    - src_tb_custo_chamado
    - src_tb_pesquisa
    - src_tb_chamado_log
    - src_tb_chamado

  Task Group 3: Gold Dimensions (depende de Task Group 2)
    - src_dm_atendente
    - src_dm_cliente
    - src_dm_canal
    - src_dm_motivo
    (Podem rodar em paralelo)

  Task Group 4: Gold Facts (depende de Task Group 3)
    - src_ft_atendimento_geral
    - src_ft_custo_operacional
    - src_ft_performance_agente
    (Podem rodar em paralelo)
```


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
