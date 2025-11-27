# Qualidade de Dados - V-Credit

## Visao Geral

A qualidade de dados e um pilar fundamental deste projeto. Dados de baixa qualidade levam a insights incorretos e decisoes equivocadas. Este documento descreve a estrategia de validacao, auditoria e monitoramento implementada na camada Silver.

## Filosofia de Qualidade

### Principios

1. **Fail Fast**: Identificar problemas o mais cedo possivel no pipeline
2. **Rastreabilidade**: Registrar todos os problemas para analise
3. **Nao Bloqueio**: Dados invalidos nao bloqueiam o pipeline, vao para auditoria
4. **Transparencia**: Stakeholders devem saber quando ha problemas de qualidade

### Onde Validamos

```
[Landing] → [Bronze] → [SILVER] ← VALIDACAO AQUI → [Gold] → [Curated]
                          ↓
                    [Auditoria]
```

**Por que Silver?**
- Bronze preserva dados brutos (historico imutavel)
- Silver e onde aplicamos regras de negocio
- Gold consome apenas dados validos do Silver

---

## Dimensoes de Qualidade

### 1. Completude (Completeness)

**Definicao**: Campos obrigatorios devem estar preenchidos.

**Validacoes**:
- Primary Keys nao nulas
- Campos criticos nao nulos (ex: nome, email)

**Exemplo**:
```python
flag_id_valido = F.col("cd_atendente").isNotNull()
flag_nome_valido = F.col("nm_atendente").isNotNull() & (F.length(F.col("nm_atendente")) > 1)
```

### 2. Consistencia (Consistency)

**Definicao**: Valores devem estar dentro de ranges aceitaveis.

**Validacoes**:
- Niveis de atendimento: 1 ou 2
- Notas CSAT: 1 a 5
- Idade: >= 0

**Exemplo**:
```python
flag_nivel_valido = (
    F.col("nu_nivel").isNotNull() &
    (F.col("nu_nivel") >= 1) &
    (F.col("nu_nivel") <= 2)
)
```

### 3. Unicidade (Uniqueness)

**Definicao**: Primary Keys devem ser unicas.

**Validacoes**:
- Deduplicacao por PK usando `.dropDuplicates()`

**Exemplo**:
```python
df_limpo = df_bronze.dropDuplicates(["cd_atendente"])
```

### 4. Conformidade (Conformity)

**Definicao**: Formatos devem seguir padroes esperados.

**Validacoes**:
- CPF: 11 digitos
- Email: conter @
- Telefone: formato valido

**Exemplo**:
```python
flag_email_valido = F.col("ds_email").contains("@")
```

### 5. Integridade Referencial (Referential Integrity)

**Definicao**: Foreign Keys devem referenciar registros existentes.

**Validacoes**:
- cd_atendente em tb_chamado deve existir em tb_atendente
- cd_cliente em tb_chamado deve existir em tb_cliente

---

## Implementacao - Camada Silver

### Processo de Validacao

Cada notebook `src/silver/src_tb_*.ipynb` segue este fluxo:

```
1. Ler Bronze (incremental: max(ingestion_timestamp))
2. Limpar (trim, conversoes, renomear)
3. Deduplicar por PK
4. Adicionar flags de validacao:
   - flag_id_valido
   - flag_nome_valido
   - flag_*_valido (especificos)
5. Calcular flag_qualidade:
   - "OK" se TODAS as flags = TRUE
   - "ERRO" se QUALQUER flag = FALSE
6. Split:
   - df_validos (flag_qualidade = "OK") → MERGE em tb_*
   - df_invalidos (flag_qualidade = "ERRO") → OVERWRITE em tb_*_invalidos
7. Salvar
```

### Exemplo Completo: tb_atendente

