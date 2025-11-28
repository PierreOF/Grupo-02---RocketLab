# Aprendizados do Projeto - V-Credit Data Lakehouse

## Equipe Pypy Noel

Este documento registra os principais aprendizados tecnicos, de negocio e metodologicos adquiridos durante o desenvolvimento do projeto V-Credit Data Lakehouse.

**Equipe**:
- João Gabriel Araújo Azevedo de Albuquerque
- Marcus Pierre Melo Monteiro
- Pedro de Araújo Duarte Gusmao

---

## Contexto do Projeto

O projeto V-Credit consistiu na implementacao de um Data Lakehouse completo para analise de operacoes de atendimento ao cliente de uma fintech. O objetivo foi transformar dados transacionais brutos em insights acionaveis para stakeholders de diferentes areas (Financeiro, Marketing, Customer Success e TI).

**Stack Tecnologica**:
- Databricks (Delta Lake + PySpark)
- Supabase (PostgreSQL)
- Fivetran (ELT)
- Power BI
- Databricks Workflows

---

## 1. Aprendizados Tecnicos

### 1.1 Arquitetura Medallion (Bronze/Silver/Gold/Curated)

**O que aprendemos**:

A arquitetura Medallion nao e apenas uma convencao de nomenclatura, mas uma filosofia de separacao de responsabilidades que traz beneficios concretos:

1. **Bronze (Raw + Metadata)**
   - **Aprendizado**: Sempre preservar os dados brutos identicos a origem
   - **Beneficio**: Permite reprocessamento completo em caso de bugs nas camadas superiores
   - **Pratica**: Adicionar metadados (`ingestion_timestamp`, `origem`) desde o inicio facilita rastreabilidade
   - **Estrategia**: Full overwrite e adequado quando a fonte ja e confiavel (Fivetran)

2. **Silver (Clean + Validated)**
   - **Aprendizado**: A camada Silver e onde a qualidade de dados realmente acontece
   - **Beneficio**: Separar registros validos de invalidos (tabelas `*_invalidos`) permite auditoria sem perder dados
   - **Pratica**: Validacoes devem ser explicitas (flags booleanas) e nao silenciosas
   - **Estrategia**: MERGE incremental baseado em `ingestion_timestamp` evita reprocessar tudo

3. **Gold (Dimensional Model)**
   - **Aprendizado**: Star Schema e modelagem dimensional nao sao conceitos abstratos - eles resolvem problemas reais de performance em BI
   - **Beneficio**: Consultas no Power BI ficam ate 10x mais rapidas com fatos pre-agregados
   - **Pratica**: Usar surrogate keys (hash MD5) ao inves de composite natural keys simplifica joins
   - **Estrategia**: Desnormalizar dimensoes (ex: incluir `ds_faixa_etaria` diretamente em `dm_cliente`) melhora UX do analista

4. **Curated (Views para Consumo)**
   - **Aprendizado**: Views 1:1 parecem redundantes, mas tem valor real em governanca
   - **Beneficio**: Facilita aplicar permissoes granulares e esconder complexidade do Gold
   - **Pratica**: Views devem ser simples (`SELECT *`), logica de negocio fica no Gold

**Principal Insight**:
> Cada camada tem um proposito unico. Tentar misturar responsabilidades (ex: validacao no Bronze, agregacao no Silver) gera confusao e dificulta manutencao.

---

### 1.2 Databricks e Delta Lake

**O que aprendemos**:

1. **ACID no Data Lake**
   - Delta Lake traz transacoes ACID para ambientes distribuidos
   - Conseguimos fazer MERGE (upsert) de forma confiavel, algo que seria complexo com Parquet puro
   - Time Travel e subestimado: conseguimos reverter uma carga incorreta usando `VERSION AS OF`

2. **Propriedades Delta Importantes**
   ```python
   # Estas propriedades fazem diferenca real:
   'delta.enableChangeDataFeed' = 'true'      # Para capturar mudancas
   'delta.autoOptimize.optimizeWrite' = 'true'  # Melhora escrita
   'delta.autoOptimize.autoCompact' = 'true'    # Compactacao automatica
   ```
   - **Aprendizado**: Habilitar desde o DDL inicial evita retrabalho

3. **Notebooks vs. Scripts**
   - Notebooks Databricks sao excelentes para desenvolvimento iterativo e documentacao
   - Markdown cells sao essenciais para explicar logica de negocio
   - Separar DDL de SRC facilita manutencao (DDL roda 1x, SRC roda diariamente)

