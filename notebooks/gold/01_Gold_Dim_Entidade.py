# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Levantamento das entidades de receita e despesa
# MAGIC
# MAGIC Antes da construção da dimensão de entidades da camada Gold, será verificada a ocorrência das entidades presentes nas tabelas Silver de Faturamento e Fornecedores.
# MAGIC
# MAGIC O objetivo é identificar:
# MAGIC
# MAGIC - as entidades associadas ao faturamento, classificadas como entidades de **receita (R)**;
# MAGIC - as entidades associadas às despesas com fornecedores, classificadas como entidades de **despesa (D)**;
# MAGIC - a eventual existência de uma mesma entidade anonimizada nos dois conjuntos.
# MAGIC
# MAGIC Essa verificação é necessária para avaliar a utilização de uma dimensão única de entidades, reunindo clientes e fornecedores e distinguindo sua natureza por meio de um atributo de classificação.
# MAGIC
# MAGIC Nesta etapa será realizado apenas o levantamento dos dados existentes nas tabelas Silver, sem criação ou alteração de tabelas na camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH entidades_receita AS (
# MAGIC     SELECT DISTINCT
# MAGIC         TRIM(cliente) AS entidade
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC     WHERE cliente IS NOT NULL
# MAGIC       AND TRIM(cliente) <> ''
# MAGIC ),
# MAGIC
# MAGIC entidades_despesa AS (
# MAGIC     SELECT DISTINCT
# MAGIC         TRIM(fornecedor) AS entidade
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC     WHERE fornecedor IS NOT NULL
# MAGIC       AND TRIM(fornecedor) <> ''
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COALESCE(r.entidade, d.entidade) AS entidade,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN r.entidade IS NOT NULL AND d.entidade IS NOT NULL THEN 'R/D'
# MAGIC         WHEN r.entidade IS NOT NULL THEN 'R'
# MAGIC         WHEN d.entidade IS NOT NULL THEN 'D'
# MAGIC     END AS natureza_entidade
# MAGIC
# MAGIC FROM entidades_receita r
# MAGIC
# MAGIC FULL OUTER JOIN entidades_despesa d
# MAGIC     ON UPPER(r.entidade) = UPPER(d.entidade)
# MAGIC
# MAGIC ORDER BY
# MAGIC     natureza_entidade,
# MAGIC     entidade;

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Conclusão do Levantamento das entidades de receita e despesa
# MAGIC
# MAGIC O levantamento das entidades existentes nas tabelas Silver de Faturamento e Fornecedores identificou inicialmente **177 valores distintos** no conjunto formado pelos campos utilizados para identificação das entidades.
# MAGIC
# MAGIC Desse total:
# MAGIC
# MAGIC - **36 valores distintos** foram encontrados no campo de cliente da tabela Silver de Faturamento;
# MAGIC - **141 entidades distintas** foram encontradas na tabela Silver de Fornecedores;
# MAGIC - **nenhuma entidade anonimizada** aparece simultaneamente nos dois conjuntos.
# MAGIC
# MAGIC Entre os 36 valores provenientes do Faturamento foi identificado `CANCELAMENTO`. Esse valor não representa uma entidade de negócio. Ele é utilizado nos dados de origem para identificar notas fiscais canceladas, seja por solicitação do cliente ou em razão de erro na emissão.
# MAGIC
# MAGIC Por esse motivo, `CANCELAMENTO` não deverá compor a dimensão de entidades da camada Gold.
# MAGIC
# MAGIC Desconsiderando esse valor operacional, o conjunto destinado à dimensão é formado por:
# MAGIC
# MAGIC - **35 entidades de receita (`R`)**;
# MAGIC - **141 entidades de despesa (`D`)**;
# MAGIC - **176 entidades no total**.
# MAGIC
# MAGIC Não foi identificada nenhuma entidade anonimizada simultaneamente como receita e despesa. Dessa forma, no conjunto de dados disponível para o MVP, a classificação por natureza é inequívoca.
# MAGIC
# MAGIC O resultado sustenta a utilização de uma única dimensão na camada Gold, denominada `Dim_Entidade`, reunindo clientes e fornecedores e utilizando o atributo `natureza_entidade` para distinguir:
# MAGIC
# MAGIC - `R` — entidade associada à receita;
# MAGIC - `D` — entidade associada à despesa.
# MAGIC
# MAGIC A construção da dimensão deverá excluir o valor `CANCELAMENTO`, preservando nas tabelas relacionadas ao faturamento os registros de notas fiscais canceladas que sejam necessários às análises do MVP.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Construção da dimensão de entidades
# MAGIC
# MAGIC Após o levantamento das entidades existentes nas tabelas Silver de Faturamento e Fornecedores, será construída a dimensão `dim_entidade` na camada Gold.
# MAGIC
# MAGIC A dimensão reunirá em uma única estrutura as entidades associadas aos dois processos financeiros analisados no MVP:
# MAGIC
# MAGIC - entidades provenientes do Faturamento, classificadas com `natureza_entidade = 'R'`, correspondentes às entidades associadas à receita;
# MAGIC - entidades provenientes de Fornecedores, classificadas com `natureza_entidade = 'D'`, correspondentes às entidades associadas à despesa.
# MAGIC
# MAGIC O valor `CANCELAMENTO`, encontrado no campo de cliente do Faturamento, será excluído da dimensão porque não representa uma entidade de negócio. Os registros de notas fiscais canceladas permanecem preservados na tabela Silver de Faturamento e seu tratamento analítico será realizado posteriormente na modelagem do fato correspondente.
# MAGIC
# MAGIC A dimensão terá os seguintes atributos:
# MAGIC
# MAGIC - `id_entidade`: chave substituta da dimensão;
# MAGIC - `nome_entidade`: identificação anonimizada da entidade;
# MAGIC - `natureza_entidade`: classificação da entidade como receita (`R`) ou despesa (`D`).
# MAGIC
# MAGIC A chave `id_entidade` será criada na camada Gold e não corresponde a um identificador existente nos dados de origem.
# MAGIC
# MAGIC Com base no levantamento anterior, são esperadas **176 entidades**, sendo **35 de natureza `R`** e **141 de natureza `D`**.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.dim_entidade AS
# MAGIC
# MAGIC WITH entidades AS (
# MAGIC
# MAGIC     SELECT DISTINCT
# MAGIC         TRIM(cliente) AS nome_entidade,
# MAGIC         'R' AS natureza_entidade
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC     WHERE cliente IS NOT NULL
# MAGIC       AND TRIM(cliente) <> ''
# MAGIC       AND UPPER(TRIM(cliente)) <> 'CANCELAMENTO'
# MAGIC
# MAGIC     UNION
# MAGIC
# MAGIC     SELECT DISTINCT
# MAGIC         TRIM(fornecedor) AS nome_entidade,
# MAGIC         'D' AS natureza_entidade
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC     WHERE fornecedor IS NOT NULL
# MAGIC       AND TRIM(fornecedor) <> ''
# MAGIC ),
# MAGIC
# MAGIC entidades_identificadas AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY natureza_entidade, UPPER(nome_entidade)
# MAGIC         ) AS id_entidade,
# MAGIC         nome_entidade,
# MAGIC         natureza_entidade
# MAGIC     FROM entidades
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     id_entidade,
# MAGIC     nome_entidade,
# MAGIC     natureza_entidade
# MAGIC
# MAGIC FROM entidades_identificadas;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Validação da dimensão de entidades
# MAGIC
# MAGIC Após a criação da tabela `workspace.gold.dim_entidade`, será realizada a validação de sua estrutura e conteúdo.
# MAGIC
# MAGIC A verificação tem como objetivos confirmar:
# MAGIC
# MAGIC - a existência de **176 registros**, conforme o levantamento realizado anteriormente;
# MAGIC - a existência de **176 identificadores únicos** em `id_entidade`;
# MAGIC - a existência de **176 combinações distintas de nome e natureza**;
# MAGIC - a presença de **35 entidades de natureza `R`**;
# MAGIC - a presença de **141 entidades de natureza `D`**;
# MAGIC - a inexistência de valores diferentes de `R` e `D` em `natureza_entidade`;
# MAGIC - a inexistência de valores nulos nos atributos da dimensão;
# MAGIC - a inexistência do valor `CANCELAMENTO` na dimensão.
# MAGIC
# MAGIC Essa validação permitirá confirmar que a `dim_entidade` representa exclusivamente as entidades de negócio identificadas nas tabelas Silver de Faturamento e Fornecedores.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_entidades,
# MAGIC
# MAGIC     COUNT(DISTINCT id_entidade) AS ids_distintos,
# MAGIC
# MAGIC     COUNT(DISTINCT CONCAT(nome_entidade, '||', natureza_entidade))
# MAGIC         AS entidades_distintas,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN natureza_entidade = 'R'
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS entidades_receita,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN natureza_entidade = 'D'
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS entidades_despesa,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN natureza_entidade NOT IN ('R', 'D')
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS naturezas_invalidas,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN id_entidade IS NULL
# MAGIC               OR nome_entidade IS NULL
# MAGIC               OR natureza_entidade IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_com_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN UPPER(TRIM(nome_entidade)) = 'CANCELAMENTO'
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS cancelamento_na_dimensao
# MAGIC
# MAGIC FROM workspace.gold.dim_entidade;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Validação da dimensão de entidades
# MAGIC
# MAGIC A validação da tabela `workspace.gold.dim_entidade` confirmou a consistência da dimensão construída a partir das entidades existentes nas tabelas Silver de Faturamento e Fornecedores.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **176 entidades**;
# MAGIC - **176 identificadores distintos** em `id_entidade`;
# MAGIC - **176 combinações distintas de entidade e natureza**;
# MAGIC - **35 entidades de natureza `R`**, associadas à receita;
# MAGIC - **141 entidades de natureza `D`**, associadas à despesa;
# MAGIC - **0 registros com natureza diferente de `R` ou `D`**;
# MAGIC - **0 registros com valores nulos nos atributos da dimensão**;
# MAGIC - **0 ocorrências de `CANCELAMENTO` na dimensão**.
# MAGIC
# MAGIC A correspondência entre a quantidade total de registros, identificadores distintos e combinações distintas de entidade e natureza confirma a unicidade dos registros da dimensão.
# MAGIC
# MAGIC O valor `CANCELAMENTO`, utilizado na origem para identificar notas fiscais canceladas, foi corretamente excluído por não representar uma entidade de negócio.
# MAGIC
# MAGIC Dessa forma, a `dim_entidade` passa a constituir a dimensão Gold compartilhada para identificação das contrapartes associadas aos processos de receita e despesa, diferenciadas pelo atributo `natureza_entidade`.
# MAGIC
# MAGIC A construção e a validação da `dim_entidade` são consideradas concluídas.