# Modelo de Dados - V-Credit Lakehouse

## Convencoes de Nomenclatura

### Prefixos de Colunas
- `cd_` = Codigo/ID (BIGINT)
- `nm_` = Nome (STRING/VARCHAR)
- `ds_` = Descricao (STRING/VARCHAR)
- `dt_` = Data (DATE/TIMESTAMP)
- `dh_` = Data/Hora (TIMESTAMP)
- `dc_` = Descricao de metadata (STRING)
- `st_` = Status (BOOLEAN/SMALLINT)
- `tm_` = Tempo em segundos (BIGINT)
- `nu_` = Numero (SMALLINT/INT)
- `vl_` = Valor monetario (DECIMAL)
- `fl_` = Flag booleana (SMALLINT 0/1)
- `val_` = Valor de metrica (numerica)
- `pk_` = Primary Key surrogate

### Prefixos de Tabelas
- **Bronze**: Nome original da fonte (ex: `chamados`, `clientes`)
- **Silver**: `tb_<entidade>` (ex: `tb_chamado`, `tb_cliente`)
- **Silver Auditoria**: `tb_<entidade>_invalidos`
- **Gold Dimensao**: `dm_<entidade>` (ex: `dm_atendente`)
- **Gold Fato**: `ft_<processo>` (ex: `ft_atendimento_geral`)
- **Curated Views**: `vw_<objeto>` (ex: `vw_dm_cliente`)

## Camada Bronze

### Tabelas Bronze

Todas as tabelas Bronze seguem o mesmo padrao:
- Schema original da fonte **preservado**
- Adicao de **2 colunas de metadata**

#### Colunas de Metadata (Padrao)
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| ingestion_timestamp | TIMESTAMP | Timestamp da carga no Bronze |
| origem | STRING | Identificador da origem (ex: "supabase") |

#### Lista de Tabelas Bronze

1. **base_atendentes**
   - Origem: Supabase `base_atendentes`
   - Registros: ~20 funcionarios
   - PK: id_atendente

2. **base_motivos**
   - Origem: Supabase `base_motivos`
   - Registros: ~13 motivos
   - PK: id_motivo

3. **canais**
   - Origem: Supabase `canais`
   - Registros: ~6 canais

4. **chamados**
   - Origem: Supabase `chamados`
   - Registros: Volumetria transacional (milhares)
   - Campos: id_chamado, id_cliente, motivo, canal, resolvido, tempos, id_atendente

5. **chamados_hora**
   - Origem: Supabase `chamados_hora` (via CSV historico)
   - Campos: Timestamps de abertura, inicio e fim

6. **clientes**
   - Origem: Supabase `clientes`
   - Registros: Base de clientes
   - PK: id_cliente

7. **custos**
   - Origem: Supabase `custos`
   - Campos: id_custo, id_chamado, custo

8. **pesquisa_satisfacao**
   - Origem: Supabase `pesquisa_satisfacao`
   - Campos: id_pesquisa, id_chamado, nota_atendimento

## Camada Silver

### Tabela: tb_atendente

**Proposito**: Cadastro limpo e validado de atendentes.

| Coluna | Tipo | PK | Descricao |
|--------|------|----|-----------||
| cd_atendente | BIGINT | ✓ | Identificador unico do atendente |
| nm_atendente | STRING | | Nome completo do funcionario |
| nu_nivel | SMALLINT | | Nivel de senioridade (1 ou 2) |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem do dado |

**Regras de Validacao**:
- cd_atendente NOT NULL
- nm_atendente NOT NULL e length > 1
- nu_nivel entre 1 e 2

### Tabela: tb_cliente

| Coluna | Tipo | PK | Descricao |
|--------|------|----| ---|
| cd_cliente | BIGINT | ✓ | Identificador unico |
| nu_cpf | STRING | | CPF do cliente |
| nm_cliente | VARCHAR(150) | | Nome completo |
| ds_email | VARCHAR(150) | | Email |
| nm_regiao | VARCHAR(50) | | Regiao geografica |
| nu_idade | SMALLINT | | Idade |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Regras de Validacao**:
- cd_cliente NOT NULL
- nm_cliente NOT NULL e length > 1
- nu_idade >= 0

### Tabela: tb_canal

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_canal | BIGINT | ✓ | ID gerado automaticamente |
| nm_canal | VARCHAR(50) | | Nome do canal (padronizado) |
| st_ativo | BOOLEAN | | Status ativo/inativo |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Padronizacao**:
- Nomes de canais sao normalizados (ex: "chat bot", "ChatBot", "Chatbot" → "CHATBOT")