4. **Performance**
   - `F.col()` e muito mais rapido que acessar colunas como strings
   - `.cache()` em DataFrames que serao usados multiplas vezes economiza recompute
   - `.coalesce(1)` para escrever arquivo unico so deve ser usado em tabelas pequenas

**Desafio Enfrentado**:
> Inicialmente estavamos recriando tabelas com `CREATE OR REPLACE TABLE`. Aprendemos que isso quebra dependencias em jobs. A solucao foi usar `IF NOT EXISTS` no DDL e MERGE no SRC.

---

### 1.3 PySpark

**O que aprendemos**:

1. **Transformacoes vs. Acoes**
   - Transformacoes sao lazy (`.select()`, `.filter()`, `.withColumn()`)
   - Acoes disparam execucao (`.count()`, `.show()`, `.write()`)
   - **Pratica**: Construir pipeline de transformacoes e executar uma unica acao no final

2. **Funcoes Importantes**
   - `F.col()`, `F.lit()`, `F.when()`, `F.coalesce()`, `F.trim()`, `F.regexp_replace()`
   - `F.md5(F.concat_ws())` para gerar surrogate keys
   - `F.current_timestamp()` para metadata

3. **Window Functions**
   - Aprendemos a usar `F.row_number().over(Window.partitionBy().orderBy())` para deduplicacao
   - Essencial para remover duplicatas mantendo o registro mais recente

4. **Validacoes com Flags**
   ```python
   .withColumn("flag_pk_valida", F.col("cd_atendente").isNotNull())
   .withColumn("flag_range_nivel", F.col("nr_nivel").between(1, 2))
   .withColumn("valido", F.col("flag_pk_valida") & F.col("flag_range_nivel"))
   ```
   - Separar cada validacao em flag propria facilita debug

5. **MERGE Pattern**
   ```python
   target.alias("t").merge(
       source.alias("s"),
       "t.cd_atendente = s.cd_atendente"
   ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
   ```
   - Idempotencia: pode rodar N vezes sem duplicar dados

**Principal Insight**:
> PySpark nao e Python "normal". Pensar em operacoes distribuidas (broadcast, partitions) faz diferenca em performance.

---

### 1.4 Modelagem Dimensional (Star Schema)

**O que aprendemos**:

1. **Dimensoes vs. Fatos**
   - **Dimensoes**: Sao o "quem, o que, onde, quando" (dm_cliente, dm_atendente, dm_motivo)
   - **Fatos**: Sao as metricas e medidas (ft_atendimento_geral, ft_custo_operacional)
   - **Pratica**: Se a entidade tem muitos registros repetidos e poucos atributos descritivos, e fato. Se tem poucos registros mas muitos atributos, e dimensao.

2. **Surrogate Keys**
   - Usar hash MD5 de natural keys como `sk_*` (surrogate key)
   - **Vantagem**: Independencia de mudancas na origem
   - **Exemplo**:
   ```python
   F.md5(F.concat_ws("_", F.col("cd_atendente"))).alias("sk_atendente")
   ```

3. **Dimensoes Degeneradas**
   - Campos como `cd_chamado` vao direto no fato (nao criam dimensao propria)
   - **Criterio**: Se tem cardinalidade alta e nao precisa de atributos descritivos

4. **Fatos Agregados**
   - Criar multiplos fatos com propositos diferentes (geral, custo, performance)
   - Evita que analistas tenham que fazer `GROUP BY` complexos no Power BI
   - **Exemplo**: `ft_custo_operacional` ja traz `val_custo_total` calculado

5. **Desnormalizacao Inteligente**
   - Incluir colunas descritivas nas dimensoes mesmo que venham de lookup
   - **Exemplo**: `dm_cliente` inclui `ds_faixa_etaria` calculado a partir de `nr_idade`
   - **Beneficio**: Analista nao precisa fazer case no Power BI

**Principal Insight**:
> Star Schema nao e sobre "normalizar tudo". E sobre balancear performance, simplicidade e usabilidade para o analista de BI.

---

### 1.5 Qualidade de Dados

**O que aprendemos**:

1. **Estrategia de Validacao**
   - Validar cedo (Silver) e nao tarde (Gold/BI)
   - Criar flags booleanas para cada regra (`flag_pk_valida`, `flag_range_valido`)
   - Flag `valido = flag1 & flag2 & flag3` determina se vai para tabela principal