```python
df_validacao = (
    df_limpo
    .withColumn("flag_id_valido", F.col("cd_atendente").isNotNull())
    .withColumn("flag_nome_valido",
        F.col("nm_atendente").isNotNull() & (F.length(F.col("nm_atendente")) > 1)
    )
    .withColumn("flag_nivel_valido",
        F.col("nu_nivel").isNotNull() &
        (F.col("nu_nivel") >= 1) &
        (F.col("nu_nivel") <= 2)
    )
    .withColumn("flag_qualidade",
        F.when(
            F.col("flag_id_valido") &
            F.col("flag_nome_valido") &
            F.col("flag_nivel_valido"),
            F.lit("OK")
        ).otherwise(F.lit("ERRO"))
    )
)

df_validos = df_validacao.filter(F.col("flag_qualidade") == "OK")
df_invalidos = df_validacao.filter(F.col("flag_qualidade") == "ERRO")
```

---

## Tabelas de Auditoria

### Estrutura

Cada tabela de auditoria `tb_*_invalidos` contem:
- Todas as colunas da tabela principal
- Colunas de validacao: `flag_*_valido`
- Coluna `flag_qualidade`

**Exemplo**: `tb_atendente_invalidos`

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| cd_atendente | BIGINT | PK |
| nm_atendente | STRING | Nome |
| nu_nivel | SMALLINT | Nivel |
| dt_ingestion | TIMESTAMP | Data ingestao |
| dc_origem | STRING | Origem |
| flag_id_valido | BOOLEAN | Validacao de ID |
| flag_nome_valido | BOOLEAN | Validacao de nome |
| flag_nivel_valido | BOOLEAN | Validacao de nivel |
| flag_qualidade | STRING | "ERRO" sempre |

### Proposito

1. **Auditoria**: Rastrear quais registros foram rejeitados
2. **Analise de Causa**: Identificar qual regra falhou
3. **Correcao na Fonte**: Enviar relatorio para correcao no Supabase
4. **Metricas de Qualidade**: Calcular % de dados validos

---

## Regras de Validacao por Tabela

### tb_atendente

| Flag | Regra |
|------|-------|
| flag_id_valido | cd_atendente IS NOT NULL |
| flag_nome_valido | nm_atendente IS NOT NULL AND length > 1 |
| flag_nivel_valido | nu_nivel IN (1, 2) |

### tb_cliente

| Flag | Regra |
|------|-------|
| flag_id_valido | cd_cliente IS NOT NULL |
| flag_nome_valido | nm_cliente IS NOT NULL AND length > 1 |
| flag_idade_valida | nu_idade >= 0 |
| flag_cpf_valido | nu_cpf IS NOT NULL (pode adicionar regex) |

### tb_chamado

| Flag | Regra |
|------|-------|
| flag_id_valido | cd_chamado IS NOT NULL |
| flag_cliente_valido | cd_cliente IS NOT NULL |
| flag_canal_valido | cd_canal IS NOT NULL |
| flag_tempos_validos | tm_espera >= 0 AND tm_duracao >= 0 |

### tb_custo_chamado

| Flag | Regra |
|------|-------|
| flag_id_valido | cd_custo IS NOT NULL |
| flag_chamado_valido | cd_chamado IS NOT NULL |
| flag_custo_valido | vl_custo >= 0 |

### tb_pesquisa

| Flag | Regra |
|------|-------|
| flag_id_valido | cd_pesquisa IS NOT NULL |
| flag_chamado_valido | cd_chamado IS NOT NULL |
| flag_nota_valida | nu_nota BETWEEN 1 AND 5 |

---

### Detalhamento de Erros

```sql
-- Quais validacoes estao falhando mais?
SELECT
    CASE
        WHEN flag_id_valido = FALSE THEN 'ID Invalido'
        WHEN flag_nome_valido = FALSE THEN 'Nome Invalido'
        WHEN flag_nivel_valido = FALSE THEN 'Nivel Fora do Range'
        ELSE 'Outro'
    END AS tipo_erro,
    COUNT(*) AS qtd_ocorrencias
FROM v_credit.silver.tb_atendente_invalidos
GROUP BY tipo_erro
ORDER BY qtd_ocorrencias DESC
```