### Tabela: tb_motivo

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_motivo | BIGINT | ✓ | ID do motivo |
| ds_motivo | VARCHAR(100) | | Descricao do motivo |
| ds_categoria | VARCHAR(50) | | Categoria macro |
| ds_criticidade | SMALLINT | | Nivel de criticidade |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Valores de Criticidade**:
- "Baixa": Motivos automatizaveis (ex: Consulta Saldo, 2a Via Boleto)
- "Media": Requer atencao moderada
- "Alta": Urgente (ex: Compra nao autorizada, Bloqueio)

### Tabela: tb_chamado

**Proposito**: Fato transacional principal de tickets de atendimento.

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_chamado | BIGINT | ✓ | ID do chamado |
| cd_cliente | BIGINT | | FK para cliente |
| ds_motivo_rel | STRING | | Motivo relatado (texto livre) |
| cd_canal | BIGINT | | FK para canal |
| st_resolvido | BOOLEAN | | Resolvido (Sim/Nao) |
| tm_espera | BIGINT | | Tempo em fila (segundos) |
| tm_duracao | BIGINT | | Duracao do atendimento (segundos) |
| cd_atendente | BIGINT | | FK para atendente (NULL se Bot) |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Regras de Negocio**:
- `cd_atendente` e NULL quando atendido por Bot
- `tm_espera` = 0 para atendimentos Bot (instantaneo)
- `st_resolvido` = TRUE indica ticket fechado com sucesso

### Tabela: tb_chamado_log

**Proposito**: Log de timestamps detalhados de cada chamado.

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_chamado | BIGINT | ✓ | ID do chamado |
| cd_cliente | BIGINT | | FK para cliente |
| dh_abertura | TIMESTAMP | | Timestamp de abertura |
| dh_inicio | TIMESTAMP | | Timestamp de inicio do atendimento |
| dh_fim | TIMESTAMP | | Timestamp de finalizacao |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Uso**: Permite calcular metricas temporais e analises de horario de pico.

### Tabela: tb_custo_chamado

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_custo | BIGINT | ✓ | ID do custo |
| cd_chamado | BIGINT | | FK para chamado |
| vl_custo | DECIMAL(12,10) | | Valor monetario preciso |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**Importante**: DECIMAL(12,10) garante precisao monetaria.

### Tabela: tb_pesquisa

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_pesquisa | BIGINT | ✓ | ID da pesquisa |
| cd_chamado | BIGINT | | FK para chamado |
| nu_nota | SMALLINT | | Nota de 1 a 5 |
| dt_ingestion | TIMESTAMP | | Data de ingestao |
| dc_origem | STRING | | Origem |

**CSAT**: Nota 1-5 (1 = Muito Insatisfeito, 5 = Muito Satisfeito)

### Tabelas de Auditoria (*_invalidos)

Cada tabela Silver possui uma correspondente `tb_<entidade>_invalidos` que contem:
- Todas as colunas da tabela principal
- Colunas adicionais de validacao: `flag_*_valido`
- Coluna `flag_qualidade` (OK ou ERRO)

**Exemplo**: `tb_atendente_invalidos`
- Campos extras: `flag_id_valido`, `flag_nome_valido`, `flag_nivel_valido`, `flag_qualidade`

## Camada Gold (Star Schema)

### Dimensoes

#### dm_atendente

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_atendente | BIGINT | ✓ | Codigo do funcionario |
| nm_atendente | STRING | | Nome |
| nu_nivel | SMALLINT | | Nivel (1 ou 2) |
| ds_perfil | STRING | | "Generalista (N1)" ou "Especialista (N2)" |

**Derivacao**: `ds_perfil` e gerado a partir de `nu_nivel`.

#### dm_cliente

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_cliente | STRING | ✓ | ID do cliente (STRING para flexibilidade) |
| nm_cliente | STRING | | Nome |
| ds_email | STRING | | Email |
| nm_regiao | STRING | | Regiao |
| nu_idade | SMALLINT | | Idade |
| ds_faixa_etaria | STRING | | "Jovem (18-35)", "Adulto (36-59)", "Senior (60+)" |

**Derivacao**: `ds_faixa_etaria` e calculado a partir de `nu_idade`.

#### dm_canal

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_canal | BIGINT | ✓ | Codigo do canal |
| nm_canal | STRING | | Nome do canal |
| st_ativo | BOOLEAN | | Status |
| ds_tipo_interacao | STRING | | "Automatizado" (Bot) ou "Humanizado" (N1/N2) |

**Derivacao**: `ds_tipo_interacao` classifica canais.

#### dm_motivo

