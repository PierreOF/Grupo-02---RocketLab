# Caso de Negocio - V-Credit

## Objetivo

Conectar as dores de negocio relatadas pelos stakeholders da V-Credit com evidencias extraidas da base de dados, demonstrando como a arquitetura de Data Lakehouse fornece insights acionaveis para tomada de decisao.

## Contexto do Negocio

A V-Credit e uma fintech que oferece servicos de credito e cartoes. A empresa enfrenta desafios criticos em sua operacao de atendimento ao cliente, com impactos diretos em:
- **Custos operacionais** elevados
- **Satisfacao do cliente** em queda
- **Eficiencia operacional** comprometida
- **Automacao** sub-utilizada

Este documento mapeia como os dados respondem a cada dor de negocio.

---

## 1. Visao Financeira (Gerente Financeiro)

### A Dor Relatada

> "Os custos do atendimento tem contribuido de forma significativa nas despesas. Precisamos cortar essa despesa excessiva."

### O que os Dados Mostram (Evidencia na Base)

Ao analisar a tabela **`ft_custo_operacional`** cruzada com **`dm_motivo`**:

**Descobertas**:
1. Uma grande parcela do custo total vem de motivos de **Baixa Criticidade**
   - Exemplos: "Consulta de Saldo", "Consulta de Limite"
2. Esses motivos simples estao sendo atendidos por **canais humanos** (Nivel 1 e 2)
3. O custo unitario do atendimento humano e **drasticamente maior** que o do Bot
4. O volume de motivos automatizaveis no canal humano ainda e **muito alto**

**Metricas**:
- **Custo Total (amostra)**: ~R$ 12.800,00
- **Desperdicio Identificado**: ~R$ 3.760,00
  - Dinheiro gasto com motivos simples em canais caros
- **Economia Potencial**: **29,3%** do orcamento

### O Grafico para o BI (A Prova)

**Visual**: Grafico de Barras Horizontais (Pareto)

**Configuracao**:
- **Eixo Y**: Motivos (`ds_motivo`)
- **Eixo X**: Custo Total (`val_custo_total`)
- **Destaque**: Pintar de **Vermelho** as barras de motivos automatizaveis

**Insight para Stakeholder**:
> "Se automatizarmos os Top 3 motivos, economizamos **29% do orcamento de atendimento**."

**Tabelas Utilizadas**:
- `v_credit.gold.ft_custo_operacional`
- `v_credit.gold.dm_motivo`

---

## 2. Visao de Experiencia / CX (Diretora de Marketing)

### A Dor Relatada

> "O coeficiente de satisfacao era 85%, mas sentimos uma piora recente. Fatores externos?"

### O que os Dados Mostram (Evidencia na Base)

Ao analisar a **`ft_atendimento_geral`**:

**Descobertas**:
1. A media de **CSAT caiu drasticamente** (de 4.25 para 2.98)
2. Existe uma **correlacao inversa perfeita**: Quando o tempo de espera sobe, a nota desce
3. O problema **nao e externo** (mercado), e **interno** (Fila)
4. A metrica **% Experiencia Negativa** (Espera > 5min OU Nota <= 2) esta alarmante

**Metricas**:
- **CSAT Atual**: 2.98 / 5.0
  - Queda brusca em relacao aos 85% (ou 4.25) historicos
- **Clientes Insatisfeitos**: **48,7%**
  - Quase metade da base esta tendo experiencia ruim

### O Grafico para o BI (A Prova)

**Visual 1**: Cartao KPI com a nota CSAT atual

**Visual 2**: Grafico de Linha de Tendencia
- **Eixo X**: Tempo de Espera (agrupado em buckets: 0-2min, 2-5min, 5-10min, 10min+)
- **Eixo Y**: CSAT Medio

**Insight para Stakeholder**:
> "Diretora, a queda nao e externa. **48% dos clientes estao esperando tempo demais**. Quando a espera passa de 5 minutos, o CSAT despenca para 2.0."

**Tabelas Utilizadas**:
- `v_credit.gold.ft_atendimento_geral`

---

## 3. Visao Operacional / CS (Coordenadora de CS)

### A Dor Relatada

> "Alto tempo medio de atendimento. Muitos clientes aguardam mais do que o esperado. Atendentes nao capacitados."

### O que os Dados Mostram (Evidencia na Base)

Na analise de **`ft_atendimento_geral`** cruzado com **`dm_canal`**:

