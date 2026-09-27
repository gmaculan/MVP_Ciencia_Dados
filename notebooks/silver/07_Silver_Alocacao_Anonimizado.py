# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da tabela Silver de Alocação
# MAGIC
# MAGIC A tabela Silver de Alocação é construída a partir de `workspace.bronze.alocacao_anonimizado`.
# MAGIC
# MAGIC A fonte representa informações de alocação dos profissionais disponíveis para o MVP. Entretanto, trata-se de uma base parcial, proveniente dos dados que puderam ser recuperados, e não de um histórico completo de todas as alocações ocorridas na empresa.
# MAGIC
# MAGIC Por esse motivo, a ausência de uma alocação em determinado período não deve ser interpretada como evidência de que o profissional não possuía alocação naquele momento.
# MAGIC
# MAGIC ## Critério de escopo
# MAGIC
# MAGIC O diagnóstico da camada Bronze identificou **347 registros**, correspondentes a **347 DRTs distintos**.
# MAGIC
# MAGIC Foram identificados **5 registros sem `NOME REDUZIDO`**, correspondentes a estagiários que estão fora do escopo definido para o MVP.
# MAGIC
# MAGIC Esses cinco registros serão excluídos da tabela Silver. Não será realizado preenchimento ou inferência do nome desses profissionais.
# MAGIC
# MAGIC Dessa forma, são esperados **342 registros** na tabela Silver de Alocação.
# MAGIC
# MAGIC ## Atributos selecionados
# MAGIC
# MAGIC Foram selecionados os seguintes atributos:
# MAGIC
# MAGIC - `DRT` → `drt`;
# MAGIC - `NOME REDUZIDO` → `nome_reduzido`;
# MAGIC - `ALOCAÇÃO PRINCIPAL` → `alocacao_principal`;
# MAGIC - `ATIVIDADE` → `atividade`;
# MAGIC - `NÍVEL` → `nivel`;
# MAGIC - `INÍCIO` → `data_inicio`.
# MAGIC
# MAGIC Os atributos textuais são mantidos como `STRING`, com remoção de espaços adicionais, e `INÍCIO` é convertido para `DATE`.
# MAGIC
# MAGIC ## Premissa de alocação adotada no MVP
# MAGIC
# MAGIC A fonte disponível não contém controle de horas que permita distribuir objetivamente o trabalho de um mesmo profissional entre múltiplas alocações simultâneas.
# MAGIC
# MAGIC Por essa razão, o MVP adota como premissa simplificadora uma única alocação por profissional nos dados disponíveis, sem criar percentuais ou distribuições artificiais.
# MAGIC
# MAGIC Essa premissa será utilizada posteriormente para apropriação dos custos de pessoal às alocações representadas no projeto.
# MAGIC
# MAGIC Alocações administrativas também são preservadas. Uma alocação pode receber custos mesmo quando não estiver associada diretamente a faturamento.
# MAGIC
# MAGIC ## Limitação da fonte
# MAGIC
# MAGIC A tabela Silver preserva somente as informações efetivamente disponíveis na fonte.
# MAGIC
# MAGIC Não serão criadas alocações ausentes, datas de término ou períodos históricos por inferência. Portanto, a tabela não deve ser interpretada como reconstrução completa do histórico de alocação da empresa.
# MAGIC
# MAGIC A transformação Bronze → Silver realiza:
# MAGIC
# MAGIC 1. exclusão dos cinco registros fora do escopo do MVP;
# MAGIC 2. seleção dos atributos relevantes;
# MAGIC 3. padronização dos nomes das colunas;
# MAGIC 4. remoção de espaços adicionais dos atributos textuais;
# MAGIC 5. conversão da data de início para `DATE`;
# MAGIC 6. preservação das alocações efetivamente representadas na fonte, sem extrapolação histórica.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.alocacao_anonimizado AS
# MAGIC
# MAGIC WITH registros_escopo AS (
# MAGIC
# MAGIC     SELECT *
# MAGIC     FROM workspace.bronze.alocacao_anonimizado
# MAGIC     WHERE `NOME REDUZIDO` IS NOT NULL
# MAGIC       AND TRIM(CAST(`NOME REDUZIDO` AS STRING)) <> ''
# MAGIC
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`DRT` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS drt,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`NOME REDUZIDO` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS nome_reduzido,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`ALOCAÇÃO PRINCIPAL` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS alocacao_principal,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`ATIVIDADE` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS atividade,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`NÍVEL` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS nivel,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`INÍCIO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 TRIM(CAST(`INÍCIO` AS STRING)),
# MAGIC                 'd/M/yyyy'
# MAGIC             )
# MAGIC         WHEN TRIM(CAST(`INÍCIO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 TRIM(CAST(`INÍCIO` AS STRING)),
# MAGIC                 'M/d/yy'
# MAGIC             )
# MAGIC         ELSE TRY_CAST(`INÍCIO` AS DATE)
# MAGIC     END AS data_inicio
# MAGIC
# MAGIC FROM registros_escopo;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver de Alocação
# MAGIC
# MAGIC Após a construção da tabela `workspace.silver.alocacao_anonimizado`, é necessário validar se a transformação Bronze → Silver preservou corretamente os registros pertencentes ao escopo do MVP e se as conversões realizadas não provocaram perda de informação.
# MAGIC
# MAGIC A validação verifica:
# MAGIC
# MAGIC - quantidade total de registros na Silver;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - existência de DRT nulo ou vazio;
# MAGIC - existência de nomes reduzidos nulos;
# MAGIC - existência de valores nulos em `alocacao_principal`, `atividade`, `nivel` e `data_inicio`;
# MAGIC - existência de DRTs repetidos;
# MAGIC - menor e maior data de início presentes na base.
# MAGIC
# MAGIC Como a fonte diagnosticada possuía 347 registros e cinco registros de estagiários foram excluídos por estarem fora do escopo definido para o MVP, são esperados **342 registros** na Silver.
# MAGIC
# MAGIC A igualdade entre a quantidade de registros e a quantidade de DRTs distintos também será verificada, de acordo com a premissa adotada para os dados de Alocação disponíveis no MVP.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH drts_repetidos AS (
# MAGIC     SELECT
# MAGIC         drt
# MAGIC     FROM workspace.silver.alocacao_anonimizado
# MAGIC     GROUP BY drt
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN drt IS NULL OR TRIM(drt) = ''
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS drt_invalidos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN nome_reduzido IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS nome_reduzido_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN alocacao_principal IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS alocacao_principal_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN atividade IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS atividade_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN nivel IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS nivel_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS data_inicio_nulos,
# MAGIC
# MAGIC     (SELECT COUNT(*) FROM drts_repetidos)
# MAGIC         AS drts_repetidos,
# MAGIC
# MAGIC     MIN(data_inicio) AS menor_data_inicio,
# MAGIC
# MAGIC     MAX(data_inicio) AS maior_data_inicio
# MAGIC
# MAGIC FROM workspace.silver.alocacao_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Verificação do registro com data de início nula
# MAGIC
# MAGIC A validação da tabela Silver de Alocação identificou **1 registro com `data_inicio` nula**.
# MAGIC
# MAGIC Antes de concluir a validação da entidade, é necessário verificar esse registro para determinar se a ausência da data já existe na fonte ou se foi produzida durante a conversão Bronze → Silver.
# MAGIC
# MAGIC Nesta etapa, o registro será apenas identificado. Nenhum valor será preenchido ou inferido.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     b.`DRT` AS drt,
# MAGIC     b.`NOME REDUZIDO` AS nome_reduzido,
# MAGIC     b.`INÍCIO` AS inicio_bronze,
# MAGIC     CAST(b.`INÍCIO` AS STRING) AS inicio_bronze_string
# MAGIC
# MAGIC FROM workspace.bronze.alocacao_anonimizado b
# MAGIC
# MAGIC INNER JOIN workspace.silver.alocacao_anonimizado s
# MAGIC     ON TRIM(CAST(b.`DRT` AS STRING)) = s.drt
# MAGIC
# MAGIC WHERE s.data_inicio IS NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Verificação da conversão da data de início
# MAGIC
# MAGIC A investigação do único registro que apresentou `data_inicio` nula na tabela Silver identificou que o problema não foi causado pela ausência da informação nem pela transformação realizada no Databricks.
# MAGIC
# MAGIC O registro corresponde ao **DRT 559**, cujo campo `INÍCIO` está preenchido na própria fonte como:
# MAGIC
# MAGIC `01/10/201`
# MAGIC
# MAGIC O valor apresenta o ano incompleto e, portanto, não pode ser convertido diretamente para uma data válida.
# MAGIC
# MAGIC A análise do próprio arquivo de origem fornece elementos que permitem identificar o ano pretendido como **2021**:
# MAGIC
# MAGIC - no registro do **DRT 559**, o campo `ÚLTIMA ATUALIZAÇÃO` está preenchido como **01/10/2021**;
# MAGIC - o registro imediatamente anterior, **DRT 558**, possui data de início no ano de **2021**;
# MAGIC - o registro imediatamente posterior, **DRT 560**, também possui data de início no ano de **2021**;
# MAGIC - portanto, o ano de 2021 é coerente com a sequência temporal dos registros adjacentes e com a data de última atualização do próprio DRT 559.
# MAGIC
# MAGIC Diante dessas evidências, para fins de tratamento de qualidade dos dados no MVP, o valor originalmente registrado como `01/10/201` será interpretado como **01/10/2021**.
# MAGIC
# MAGIC A correção mantém o dia e o mês existentes na fonte e completa exclusivamente o dígito ausente do ano com base nas informações disponíveis no próprio conjunto de dados.
# MAGIC
# MAGIC Assim, a inconsistência é tratada de forma explícita e documentada na camada Silver.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Correção da data de início do DRT 559
# MAGIC
# MAGIC A verificação realizada na seção anterior identificou uma inconsistência no campo de data de início do **DRT 559**.
# MAGIC
# MAGIC Na fonte, o valor está registrado como `01/10/201`, com o ano incompleto. A análise das informações disponíveis no próprio conjunto de dados permitiu estabelecer **01/10/2021** como o valor a ser utilizado no MVP.
# MAGIC
# MAGIC A correção será aplicada diretamente ao registro correspondente na tabela `workspace.silver.alocacao_anonimizado`, alterando exclusivamente `data_inicio` do DRT 559.
# MAGIC
# MAGIC Nenhum outro registro ou atributo da tabela será modificado.
# MAGIC
# MAGIC Após a correção, será realizada nova validação para confirmar que a tabela permanece com os mesmos **342 registros e 342 DRTs distintos** e que não existem mais valores nulos em `data_inicio`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC UPDATE workspace.silver.alocacao_anonimizado
# MAGIC
# MAGIC SET data_inicio = TO_DATE('01/10/2021', 'dd/MM/yyyy')
# MAGIC
# MAGIC WHERE drt = '559'
# MAGIC   AND data_inicio IS NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Validação da correção da data de início
# MAGIC
# MAGIC Após a correção da inconsistência identificada no DRT 559, será realizada uma nova validação da tabela `workspace.silver.alocacao_anonimizado`.
# MAGIC
# MAGIC A verificação tem como objetivos confirmar:
# MAGIC
# MAGIC - a permanência dos **342 registros** previstos para o escopo do MVP;
# MAGIC - a permanência de **342 DRTs distintos**;
# MAGIC - a inexistência de DRTs duplicados;
# MAGIC - a inexistência de valores nulos em `data_inicio`;
# MAGIC - o registro de **01/10/2021** como `data_inicio` do DRT 559.
# MAGIC
# MAGIC Essa validação permite confirmar que a correção foi aplicada exclusivamente ao registro identificado, sem alterar a quantidade ou a granularidade dos dados da tabela Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC
# MAGIC     COUNT(*) - COUNT(DISTINCT drt) AS drts_repetidos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS data_inicio_nulos,
# MAGIC
# MAGIC     MAX(
# MAGIC         CASE
# MAGIC             WHEN drt = '559'
# MAGIC             THEN data_inicio
# MAGIC         END
# MAGIC     ) AS data_inicio_drt_559
# MAGIC
# MAGIC FROM workspace.silver.alocacao_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Conclusão da Validação da correção da data de início
# MAGIC
# MAGIC A validação realizada após a correção do DRT 559 confirmou a consistência final da tabela `workspace.silver.alocacao_anonimizado`.
# MAGIC
# MAGIC A tabela permanece com **342 registros**, correspondentes a **342 DRTs distintos**, sem ocorrência de DRTs repetidos.
# MAGIC
# MAGIC Após o tratamento da inconsistência identificada na fonte, não existem mais valores nulos em `data_inicio`.
# MAGIC
# MAGIC Especificamente para o **DRT 559**, a data de início passou a ser registrada como **01/10/2021**, conforme a premissa de tratamento documentada anteriormente.
# MAGIC
# MAGIC A correção não alterou a quantidade de registros nem a granularidade da tabela e foi aplicada exclusivamente à inconsistência identificada.
# MAGIC
# MAGIC Dessa forma, a tabela Silver de Alocação apresenta:
# MAGIC
# MAGIC - **342 registros**;
# MAGIC - **342 DRTs distintos**;
# MAGIC - **0 DRTs repetidos**;
# MAGIC - **0 datas de início nulas**;
# MAGIC - `data_inicio` do DRT 559 igual a **01/10/2021**.
# MAGIC
# MAGIC Com isso, a construção, o tratamento da inconsistência identificada e a validação da tabela Silver de Alocação são considerados concluídos.