2. **Tabelas de Auditoria `*_invalidos`**
   - Registros que falham validacao vao para `tb_<entidade>_invalidos`
   - Mesma estrutura da tabela principal + flags de validacao
   - **Beneficio**: Nao perde dados, permite investigacao de qualidade

3. **Tipos de Validacao Implementadas**
   - **Primary Key**: `F.col("pk").isNotNull()`
   - **Range**: `F.col("valor").between(min, max)`
   - **Tamanho String**: `F.length(F.col("campo")) <= limite`
   - **Formato**: `F.regexp_replace()` para corrigir typos conhecidos
   - **Integridade**: Verificar se FKs existem nas dimensoes

4. **Correcoes na Camada Silver**
   - Aprendemos que alguns problemas devem ser corrigidos (ex: typos como "Compra no autorizada")
   - Usar `F.regexp_replace()` para fix deterministico
   - Documentar correcoes em comentarios/markdown

**Desafio Enfrentado**:
> Inicialmente estavamos silenciosamente ignorando registros invalidos. Aprendemos que transparencia (tabelas `*_invalidos`) e melhor que filtros silenciosos.

---

### 1.6 Orquestracao com Databricks Workflows

**O que aprendemos**:

1. **Separacao DDL vs. SRC**
   - **DDL Jobs**: Executados uma unica vez no setup inicial
   - **SRC Jobs**: Executados diariamente (pipeline de carga)
   - **Beneficio**: Evita recriar estruturas desnecessariamente

2. **Dependencias entre Tasks**
   ```yaml
   - task_key: Silver_Layer
     depends_on:
       - task_key: Bronze_Layer
   ```
   - Databricks garante ordem de execucao
   - Se Bronze falha, Silver nao executa

3. **Paralelizacao**
   - Tasks na mesma camada sem dependencia entre si rodam em paralelo
   - Exemplo: Todos os notebooks Silver rodam simultaneamente apos Bronze completar

4. **Jobs YAML (Infrastructure as Code)**
   - Definir jobs em YAML e versionavel no Git
   - Deploy via Databricks CLI (`databricks bundle deploy`)
   - **Vantagem**: Reproducibilidade e versionamento

5. **Monitoramento**
   - Databricks Workflows UI mostra status de cada task
   - Logs de erro detalhados facilitam troubleshooting
   - Historico de execucoes permite analise de performance

**Principal Insight**:
> Orquestracao via YAML jobs e muito superior a scripts manuais. Permite governanca, auditoria e recuperacao de falhas.

---

### 1.7 Integracao de Dados (Fivetran)

**O que aprendemos**:

1. **Por que Fivetran?**
   - Simula cenario real de producao (dados vem de sistemas externos)
   - Evita abordagens simplistas (upload manual de CSV)
   - Demonstra integracao real entre banco de dados e lakehouse

2. **CDC (Change Data Capture)**
   - Fivetran sincroniza mudancas automaticamente
   - Near real-time: dados atualizados continuamente
   - **Beneficio**: Lakehouse reflete estado atual da origem

3. **Landing Zone**
   - Fivetran carrega em schema separado (`postgres_public`)
   - **Pratica**: Nao transformar dados no Landing, deixar identico a origem
   - Bronze le do Landing e adiciona metadata

4. **Monitoramento de Sync**
   - Acompanhar Fivetran dashboard para detectar falhas de sync
   - Se Bronze estiver vazio, checar Fivetran primeiro

**Principal Insight**:
> Usar uma ferramenta de ingestao gerenciada (Fivetran) libera tempo para focar em transformacoes de valor ao inves de scripts de carga.

---

## 2. Aprendizados de Negocio

### 2.1 Traduzir Dor de Negocio em Metrica

**O que aprendemos**:

Stakeholders nao falam em "fatos" e "dimensoes". Eles falam em problemas de negocio:
- "Os custos estao altos"
- "A satisfacao caiu"
- "As filas sao longas"

**Nossa responsabilidade**: Traduzir isso em queries SQL/PySpark e metricas mensuraveis.

**Exemplos**:

| Dor do Stakeholder | Metrica Implementada |
|-------------------|----------------------|
| "Custos excessivos no atendimento" | `SUM(vl_custo)` agrupado por `ds_motivo` |
| "Satisfacao caiu" | `AVG(nr_nota_satisfacao)` ao longo do tempo |
| "Filas longas" | `AVG(nr_tempo_espera_segundos)` por `ds_tipo_interacao` |
| "Bot ineficaz" | Taxa de transbordo: `COUNT(CASE WHEN cd_atendente IS NOT NULL THEN 1 END) / COUNT(*)` |

