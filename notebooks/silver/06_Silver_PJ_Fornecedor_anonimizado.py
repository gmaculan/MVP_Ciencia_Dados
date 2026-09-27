# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da tabela Silver de PJ
# MAGIC
# MAGIC A tabela Silver de PJ é construída a partir de `workspace.bronze.pj_anonimizado`.
# MAGIC
# MAGIC A fonte contém informações cadastrais de profissionais contratados como pessoa jurídica. Para o escopo analítico do MVP, serão preservados apenas os atributos necessários para identificar a empresa e o profissional correspondente.
# MAGIC
# MAGIC ## Atributos selecionados
# MAGIC
# MAGIC Foram selecionados os seguintes atributos:
# MAGIC
# MAGIC - `NOME REDUZIDO EMPRESA` → `nome_empresa`;
# MAGIC - `NOME REDUZIDO` → `nome_reduzido`;
# MAGIC - `NOME` → `nome`;
# MAGIC - `GÊNERO` → `genero`.
# MAGIC
# MAGIC Os campos são mantidos como `STRING` e têm espaços adicionais removidos durante a transformação.
# MAGIC
# MAGIC ## Tratamento de duplicidades
# MAGIC
# MAGIC O diagnóstico da fonte identificou **12 registros**, mas existem ocorrências repetidas considerando conjuntamente os quatro atributos selecionados para a Silver.
# MAGIC
# MAGIC Como essas ocorrências não acrescentam informação distinta dentro do escopo adotado para a entidade PJ, a Silver manterá apenas as combinações distintas desses quatro atributos.
# MAGIC
# MAGIC Dessa forma, a transformação Bronze → Silver realiza:
# MAGIC
# MAGIC 1. seleção dos atributos relevantes para o escopo do MVP;
# MAGIC 2. padronização dos nomes das colunas;
# MAGIC 3. remoção de espaços adicionais dos campos textuais;
# MAGIC 4. eliminação de registros integralmente duplicados considerando os atributos selecionados.
# MAGIC
# MAGIC A deduplicação é aplicada somente quando todos os atributos selecionados apresentam a mesma combinação de valores, sem inferir ou alterar informações da fonte.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.pj_anonimizado AS
# MAGIC
# MAGIC SELECT DISTINCT
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`NOME REDUZIDO EMPRESA` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS nome_empresa,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`NOME REDUZIDO` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS nome_reduzido,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`NOME` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS nome,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`GÊNERO` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS genero
# MAGIC
# MAGIC FROM workspace.bronze.pj_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver de PJ
# MAGIC
# MAGIC Após a construção da tabela `workspace.silver.pj_anonimizado`, é necessário validar o resultado da transformação Bronze → Silver.
# MAGIC
# MAGIC A validação verifica:
# MAGIC
# MAGIC - quantidade total de registros resultantes;
# MAGIC - quantidade de empresas distintas;
# MAGIC - quantidade de nomes reduzidos distintos;
# MAGIC - quantidade de nomes distintos;
# MAGIC - quantidade de valores distintos de gênero;
# MAGIC - existência de valores nulos nos quatro atributos selecionados;
# MAGIC - existência de registros duplicados considerando conjuntamente `nome_empresa`, `nome_reduzido`, `nome` e `genero`.
# MAGIC
# MAGIC Como a transformação aplicou deduplicação somente às combinações integralmente repetidas dos atributos selecionados, não devem permanecer registros idênticos na tabela Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH duplicidades AS (
# MAGIC     SELECT
# MAGIC         nome_empresa,
# MAGIC         nome_reduzido,
# MAGIC         nome,
# MAGIC         genero,
# MAGIC         COUNT(*) AS quantidade
# MAGIC     FROM workspace.silver.pj_anonimizado
# MAGIC     GROUP BY
# MAGIC         nome_empresa,
# MAGIC         nome_reduzido,
# MAGIC         nome,
# MAGIC         genero
# MAGIC     HAVING COUNT(*) > 1
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT nome_empresa) AS total_empresas,
# MAGIC     COUNT(DISTINCT nome_reduzido) AS total_nomes_reduzidos,
# MAGIC     COUNT(DISTINCT nome) AS total_nomes,
# MAGIC     COUNT(DISTINCT genero) AS total_generos,
# MAGIC
# MAGIC     SUM(CASE WHEN nome_empresa IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS nome_empresa_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN nome_reduzido IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS nome_reduzido_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN nome IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS nome_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN genero IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS genero_nulos,
# MAGIC
# MAGIC     (SELECT COUNT(*) FROM duplicidades)
# MAGIC         AS registros_duplicados
# MAGIC
# MAGIC FROM workspace.silver.pj_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Validação da tabela Silver de PJ
# MAGIC
# MAGIC A validação da tabela `workspace.silver.pj_anonimizado` confirmou a consistência da transformação realizada na passagem da camada Bronze para a Silver.
# MAGIC
# MAGIC A tabela Silver contém **10 registros**, correspondentes a:
# MAGIC
# MAGIC - **9 empresas distintas**;
# MAGIC - **10 nomes reduzidos distintos**;
# MAGIC - **10 nomes distintos**;
# MAGIC - **2 valores distintos de gênero**.
# MAGIC
# MAGIC Não foram encontrados valores nulos em nenhum dos quatro atributos selecionados: `nome_empresa`, `nome_reduzido`, `nome` e `genero`.
# MAGIC
# MAGIC Também não foram identificados registros duplicados considerando conjuntamente os quatro atributos.
# MAGIC
# MAGIC A redução dos **12 registros existentes na fonte para 10 registros na Silver** decorre exclusivamente da eliminação das ocorrências integralmente repetidas nos atributos selecionados, conforme definido na transformação. Nenhuma informação distinta foi eliminada por esse procedimento.
# MAGIC
# MAGIC Com isso, a construção e a validação da tabela Silver de PJ são consideradas concluídas.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Construção da tabela Silver de Fornecedores
# MAGIC
# MAGIC A tabela Silver de Fornecedores é construída a partir de `workspace.bronze.fornecedor_anonimizado`.
# MAGIC
# MAGIC A fonte contém os valores observados de despesas com fornecedores em diferentes competências. Para o escopo do MVP, a camada Silver preservará exclusivamente os registros efetivamente existentes na fonte, sem criação ou extrapolação de competências ou valores.
# MAGIC
# MAGIC ## Atributos selecionados
# MAGIC
# MAGIC Foram selecionados os seguintes atributos:
# MAGIC
# MAGIC - `fornecedor_anonimizado` → `fornecedor`;
# MAGIC - `competencia` → `competencia`;
# MAGIC - `valor_nf_fornecedor` → `valor_nf_fornecedor`.
# MAGIC
# MAGIC O nome do fornecedor é mantido como `STRING`, a competência é convertida para `DATE` e o valor da nota fiscal é convertido para `DECIMAL(15,2)`.
# MAGIC
# MAGIC ## Tratamento dos registros
# MAGIC
# MAGIC A transformação Bronze → Silver realiza:
# MAGIC
# MAGIC 1. seleção dos atributos relevantes para o escopo analítico;
# MAGIC 2. padronização dos nomes e tipos;
# MAGIC 3. remoção de espaços adicionais no nome do fornecedor;
# MAGIC 4. conversão da competência para `DATE`;
# MAGIC 5. conversão do valor da nota fiscal para `DECIMAL(15,2)`;
# MAGIC 6. preservação dos registros observados na fonte.
# MAGIC
# MAGIC A fonte de fornecedores representa uma **amostra dos dados disponíveis**, não uma série histórica completa de todas as despesas da empresa.
# MAGIC
# MAGIC Por esse motivo, competências ausentes não serão criadas na Silver e valores não serão propagados para períodos sem observação.
# MAGIC
# MAGIC Caso seja necessária posteriormente uma extrapolação dos valores observados para fins de análise do MVP, essa operação deverá ser realizada em etapa analítica posterior e permanecer claramente distinguida dos dados efetivamente observados.
# MAGIC
# MAGIC Assim, a tabela Silver representa exclusivamente os registros de fornecedores presentes na fonte.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.fornecedor_anonimizado AS
# MAGIC
# MAGIC SELECT
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`fornecedor_anonimizado` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS fornecedor,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`competencia` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 TRIM(CAST(`competencia` AS STRING)),
# MAGIC                 'd/M/yyyy'
# MAGIC             )
# MAGIC         WHEN TRIM(CAST(`competencia` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 TRIM(CAST(`competencia` AS STRING)),
# MAGIC                 'M/d/yy'
# MAGIC             )
# MAGIC         ELSE TRY_CAST(`competencia` AS DATE)
# MAGIC     END AS competencia,
# MAGIC
# MAGIC     TRY_CAST(
# MAGIC         `valor_nf_fornecedor` AS DECIMAL(15,2)
# MAGIC     ) AS valor_nf_fornecedor
# MAGIC
# MAGIC FROM workspace.bronze.fornecedor_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação da tabela Silver de Fornecedores
# MAGIC
# MAGIC Após a construção da tabela `workspace.silver.fornecedor_anonimizado`, é necessário validar se a transformação Bronze → Silver preservou corretamente os registros observados na fonte e se as conversões de tipos não provocaram perda de informação.
# MAGIC
# MAGIC A validação verifica:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de fornecedores distintos;
# MAGIC - quantidade de competências distintas;
# MAGIC - existência de fornecedor nulo;
# MAGIC - existência de competência nula;
# MAGIC - existência de valor da nota fiscal nulo;
# MAGIC - menor e maior competência presentes na Silver;
# MAGIC - menor e maior valor de nota fiscal observado.
# MAGIC
# MAGIC Nesta etapa não é realizada extrapolação para competências ausentes. A validação considera exclusivamente os registros efetivamente presentes na fonte e transformados para a camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT fornecedor) AS total_fornecedores,
# MAGIC
# MAGIC     COUNT(DISTINCT competencia) AS total_competencias,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN fornecedor IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS fornecedor_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN competencia IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS competencia_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN valor_nf_fornecedor IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS valor_nf_fornecedor_nulos,
# MAGIC
# MAGIC     MIN(competencia) AS menor_competencia,
# MAGIC
# MAGIC     MAX(competencia) AS maior_competencia,
# MAGIC
# MAGIC     MIN(valor_nf_fornecedor) AS menor_valor_nf,
# MAGIC
# MAGIC     MAX(valor_nf_fornecedor) AS maior_valor_nf
# MAGIC
# MAGIC FROM workspace.silver.fornecedor_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação da tabela Silver de Fornecedores
# MAGIC
# MAGIC A validação da tabela `workspace.silver.fornecedor_anonimizado` confirmou a preservação dos registros observados na fonte e a consistência das transformações realizadas na passagem da camada Bronze para a Silver.
# MAGIC
# MAGIC Foram obtidos **850 registros**, correspondentes a **141 fornecedores distintos** e **37 competências distintas**.
# MAGIC
# MAGIC Não foram encontrados valores nulos em nenhum dos três atributos selecionados:
# MAGIC
# MAGIC - `fornecedor`;
# MAGIC - `competencia`;
# MAGIC - `valor_nf_fornecedor`.
# MAGIC
# MAGIC As competências presentes na tabela abrangem o período de **01/04/2015 a 01/12/2025**.
# MAGIC
# MAGIC Os valores de notas fiscais de fornecedores variam entre **R$ 31,01 e R$ 166.940,14**.
# MAGIC
# MAGIC A tabela Silver preserva exclusivamente os registros efetivamente observados na fonte. A existência de somente 37 competências ao longo do intervalo temporal é compatível com o caráter amostral da base de fornecedores e não será preenchida artificialmente nesta camada.
# MAGIC
# MAGIC Nenhuma competência ausente foi criada e nenhum valor foi extrapolado. Caso seja necessária posteriormente uma estimativa para períodos sem observação, essa transformação deverá ocorrer em etapa analítica posterior e permanecer claramente distinguida dos dados observados.
# MAGIC
# MAGIC Os resultados confirmam que a transformação Bronze → Silver preservou os **850 registros da fonte** e realizou adequadamente a padronização dos atributos selecionados.
# MAGIC
# MAGIC Com isso, a construção e a validação da tabela Silver de Fornecedores são consideradas concluídas.