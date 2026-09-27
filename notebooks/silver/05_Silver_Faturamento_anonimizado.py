# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da tabela Silver de Faturamento
# MAGIC
# MAGIC A tabela Silver de Faturamento é construída a partir de `workspace.bronze.faturamento_anonimizado`.
# MAGIC
# MAGIC Na passagem da camada Bronze para a Silver serão mantidos apenas os atributos necessários para representar a identificação da nota fiscal, sua associação aos códigos de resultado (CR), cliente, competência, emissão, vencimento e respectivos valores financeiros.
# MAGIC
# MAGIC ## Critério de validade dos registros
# MAGIC
# MAGIC Para o escopo do MVP, somente registros com `NF` preenchida são considerados registros válidos de faturamento.
# MAGIC
# MAGIC As linhas sem identificação de nota fiscal são descartadas antes das demais transformações, pois não representam um faturamento individualizável para as análises previstas.
# MAGIC
# MAGIC O diagnóstico realizado na camada Bronze identificou:
# MAGIC
# MAGIC - **5.128 registros** na fonte;
# MAGIC - **4.157 registros com NF preenchida**;
# MAGIC - **971 registros sem NF**, que não serão transportados para a Silver.
# MAGIC
# MAGIC ## Atributos selecionados
# MAGIC
# MAGIC Foram selecionados os seguintes atributos:
# MAGIC
# MAGIC - `NF` → `nf`;
# MAGIC - `CR1` → `cr1`;
# MAGIC - `CR2` → `cr2`;
# MAGIC - `CR3` → `cr3`;
# MAGIC - `CR4` → `cr4`;
# MAGIC - `Emissão` → `data_emissao`;
# MAGIC - `Competência` → `data_competencia`;
# MAGIC - `Cliente` → `cliente`;
# MAGIC - `Valor` → `valor`;
# MAGIC - `Vencimento` → `data_vencimento`;
# MAGIC - `VALOR ISS 2` → `valor_iss_2`;
# MAGIC - `VALOR ISS 5` → `valor_iss_5`;
# MAGIC - `Líquido` → `valor_liquido`;
# MAGIC - `Retenção IR` → `retencao_ir`;
# MAGIC - `Retenção PIS` → `retencao_pis`;
# MAGIC - `Retenção COFINS` → `retencao_cofins`;
# MAGIC - `Retenção CSSL` → `retencao_cssl`.
# MAGIC
# MAGIC Os campos financeiros são convertidos para `DECIMAL(15,2)`, enquanto emissão, competência e vencimento são convertidos para `DATE`.
# MAGIC
# MAGIC ## Preservação da granularidade do faturamento
# MAGIC
# MAGIC A existência de uma mesma NF em mais de um registro não será tratada automaticamente como duplicidade. O diagnóstico da fonte identificou ocorrências de NFs repetidas associadas, entre outros casos, a registros relacionados a cancelamentos.
# MAGIC
# MAGIC Também foram identificadas situações em que o mesmo conjunto `CR1`–`CR4` possui mais de uma NF na mesma competência. Esses registros representam ocorrências existentes na fonte e serão preservados.
# MAGIC
# MAGIC Por esse motivo, a transformação não aplica `DISTINCT`, não elimina registros apenas pela repetição da NF e não estabelece artificialmente a regra de uma única NF por CR e competência.
# MAGIC
# MAGIC ## Tratamentos realizados
# MAGIC
# MAGIC A transformação Bronze → Silver realiza:
# MAGIC
# MAGIC 1. descarte das linhas sem `NF`;
# MAGIC 2. seleção dos atributos relevantes para o escopo analítico;
# MAGIC 3. padronização dos nomes das colunas;
# MAGIC 4. remoção de espaços adicionais nos campos textuais;
# MAGIC 5. conversão das datas para o tipo `DATE`;
# MAGIC 6. conversão dos valores monetários para `DECIMAL(15,2)`;
# MAGIC 7. preservação dos registros válidos sem deduplicação artificial.
# MAGIC
# MAGIC Campos auxiliares, controles operacionais e atributos não necessários às análises definidas para o MVP não são transportados para esta tabela Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.faturamento_anonimizado AS
# MAGIC
# MAGIC WITH registros_validos AS (
# MAGIC
# MAGIC     SELECT *
# MAGIC     FROM workspace.bronze.faturamento_anonimizado
# MAGIC     WHERE `NF` IS NOT NULL
# MAGIC       AND TRIM(CAST(`NF` AS STRING)) <> ''
# MAGIC
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     TRIM(CAST(`NF` AS STRING)) AS nf,
# MAGIC
# MAGIC     NULLIF(TRIM(CAST(`CR1` AS STRING)), '') AS cr1,
# MAGIC     NULLIF(TRIM(CAST(`CR2` AS STRING)), '') AS cr2,
# MAGIC     NULLIF(TRIM(CAST(`CR3` AS STRING)), '') AS cr3,
# MAGIC     NULLIF(TRIM(CAST(`CR4` AS STRING)), '') AS cr4,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`Emissão` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Emissão` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`Emissão` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Emissão` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`Emissão` AS DATE)
# MAGIC     END AS data_emissao,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`Competência` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Competência` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`Competência` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Competência` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`Competência` AS DATE)
# MAGIC     END AS data_competencia,
# MAGIC
# MAGIC     NULLIF(TRIM(CAST(`Cliente` AS STRING)), '') AS cliente,
# MAGIC
# MAGIC     TRY_CAST(`Valor` AS DECIMAL(15,2)) AS valor,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`Vencimento` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Vencimento` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`Vencimento` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`Vencimento` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`Vencimento` AS DATE)
# MAGIC     END AS data_vencimento,
# MAGIC
# MAGIC     TRY_CAST(`VALOR ISS 2` AS DECIMAL(15,2)) AS valor_iss_2,
# MAGIC     TRY_CAST(`VALOR ISS 5` AS DECIMAL(15,2)) AS valor_iss_5,
# MAGIC     TRY_CAST(`Líquido` AS DECIMAL(15,2)) AS valor_liquido,
# MAGIC
# MAGIC     TRY_CAST(`Retenção IR` AS DECIMAL(15,2)) AS retencao_ir,
# MAGIC     TRY_CAST(`Retenção PIS` AS DECIMAL(15,2)) AS retencao_pis,
# MAGIC     TRY_CAST(`Retenção COFINS` AS DECIMAL(15,2)) AS retencao_cofins,
# MAGIC     TRY_CAST(`Retenção CSSL` AS DECIMAL(15,2)) AS retencao_cssl
# MAGIC
# MAGIC FROM registros_validos;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver de Faturamento
# MAGIC
# MAGIC Após a construção da tabela `workspace.silver.faturamento_anonimizado`, é necessário validar se a transformação Bronze → Silver preservou corretamente os registros considerados válidos e se as conversões de tipos não provocaram perda de informação.
# MAGIC
# MAGIC A validação verifica:
# MAGIC
# MAGIC - quantidade total de registros na Silver;
# MAGIC - quantidade de NFs distintas;
# MAGIC - existência de NF nula ou vazia;
# MAGIC - existência de valores nulos nos códigos `CR1`, `CR2`, `CR3` e `CR4`;
# MAGIC - existência de valores nulos em emissão, competência, cliente, valor e vencimento;
# MAGIC - existência de valores nulos nos campos financeiros selecionados;
# MAGIC - intervalo das datas de competência;
# MAGIC - quantidade de NFs que aparecem em mais de um registro.
# MAGIC
# MAGIC A repetição de uma NF não será considerada automaticamente um erro, pois a análise realizada na fonte mostrou a existência de registros que devem ser preservados, inclusive ocorrências relacionadas a cancelamentos.
# MAGIC
# MAGIC Da mesma forma, a existência de mais de uma NF para o mesmo conjunto `CR1`–`CR4` em uma mesma competência não será tratada como duplicidade artificial.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH nfs_repetidas AS (
# MAGIC     SELECT nf
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC     GROUP BY nf
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT nf) AS total_nfs_distintas,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN nf IS NULL OR TRIM(nf) = ''
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS nf_invalidas,
# MAGIC
# MAGIC     SUM(CASE WHEN cr1 IS NULL THEN 1 ELSE 0 END) AS cr1_nulos,
# MAGIC     SUM(CASE WHEN cr2 IS NULL THEN 1 ELSE 0 END) AS cr2_nulos,
# MAGIC     SUM(CASE WHEN cr3 IS NULL THEN 1 ELSE 0 END) AS cr3_nulos,
# MAGIC     SUM(CASE WHEN cr4 IS NULL THEN 1 ELSE 0 END) AS cr4_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_emissao IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_emissao_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_competencia IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_competencia_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN cliente IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cliente_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS valor_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_vencimento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_vencimento_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN valor_iss_2 IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS valor_iss_2_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN valor_iss_5 IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS valor_iss_5_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN valor_liquido IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS valor_liquido_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN retencao_ir IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS retencao_ir_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN retencao_pis IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS retencao_pis_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN retencao_cofins IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS retencao_cofins_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN retencao_cssl IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS retencao_cssl_nulos,
# MAGIC
# MAGIC     MIN(data_competencia) AS menor_competencia,
# MAGIC     MAX(data_competencia) AS maior_competencia,
# MAGIC
# MAGIC     (SELECT COUNT(*) FROM nfs_repetidas)
# MAGIC         AS quantidade_nfs_repetidas
# MAGIC
# MAGIC FROM workspace.silver.faturamento_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Validação da tabela Silver de Faturamento
# MAGIC
# MAGIC A validação da tabela `workspace.silver.faturamento_anonimizado` confirmou a preservação dos registros válidos e a consistência das transformações realizadas na passagem da camada Bronze para a Silver.
# MAGIC
# MAGIC Foram obtidos **4.157 registros válidos**, correspondentes a **4.147 NFs distintas**. Não foi identificada nenhuma NF nula ou vazia na tabela Silver, confirmando que os registros sem identificação de nota fiscal foram corretamente excluídos.
# MAGIC
# MAGIC Não foram encontrados valores nulos em nenhum dos atributos selecionados:
# MAGIC
# MAGIC - `cr1`;
# MAGIC - `cr2`;
# MAGIC - `cr3`;
# MAGIC - `cr4`;
# MAGIC - `data_emissao`;
# MAGIC - `data_competencia`;
# MAGIC - `cliente`;
# MAGIC - `valor`;
# MAGIC - `data_vencimento`;
# MAGIC - `valor_iss_2`;
# MAGIC - `valor_iss_5`;
# MAGIC - `valor_liquido`;
# MAGIC - `retencao_ir`;
# MAGIC - `retencao_pis`;
# MAGIC - `retencao_cofins`;
# MAGIC - `retencao_cssl`.
# MAGIC
# MAGIC As competências presentes na tabela abrangem o período de **01/11/2011 a 20/10/2025**.
# MAGIC
# MAGIC Foram identificadas **8 NFs que aparecem em mais de um registro**. Essas ocorrências são preservadas, pois a repetição de uma NF não caracteriza automaticamente uma duplicidade indevida. A análise realizada anteriormente na fonte identificou registros que devem ser mantidos, inclusive ocorrências relacionadas a cancelamentos.
# MAGIC
# MAGIC Também permanece válida a decisão de permitir mais de uma NF para o mesmo conjunto `CR1`–`CR4` em uma mesma competência. A transformação não impõe artificialmente uma relação de uma única NF por CR e competência.
# MAGIC
# MAGIC Os resultados confirmam que a transformação Bronze → Silver preservou os **4.157 registros válidos**, realizou adequadamente as conversões dos atributos selecionados e não introduziu valores nulos decorrentes do tratamento.
# MAGIC
# MAGIC Com isso, a construção e a validação da tabela Silver de Faturamento são consideradas concluídas.