**Descobertas**:
1. A **media global de espera e "mentirosa"** (baixa) porque os Bots atendem em 0 segundos
2. Quando filtramos apenas `ds_tipo_interacao = 'Humanizado'`, a **fila explode**
3. A equipe **Nivel 2 esta gastando tempo** com coisas que o Nivel 1 ou Bot deveriam resolver

**Metricas**:
- **Espera no Bot**: 00:00 (Imediato)
- **Espera no Humano**: **~08:37** (517 segundos)

### O Grafico para o BI (A Prova)

**Visual**: Grafico de Colunas Comparativo

**Configuracao**:
- **Categorias**: Chatbot vs. Humano
- **Metrica**: Tempo Medio de Espera

**Insight para Stakeholder**:
> "O cliente espera **quase 9 minutos** para falar com alguem. Isso quebra a operacao."

**Tabelas Utilizadas**:
- `v_credit.gold.ft_atendimento_geral`
- `v_credit.gold.dm_canal`

---

## 4. Visao de Tecnologia (Diretor de TI)

### A Dor Relatada

> "Nosso chatbot nao resolve a maior parte das solicitacoes. Muitos usuarios sao analfabetos digitais."

### O que os Dados Mostram (Evidencia na Base)

Analisando a transicao de canais e a **`dm_cliente`**:

**Descobertas**:
1. Existe um **alto volume de chamados que iniciam no Digital** mas terminam com um `cd_atendente` preenchido (**Transbordo**)
2. Ao cruzar com `ds_faixa_etaria`, vemos que o publico **Senior (60+)** tem a **maior taxa de abandono** do canal digital

**Metricas**:
- **Taxa de Transbordo**: **38%**
  - De cada 10 chamados no bot, 4 ele falha e joga pro humano
- **Faixa Etaria Critica**: Seniors (60+)

### O Grafico para o BI (A Prova)

**Visual 1**: Grafico de Rosca (Pizza)
- **Metrica**: Taxa de Transbordo (Bot → Humano)

**Visual 2**: Grafico de Barras
- **Eixo X**: Faixa Etaria
- **Eixo Y**: Volume de Transbordo

**Insight para Stakeholder**:
> "Precisamos simplificar a URA/Bot para os idosos, pois eles representam a **maior fuga para o humano**."

**Tabelas Utilizadas**:
- `v_credit.gold.ft_atendimento_geral`
- `v_credit.gold.dm_cliente`
- `v_credit.gold.dm_canal`

---

## Resumo da Estrategia para Apresentacao

### Ordem Logica para Contar a Historia

Apresente os graficos nesta sequencia para construir a narrativa:

#### 1. O Choque (CX)
**Impacto Emocional Primeiro**

> "Nossa nota caiu para **2.98** porque **48% dos clientes sofrem na fila**."

**Visual**: KPI Card + Linha de Tendencia (CSAT vs Tempo Espera)

#### 2. A Causa (Operacional/Tech)
**Explique o Problema Raiz**

> "A fila humana e de **9 minutos** porque o Bot falha em **38% das vezes** (Transbordo)."

**Visual**: Colunas Comparativas (Bot vs Humano) + Rosca de Transbordo

#### 3. O Dinheiro (Financeiro)
**Feche com o Business Case**

> "Isso gera um desperdicio de **R$ 3.760** (na amostra) atendendo coisas simples. Se automatizarmos o 'Top 3 Motivos', economizamos **29% do orcamento**."

**Visual**: Pareto de Custos por Motivo

---

## Plano de Acao Recomendado

Com base nas evidencias dos dados:

### Curto Prazo (1-3 meses)
1. **Automatizar Top 3 Motivos**
   - Consulta de Saldo
   - Consulta de fatura
   - Consulta de Limite
2. **Melhorar UX do Chatbot para Seniors**
   - Simplificar menu de opcoes
   - Adicionar opcao de voz
3. **Redistribuir Carga**
   - Nao rotear motivos simples para Nivel 2

### Medio Prazo (3-6 meses)
1. **Implementar Callback**
   - Evitar fila > 5min oferecendo callback
2. **Treinar Nivel 1**
   - Capacitar para resolver motivos que estao indo pro N2
3. **Dashboard de Monitoramento**
   - CSAT em tempo real
   - Alerta quando fila > 5min

### Longo Prazo (6-12 meses)
1. **IA Conversacional**
   - Substituir URA rigida por NLP
2. **Proatividade**
   - Detectar insatisfacao antes do ticket
3. **Self-Service Portal**
   - Portal web para resolver tudo online