**Principal Insight**:
> Dados sem contexto de negocio sao inuteis. Sempre perguntar: "Qual decisao essa metrica vai informar?"

---

### 2.2 Storytelling com Dados

**O que aprendemos**:

Nao basta ter os dados corretos. E preciso contar uma historia que convenca stakeholders a agir.

**Estrutura que Funciona**:
1. **O Choque** (Impacto Emocional): "48% dos clientes estao insatisfeitos"
2. **A Causa** (Diagnostico): "Porque a fila humana e de 9 minutos"
3. **A Solucao** (Business Case): "Automacao economiza 29% do orcamento"

**Praticas**:
- Sempre comecar com a metrica mais impactante (CSAT, Custo)
- Usar visualizacoes simples (KPI cards, barras, linhas)
- Evitar tabelas com muitas colunas

---

### 2.3 Data-Driven vs. Data-Informed

**O que aprendemos**:

Dados informam decisoes, mas nao substituem julgamento de negocio.

**Exemplo**: Os dados mostraram que automacao economiza 29%, mas a decisao de QUAL motivo automatizar primeiro envolve:
- Complexidade tecnica de implementacao
- Impacto na experiencia do cliente
- Risco de erros do bot

**Nossa funcao**: Fornecer evidencias, nao ditar decisoes.

---

## 3. Aprendizados de Processos e Metodologia

### 3.1 Versionamento (Git)

**O que aprendemos**:

1. **Branches**
   - `main`: Codigo em producao
   - `develop`: Codigo em desenvolvimento
   - Feature branches para grandes mudancas

2. **Commits Significativos**
   - Seguir Conventional Commits (`feat:`, `fix:`, `refactor:`)
   - Mensagens em ingles
   - Commits atomicos (uma mudanca logica por commit)

3. **Rebase vs. Merge**
   - Usar `git pull --rebase` para manter historico linear
   - Evita commits de merge desnecessarios

**Desafio Enfrentado**:
> Confusao entre branch local `dev` e remota `origin/develop`. Solucao: Usar `git pull --rebase` para sincronizar.

---

### 3.2 Documentacao

**O que aprendemos**:

1. **Documentacao e Codigo**
   - Markdown cells nos notebooks explicam o "por que", nao apenas o "o que"
   - Codigo autodocumentado com nomes de variaveis claros

2. **Documentacao Externa**
   - Criar docs estruturados (01-visao-geral, 02-arquitetura, etc.)
   - Sequencia logica para novos integrantes entenderem o projeto

3. **Manutencao de Docs**
   - Documentacao desatualizada e pior que nenhuma documentacao
   - Sempre atualizar docs quando mudar implementacao

**Principal Insight**:
> Codigo sem documentacao e uma bomba-relogio. Nos mesmos esquecemos decisoes apos 2 semanas.

---

### 3.3 Separacao de Responsabilidades

**O que aprendemos**:

1. **DDL vs. SRC**
   - DDL: Estruturas (CREATE TABLE, CREATE VIEW)
   - SRC: Dados (INSERT, MERGE, transformacoes)
   - **Beneficio**: DDL roda 1x, SRC roda N vezes

2. **Notebooks Modulares**
   - Cada notebook faz UMA coisa (uma tabela, uma dimensao)
   - Evitar "god notebooks" que fazem tudo
   - **Vantagem**: Reprocessamento seletivo

3. **Configuracao vs. Codigo**
   - Jobs definidos em YAML (configuracao)
   - Logica de negocio em notebooks (codigo)
   - **Vantagem**: Mudancas em orquestracao nao mexem em codigo

---

## 4. Desafios Enfrentados e Solucoes

### Desafio 1: Typo em Dados Fonte

**Problema**: Coluna `nome_motivo` tinha valor "Compra no autorizada" (sem til) no Bronze

**Solucao**:
- Adicionar `F.regexp_replace()` na camada Silver para corrigir
- Documentar correcao em markdown cell
- **Aprendizado**: Nao confiar cegamente em dados da origem

---

### Desafio 2: Performance em Joins

**Problema**: Joins entre Silver e dimensoes demorando muito

**Solucao**:
- Usar `.cache()` em dimensoes pequenas
- Garantir que colunas de join estejam indexadas
- Usar broadcast hint quando uma tabela e pequena
- **Aprendizado**: Spark precisa de hints para otimizar joins