---

## Alertas e SLA

### Thresholds Recomendados

| Metrica | Threshold | Acao |
|---------|-----------|------|
| % Qualidade | < 95% | Alerta (warning) |
| % Qualidade | < 90% | Alerta (critical) + Investigacao |
| Qtd Invalidos | > 100 registros | Investigacao |
| Qtd Invalidos | Crescimento > 50% dia a dia | Alerta imediato |

### Implementacao de Alertas (Pseudocodigo)

```python
qtd_invalidos_hoje = spark.sql("SELECT COUNT(*) FROM tb_chamado_invalidos WHERE dt_ingestion = CURRENT_DATE").first()[0]
qtd_invalidos_ontem = spark.sql("SELECT COUNT(*) FROM tb_chamado_invalidos WHERE dt_ingestion = CURRENT_DATE - 1").first()[0]

if qtd_invalidos_hoje > qtd_invalidos_ontem * 1.5:
    enviar_alerta("Aumento anomalo de registros invalidos em tb_chamado")
```

---

## Correcao de Dados

### Processo de Correcao

1. **Identificar**: Query em `tb_*_invalidos` para listar registros problematicos
2. **Analisar**: Verificar qual flag esta FALSE
3. **Corrigir na Fonte**: Atualizar dados no Supabase
4. **Reprocessar**: Fivetran sincroniza → Bronze → Silver

### Exemplo de Query para Investigacao

```sql
-- Listar atendentes com nivel invalido
SELECT
    cd_atendente,
    nm_atendente,
    nu_nivel,
    flag_nivel_valido
FROM v_credit.silver.tb_atendente_invalidos
WHERE flag_nivel_valido = FALSE
```

Resultado:
```
cd_atendente | nm_atendente | nu_nivel | flag_nivel_valido
-------------|--------------|----------|-------------------
999          | João Silva   | 3        | FALSE
```

**Acao**: Atualizar no Supabase para `nu_nivel = 2`.

---

## Limpeza de Dados Comuns

### Padronizacao de Canais

**Problema**: Canais escritos de forma inconsistente.

**Solucao**:
```python
df_clean = df_bronze.withColumn(
    "nm_canal",
    F.upper(F.regexp_replace(F.col("canal"), "[^a-zA-Z]", ""))
)
```

**Resultado**:
- "chat bot", "ChatBot", "Chatbot" → "CHATBOT"
- "U.R.A", "ura", "URA" → "URA"

### Tratamento de Nulls

**Problema**: Campos numericos com NULL.

**Solucao**:
```python
df_clean = df_bronze.withColumn(
    "tm_espera",
    F.coalesce(F.col("tempo_espera"), F.lit(0))
)
```

### Remocao de Espacos

**Problema**: Nomes com espacos antes/depois.

**Solucao**:
```python
df_clean = df_bronze.withColumn(
    "nm_atendente",
    F.trim(F.col("nome_atendente"))
)
```

---

## Metricas de Qualidade

### KPIs de Qualidade

1. **Taxa de Qualidade** = (Registros Validos / Total) * 100
2. **Taxa de Rejeicao** = (Registros Invalidos / Total) * 100
3. **Tempo Medio de Correcao** = Tempo entre identificacao e correcao
4. **Recorrencia de Erros** = Mesmos registros falhando repetidamente

### Meta de Qualidade

- **Bronze**: 100% (aceita tudo da fonte)
- **Silver**: >= 95% de qualidade
- **Gold**: 100% (consome apenas Silver valido)

---

## Conclusao

A estrategia de qualidade implementada garante que:
- Problemas sao identificados rapidamente
- Dados ruins nao bloqueiam o pipeline
- Ha rastreabilidade completa
- Stakeholders tem visibilidade de qualidade

**Lembre-se**: Qualidade de dados e responsabilidade de todos, nao apenas do time de dados.
