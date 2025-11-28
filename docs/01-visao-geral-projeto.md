# Visao Geral do Projeto V-Credit

## Contexto de Negocio

A **V-Credit** e uma empresa de servicos financeiros que enfrenta desafios criticos em sua operacao de atendimento ao cliente. Este projeto de Data Lakehouse foi desenvolvido para fornecer insights acionaveis que permitam a tomada de decisoes estrategicas baseadas em dados.

## Objetivos do Projeto

### Objetivo Principal
Implementar uma arquitetura de dados moderna (Medallion Architecture) que permita:
- Monitoramento em tempo real da satisfacao do cliente (CSAT)
- Analise de custos operacionais do atendimento
- Otimizacao da alocacao de recursos humanos e tecnologicos
- Identificacao de oportunidades de automacao

### Objetivos Especificos

1. **Visao Financeira**
   - Identificar despesas excessivas no atendimento
   - Calcular o potencial de economia com automacao
   - Analisar custo por canal de atendimento

2. **Visao de Experiencia do Cliente (CX)**
   - Monitorar a evolucao do CSAT
   - Correlacionar tempo de espera com satisfacao
   - Identificar pontos criticos na jornada do cliente

3. **Visao Operacional**
   - Medir tempos de espera e atendimento
   - Avaliar desempenho por canal (Bot vs. Humano)
   - Otimizar distribuicao de carga entre niveis de atendimento

4. **Visao Tecnologica**
   - Medir efetividade do chatbot
   - Identificar taxas de transbordo (bot → humano)
   - Segmentar problemas por perfil demografico

## Dores de Negocio Identificadas

### 1. Custos Elevados (Gerente Financeiro)
**Problema**: "Os custos do atendimento tem contribuido de forma significativa nas despesas. Precisamos cortar essa despesa excessiva."

### 2. Queda na Satisfacao (Diretora de Marketing)
**Problema**: "O coeficiente de satisfacao era 85%, mas sentimos uma piora recente. Fatores externos?"

### 3. Filas Longas (Coordenadora de CS)
**Problema**: "Alto tempo medio de atendimento. Muitos clientes aguardam mais do que o esperado. Atendentes nao capacitados."


### 4. Chatbot Ineficaz (Diretor de TI)
**Problema**: "Nosso chatbot nao resolve a maior parte das solicitacoes. Muitos usuarios sao analfabetos digitais."

## Stakeholders

| Stakeholder | Area | Interesse Principal |
|-------------|------|---------------------|
| Gerente Financeiro | Financeiro | Reducao de custos operacionais |
| Diretora de Marketing | CX/Marketing | Melhoria da satisfacao do cliente |
| Coordenadora de CS | Customer Success | Otimizacao de processos operacionais |
| Diretor de TI | Tecnologia | Efetividade da automacao |


### Entregas do Projeto

1. **Data Lakehouse**: Arquitetura completa Bronze → Silver → Gold → Curated
2. **Dashboard Power BI**: Visualizacoes acionaveis para cada stakeholder
3. **Modelo Dimensional**: Star Schema otimizado para analytics
4. **Qualidade de Dados**: Sistema de auditoria e validacao automatica

## Tecnologias Utilizadas

- **Banco de Dados Origem**: Supabase (PostgreSQL)
- **ETL**: Fivetran (ingestao automatizada)
- **Data Platform**: Databricks (Delta Lake + PySpark)
- **Storage**: Delta Lake (formato ACID para lakehouse)
- **BI**: Power BI (dashboards e relatorios)
- **Orquestracao**: Databricks Workflows (notebooks)

## Proximos Passos

1. Leia a [Arquitetura de Dados](./02-arquitetura-dados.md) para entender o fluxo end-to-end
2. Consulte o [Modelo de Dados](./03-modelo-dados.md) para detalhes das tabelas
3. Veja o [Caso de Negocio](./04-caso-negocio.md) para entender as analises implementadas