| Coluna | Tipo | PK | Descricao |
|--------|------|----|----|
| cd_motivo | BIGINT | ✓ | Codigo do motivo |
| ds_motivo | STRING | | Descricao |
| ds_categoria | STRING | | Categoria |
| ds_criticidade | STRING | | "Baixa", "Media" ou "Alta" |
| ds_potencial_automacao | STRING | | "Alto", "Medio" ou "Baixo" |

**Derivacao**: `ds_potencial_automacao` mapeado a partir de `ds_criticidade`.

### Fatos

#### ft_atendimento_geral

**Proposito**: Fato principal com todas as metricas de atendimento.

| Coluna | Tipo | PK | FK | Descricao |
|--------|------|----|----|-----------|
| pk_fato_atendimento | STRING | ✓ | | Hash MD5 (surrogate key) |
| cd_cliente | STRING | | ✓ | FK para dm_cliente |
| cd_motivo | BIGINT | | ✓ | FK para dm_motivo |
| cd_canal | BIGINT | | ✓ | FK para dm_canal |
| cd_atendente | BIGINT | | ✓ | FK para dm_atendente |
| cd_chamado | BIGINT | | | Degenerate Dimension |
| dt_referencia | DATE | | | Data do fato |
| nu_hora_dia | SMALLINT | | | Hora (0-23) |
| val_tempo_espera | BIGINT | | | Metrica: Espera (seg) |
| val_tempo_atendimento | BIGINT | | | Metrica: Duracao (seg) |
| val_custo | DECIMAL(12,10) | | | Metrica: Custo unitario |
| val_nota_csat | SMALLINT | | | Metrica: Nota (1-5) |
| st_resolvido | SMALLINT | | | Flag 0/1 |
| fl_experiencia_negativa | SMALLINT | | | Flag: Espera > 5min OU Nota <= 2 |

**Regra de Negocio**: `fl_experiencia_negativa` = 1 quando:
- `val_tempo_espera` > 300 segundos (5 minutos) OU
- `val_nota_csat` <= 2

#### ft_custo_operacional

**Proposito**: Fato focado em analise de custos.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| pk_fato_custo | STRING | Hash MD5 |
| cd_motivo | BIGINT | FK |
| cd_canal | BIGINT | FK |
| dt_referencia | DATE | Data |
| val_custo_total | DECIMAL(12,10) | Soma de custos |
| qtd_chamados | BIGINT | Contagem |
| val_custo_medio | DECIMAL(12,10) | Media |

#### ft_performance_agente

**Proposito**: Metricas de desempenho individual.

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| pk_fato_performance | STRING | Hash MD5 |
| cd_atendente | BIGINT | FK |
| dt_referencia | DATE | Data |
| qtd_atendimentos | BIGINT | Total atendimentos |
| val_tempo_medio_atendimento | DECIMAL(10,2) | Media de duracao |
| val_csat_medio | DECIMAL(3,2) | Media de satisfacao |
| qtd_resolvidos | BIGINT | Chamados fechados |
| pct_taxa_resolucao | DECIMAL(5,2) | % Resolvidos |

## Relacionamentos (Star Schema)

```
        dm_atendente
               |
               |
        dm_cliente ← ft_atendimento_geral → dm_canal
               |            |
               |            |
        dm_motivo          dm_chamado
```

## Camada Curated

Views 1:1 que expõem as tabelas Gold:

- `vw_dm_atendente` → `dm_atendente`
- `vw_dm_cliente` → `dm_cliente`
- `vw_dm_canal` → `dm_canal`
- `vw_dm_motivo` → `dm_motivo`
- `vw_ft_atendimento_geral` → `ft_atendimento_geral`
- `vw_ft_custo_operacional` → `ft_custo_operacional`
- `vw_ft_performance_agente` → `ft_performance_agente`

## Dicionario de Dados Resumido

### Valores de Dominio

**nu_nivel** (Nivel de Atendimento):
- `1` = Generalista (Atendimento Inicial)
- `2` = Especialista (Atendimento Especializado)

**Canais Padronizados**:
- "CHATBOT" (automatizado)
- "URA" (automatizado)
- "ATENDIMENTO INICIAL" (humano N1)
- "ATENDIMENTO ESPECIALIZADO" (humano N2)

**Criticidade**:
- "Baixa": Consultas simples, automatizaveis
- "Media": Requer analise moderada
- "Alta": Urgencia (fraude, bloqueios)

**Status Resolvido**:
- `TRUE` / `1` = Ticket fechado com sucesso
- `FALSE` / `0` = Ticket nao resolvido ou abandonado
