{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# \ud83d\udee0\ufe0f Pipeline de Ingest\u00e3o: Landing Zone \u2192 Bronze Layer\n",
    "\n",
    "Este notebook \u00e9 respons\u00e1vel pela ingest\u00e3o de dados brutos da **Landing Zone** (Cat\u00e1logo: `v_credit`, Schema: `postgres_public`) para a camada **Bronze**.\n",
    "\n",
    "## \ud83c\udfdba Arquitetura e Decis\u00f5es de Governan\u00e7a\n",
    "\n",
    "### 1. Integra\u00e7\u00e3o via Fivetran (Supabase \u2192 Landing)\n",
    "A camada de Landing n\u00e3o \u00e9 alimentada diretamente por scripts *custom*, mas sim atrav\u00e9s de uma integra\u00e7\u00e3o gerenciada pelo **Fivetran** conectada ao banco transacional **Supabase**.\n",
    "\n",
    "**Benef\u00edcios desta abordagem:**\n",
    "- **Confiabilidade:** O Fivetran gerencia automaticamente retries, *backpressure* e mudan\u00e7as de esquema (Schema Drift) na origem.\n",
    "- **Menor Manuten\u00e7\u00e3o:** Removemos a necessidade de manter *connectors* complexos de banco de dados na camada de engenharia (`src`), delegando a extra\u00e7\u00e3o para uma ferramenta especializada.\n",
    "- **Log-based CDC:** Garante que todas as transa\u00e7\u00f5es do Supabase sejam capturadas sem onerar o banco de produ\u00e7\u00e3o.\n",
    "\n",
    "### 2. Estrutura do Projeto (`src` vs `ddl`)\n",
    "Seguindo nossos padr\u00f5es de governança de c\u00f3digo:\n",
    "- **`src/` (Source):** Onde este notebook reside. Cont\u00e9m apenas a **l\u00f3gica de orquestra\u00e7\u00e3o e transforma\u00e7\u00e3o**.\n",
    "- **`ddl/` (Data Definition Language):** As defini\u00e7\u00f5es das tabelas, schemas e *constraints* s\u00e3o versionadas separadamente. Isso desacopla a regra de neg\u00f3cio (pipeline) da estrutura f\u00edsica dos dados.\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "inputWidgets": {},
     "nuid": "9b9f15a1-72bb-4861-915a-c9d2fa71bbb5",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": [
    "from pyspark.sql.functions import current_timestamp, lit\n",
    "from pyspark.sql import functions as F\n",
    "from datetime import datetime\n",
    "\n",
    "CATALOGO_ORIGEM = \"v_credit\"\n",
    "SCHEMA_ORIGEM = \"postgres_public\"\n",
    "CATALOGO_DESTINO = \"v_credit\"\n",
    "SCHEMA_DESTINO = \"bronze\"\n",
    "ORIGEM_DADOS = \"supabase\""
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 3. Mapeamento de Tabelas\n",
    "Dicion\u00e1rio centralizado para mapear as tabelas de origem (Postgres/Supabase) para seus respectivos destinos na camada Bronze. Isso facilita a inclus\u00e3o de novas tabelas no pipeline sem alterar a l\u00f3gica de ingest\u00e3o."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "inputWidgets": {},
     "nuid": "f0f72eee-8198-40a5-9aff-408baa90729e",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": [
    "tabelas_postgres = {\n",
    "    \"base_atendentes\": \"base_atendentes\",\n",
    "    \"base_motivos\": \"base_motivos\",\n",
    "    \"canais\": \"canais\",\n",
    "    \"chamados\": \"chamados\",\n",
    "    \"chamados_hora\": \"chamados_hora\",\n",
    "    \"clientes\": \"clientes\",\n",
    "    \"custos\": \"custos\",\n",
    "    \"pesquisa_satisfacao\": \"pesquisa_satisfacao\"\n",
    "}"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 4. Execu\u00e7\u00e3o da Ingest\u00e3o e Rastreabilidade\n",
    "\n",
    "O loop abaixo itera sobre as tabelas mapeadas e realiza a carga *full-overwrite* para a camada Bronze.\n",
    "\n",
    "#### \u23f1\ufe0f Estrat\u00e9gia de Timestamp (Lineage do Lote)\n",
    "**Decis\u00e3o de Governan\u00e7a:** A vari\u00e1vel `timestamp_carga` (ou a l\u00f3gica de *current_timestamp*) \u00e9 utilizada para marcar o momento exato da ingest\u00e3o.\n",
    "\n",
    "> **Nota de Design:** Idealmente, ao tratar o processamento como um lote \u00fanico, o `time_stamp` funciona como um identificador do **Batch ID**. Mesmo que calculado tecnicamente pr\u00f3ximo \u00e0 execu\u00e7\u00e3o (dentro ou fora do loop), o conceito governado aqui \u00e9 garantir que cada registro na camada Bronze possua um carimbo de auditoria (`ingestion_timestamp`) que permita rastrear quando aquele dado foi efetivamente materializado no Data Lake."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "inputWidgets": {},
     "nuid": "59f1cc53-aef2-4de7-b0e1-e578152fa0e2",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": [
    "for tabela_origem, tabela_destino in tabelas_postgres.items():\n",
    "    \n",
    "    full_source_table = f\"{CATALOGO_ORIGEM}.{SCHEMA_ORIGEM}.{tabela_origem}\"\n",
    "    full_target_table = f\"{CATALOGO_DESTINO}.{SCHEMA_DESTINO}.{tabela_destino}\"\n",
    "\n",
    "    timestamp_carga = F.current_timestamp()\n",
    "    \n",
    "    try:\n",
    "        print(f\"Iniciando ingestão da tabela: '{full_source_table}'\")\n",
    "        \n",
    "        df = spark.read.table(full_source_table)\n",
    "        \n",
    "        df = df.withColumn(\"ingestion_timestamp\", lit(timestamp_carga))\n",
    "        df = df.withColumn(\"origem\", lit(ORIGEM_DADOS))\n",
    "\n",
    "        df.write.mode(\"overwrite\").saveAsTable(full_target_table)\n",
    "        \n",
    "        print(f\"✅ Tabela '{full_target_table}' carregada com sucesso!\")\n",
    "        \n",
    "    except Exception as e:\n",
    "        print(f\"❌ Erro ao processar tabela '{full_target_table}': {str(e)}\\n\")"
   ]
  }
 ],
 "metadata": {
  "application/vnd.databricks.v1+notebook": {
   "computePreferences": null,
   "dashboards": [],
   "environmentMetadata": {
    "base_environment": "",
    "environment_version": "4"
   },
   "inputWidgetPreferences": null,
   "language": "python",
   "notebookMetadata": {
    "pythonIndentUnit": 4
   },
   "notebookName": "ingestion_landing_to_bronze",
   "widgets": {}
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}