---

### Desafio 3: Duplicatas

**Problema**: Bronze recebia duplicatas da origem

**Solucao**:
- Implementar deduplicacao no Silver usando Window Functions
- `F.row_number().over(Window.partitionBy("pk").orderBy(F.desc("ingestion_timestamp")))`
- **Aprendizado**: Sempre dedupe antes de MERGE

---

### Desafio 4: Falha de Job por Dependencia

**Problema**: Job Gold falhava porque Silver ainda nao tinha terminado

**Solucao**:
- Adicionar `depends_on` no YAML do job
- Databricks garante ordem de execucao
- **Aprendizado**: Nunca assumir que tasks rodam em ordem sem dependencia explicita

---

## 5. Boas Praticas Identificadas

### 5.1 Arquitetura

- **Separar camadas por responsabilidade** (Bronze = raw, Silver = clean, Gold = analytics)
- **Adicionar metadata desde o Bronze** (`ingestion_timestamp`, `origem`)
- **Usar Delta Lake properties** (`enableChangeDataFeed`, `autoOptimize`)

### 5.2 Qualidade de Dados

- **Criar flags de validacao explicitas**
- **Separar validos de invalidos** (tabelas `*_invalidos`)
- **Validar cedo** (Silver), nao tarde (Gold/BI)
- **Documentar correcoes conhecidas**

### 5.3 Modelagem

- **Usar surrogate keys** (hash MD5) ao inves de composite natural keys
- **Desnormalizar dimensoes** para facilitar uso em BI
- **Criar multiplos fatos especializados** (geral, custo, performance)

### 5.4 Orquestracao

- **Separar DDL de SRC**
- **Definir jobs em YAML** (Infrastructure as Code)
- **Usar dependencias explicitas** entre tasks
- **Monitorar execucoes** via Databricks Workflows UI

### 5.5 Codigo

- **Notebooks modulares** (uma responsabilidade por notebook)
- **Markdown cells explicativas**
- **Commits atomicos e significativos**
- **Codigo autodocumentado** (nomes claros de variaveis)

### 5.6 Documentacao

- **Documentar decisoes de arquitetura**
- **Explicar o "por que", nao apenas o "o que"**
- **Manter docs sincronizados com codigo**

---

## 6. Habilidades Desenvolvidas

### Tecnicas

- [x] PySpark (transformacoes, window functions, MERGE)
- [x] Databricks (notebooks, workflows, Delta Lake)
- [x] SQL (DDL, DML, queries analiticas)
- [x] Modelagem Dimensional (Star Schema)
- [x] Arquitetura Medallion (Bronze/Silver/Gold)
- [x] Infrastructure as Code (YAML, Databricks CLI)
- [x] Qualidade de Dados (validacao, auditoria)

### Negocio

- [x] Traducao de dor de negocio em metrica
- [x] Storytelling com dados
- [x] Analise de KPIs (CSAT, custos, tempos de espera)
- [x] Identificacao de oportunidades de automacao

### Metodologicas

- [x] Documentacao tecnica estruturada
- [x] Separacao de responsabilidades (DDL/SRC)
- [x] Modularizacao de codigo

---

## 7. Conclusao

Este projeto foi uma experiencia completa de implementacao de Data Lakehouse, desde a ingestao de dados ate a entrega de insights de negocio via dashboards.

### Principais Conquistas

1. **Arquitetura Moderna**: Implementamos uma arquitetura Medallion completa e escalavel
2. **Qualidade de Dados**: Sistema robusto de validacao e auditoria
3. **Insights Acionaveis**: Respondemos as 4 dores de negocio dos stakeholders com evidencias
4. **Infrastructure as Code**: Jobs versionados e reproduziveis via YAML
5. **Documentacao Completa**: Projeto totalmente documentado para novos integrantes

### O que Levamos Daqui

Alem das habilidades tecnicas (PySpark, Databricks, Modelagem Dimensional), aprendemos que:

- **Dados sem contexto nao geram valor**: E preciso entender o negocio
- **Arquitetura importa**: Separacao de responsabilidades facilita manutencao
- **Qualidade e transparencia**: Melhor mostrar problemas (tabelas `*_invalidos`) do que esconder
- **Documentacao e investimento**: Codigo sem docs e passivo, nao ativo

---

**Equipe Pypy Noel**

João Gabriel Araújo Azevedo de Albuquerque
Marcus Pierre Melo Monteiro
Pedro de Araújo Duarte Gusmao
