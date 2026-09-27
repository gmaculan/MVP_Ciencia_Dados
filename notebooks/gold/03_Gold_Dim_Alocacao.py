# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC # 1. Levantamento da estrutura da dimensão de alocações
# MAGIC
# MAGIC A construção da `dim_alocacao` partirá da tabela `workspace.silver.alocacao_anonimizado`.
# MAGIC
# MAGIC Diferentemente da tabela Silver, que contém a associação entre cada profissional e sua alocação, a dimensão Gold deverá representar as características da própria alocação, evitando incorporar atributos destinados à identificação do empregado.
# MAGIC
# MAGIC Por esse motivo, `drt` e `nome_reduzido` não serão utilizados como atributos descritivos da dimensão, pois a identificação dos vínculos empregatícios é responsabilidade da `dim_empregado`.
# MAGIC
# MAGIC Além de evitar redundância entre dimensões, essa separação segue uma preocupação de governança de dados. Embora os dados utilizados neste MVP tenham sido previamente anonimizados, em um ambiente corporativo real informações de identificação dos empregados constituem dados pessoais ou sensíveis ao contexto organizacional. Evitar sua replicação desnecessária em diferentes estruturas reduz a disseminação dessas informações e facilita seu controle e governança.
# MAGIC
# MAGIC A associação entre empregados e alocações será realizada no modelo dimensional por meio das respectivas chaves, sem necessidade de repetir atributos de identificação do empregado na `dim_alocacao`.
# MAGIC
# MAGIC A `data_inicio` não será considerada atributo da `dim_alocacao`, pois a análise temporal das alocações será realizada por meio da `dim_tempo`.
# MAGIC
# MAGIC O atributo `nivel` também não será incorporado à dimensão, pois não é necessário para as análises previstas no MVP.
# MAGIC
# MAGIC O atributo `atividade`, por outro lado, será mantido na `dim_alocacao`. Essa informação será utilizada para auxiliar na distinção entre alocações relacionadas ao faturamento e alocações administrativas. Sua utilização evita a necessidade de reconstruir posteriormente essa classificação por meio do levantamento dos centros de resultado, da identificação de seus níveis hierárquicos e da verificação de quais centros estão ou não associados a clientes.
# MAGIC
# MAGIC Dessa forma, os atributos previstos para a `dim_alocacao` são:
# MAGIC
# MAGIC - `id_alocacao`: chave substituta criada na camada Gold;
# MAGIC - `alocacao_principal`: identificação da alocação;
# MAGIC - `atividade`: classificação utilizada para auxiliar na distinção entre alocações relacionadas ao faturamento e alocações administrativas.
# MAGIC
# MAGIC Antes da criação da dimensão, será verificado se uma mesma `alocacao_principal` está associada a mais de uma `atividade`.
# MAGIC
# MAGIC Essa verificação permitirá determinar se `alocacao_principal` identifica de forma única cada alocação ou se a combinação entre `alocacao_principal` e `atividade` deverá ser considerada na definição da granularidade da dimensão.
# MAGIC
# MAGIC Nesta etapa será realizado apenas esse levantamento, sem criação ou alteração de tabelas na camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     alocacao_principal,
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT atividade) AS atividades_distintas,
# MAGIC     CONCAT_WS(
# MAGIC         ', ',
# MAGIC         SORT_ARRAY(COLLECT_SET(atividade))
# MAGIC     ) AS atividades_encontradas
# MAGIC
# MAGIC FROM workspace.silver.alocacao_anonimizado
# MAGIC
# MAGIC GROUP BY
# MAGIC     alocacao_principal
# MAGIC
# MAGIC ORDER BY
# MAGIC     alocacao_principal;

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Conclusão do Levantamento da estrutura da dimensão de alocações
# MAGIC
# MAGIC O levantamento realizado sobre a tabela `workspace.silver.alocacao_anonimizado` identificou **61 valores distintos de `alocacao_principal`** entre os **342 registros** existentes na Silver.
# MAGIC
# MAGIC Das 61 alocações identificadas:
# MAGIC
# MAGIC - **58** estão associadas a uma única `atividade`;
# MAGIC - **3** apresentam registros associados simultaneamente às atividades `FIM` e `MEIO`: `NEXA`, `NEXA.ADM` e `XXX`.
# MAGIC
# MAGIC A existência dessas divergências deve ser analisada considerando as características da fonte de dados. Os registros utilizados no MVP são provenientes de planilhas sujeitas a preenchimento manual, nas quais podem ocorrer erros de digitação, classificações incorretas e ausência de informações.
# MAGIC
# MAGIC Em um sistema corporativo estruturado, como o representado pelo modelo proposto neste MVP, essas ocorrências poderiam ser reduzidas por mecanismos de controle de qualidade na entrada dos dados. Entre esses mecanismos estariam a utilização de cadastros previamente definidos de centros de resultado e suas respectivas classificações, listas de valores válidos e obrigatoriedade de preenchimento de determinados campos. Esses controles reduziriam inconsistências decorrentes da digitação manual e permitiriam manter classificações padronizadas por cliente, departamento ou responsável.
# MAGIC
# MAGIC Com base no conhecimento do negócio, ficam estabelecidas para a camada Gold as seguintes regras de classificação:
# MAGIC
# MAGIC - `NEXA` será classificada como atividade `MEIO`;
# MAGIC - `NEXA.ADM` será classificada como atividade `MEIO`;
# MAGIC - `XXX` será classificada como atividade `FIM`.
# MAGIC
# MAGIC Eventuais registros dessas três alocações que apresentem classificação diferente da definida acima serão considerados inconsistências de preenchimento da fonte e serão padronizados durante a construção da `dim_alocacao`.
# MAGIC
# MAGIC Com essas regras, cada `alocacao_principal` passará a possuir uma única classificação de `atividade` na dimensão Gold. A granularidade da `dim_alocacao` será, portanto, de **um registro por `alocacao_principal`**.
# MAGIC
# MAGIC A tabela Silver permanecerá inalterada, preservando os dados conforme tratados a partir da fonte. As regras de padronização definidas nesta etapa serão aplicadas exclusivamente na construção da camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.dim_alocacao AS
# MAGIC
# MAGIC WITH alocacoes_padronizadas AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         alocacao_principal,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN alocacao_principal IN ('NEXA', 'NEXA.ADM') THEN 'MEIO'
# MAGIC             WHEN alocacao_principal = 'XXX' THEN 'FIM'
# MAGIC             ELSE atividade
# MAGIC         END AS atividade
# MAGIC
# MAGIC     FROM workspace.silver.alocacao_anonimizado
# MAGIC ),
# MAGIC
# MAGIC alocacoes_distintas AS (
# MAGIC
# MAGIC     SELECT DISTINCT
# MAGIC         alocacao_principal,
# MAGIC         atividade
# MAGIC
# MAGIC     FROM alocacoes_padronizadas
# MAGIC ),
# MAGIC
# MAGIC alocacoes_identificadas AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY alocacao_principal
# MAGIC         ) AS id_alocacao,
# MAGIC
# MAGIC         alocacao_principal,
# MAGIC         atividade
# MAGIC
# MAGIC     FROM alocacoes_distintas
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     id_alocacao,
# MAGIC     alocacao_principal,
# MAGIC     atividade
# MAGIC
# MAGIC FROM alocacoes_identificadas;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Validação da dimensão de alocações
# MAGIC
# MAGIC Após a criação da tabela `workspace.gold.dim_alocacao`, será realizada a validação de sua estrutura e conteúdo.
# MAGIC
# MAGIC A verificação tem como objetivos confirmar:
# MAGIC
# MAGIC - a existência de **61 registros**, correspondentes às 61 alocações distintas identificadas no levantamento;
# MAGIC - a existência de **61 identificadores únicos** em `id_alocacao`;
# MAGIC - a existência de **61 valores distintos** de `alocacao_principal`;
# MAGIC - a inexistência de valores nulos nos atributos da dimensão;
# MAGIC - a existência de apenas uma classificação de `atividade` para cada `alocacao_principal`;
# MAGIC - a inexistência de valores de `atividade` diferentes de `FIM` e `MEIO`;
# MAGIC - a aplicação das regras de padronização definidas para `NEXA`, `NEXA.ADM` e `XXX`.
# MAGIC
# MAGIC Essa validação permitirá confirmar a granularidade de um registro por `alocacao_principal` e a consistência das classificações utilizadas na `dim_alocacao`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT id_alocacao) AS ids_distintos,
# MAGIC
# MAGIC     COUNT(DISTINCT alocacao_principal) AS alocacoes_distintas,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN id_alocacao IS NULL
# MAGIC               OR alocacao_principal IS NULL
# MAGIC               OR atividade IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_com_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN atividade NOT IN ('FIM', 'MEIO')
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS atividades_invalidas,
# MAGIC
# MAGIC     MAX(
# MAGIC         CASE WHEN alocacao_principal = 'NEXA'
# MAGIC              THEN atividade END
# MAGIC     ) AS atividade_nexa,
# MAGIC
# MAGIC     MAX(
# MAGIC         CASE WHEN alocacao_principal = 'NEXA.ADM'
# MAGIC              THEN atividade END
# MAGIC     ) AS atividade_nexa_adm,
# MAGIC
# MAGIC     MAX(
# MAGIC         CASE WHEN alocacao_principal = 'XXX'
# MAGIC              THEN atividade END
# MAGIC     ) AS atividade_xxx
# MAGIC
# MAGIC FROM workspace.gold.dim_alocacao;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Validação da dimensão de alocações
# MAGIC
# MAGIC A validação da tabela `workspace.gold.dim_alocacao` confirmou a consistência da dimensão construída a partir da tabela Silver de Alocação e das regras de qualidade definidas para a camada Gold.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **61 registros**;
# MAGIC - **61 identificadores distintos** em `id_alocacao`;
# MAGIC - **61 valores distintos** de `alocacao_principal`;
# MAGIC - **0 registros com valores nulos**;
# MAGIC - **0 classificações de atividade diferentes de `FIM` ou `MEIO`**.
# MAGIC
# MAGIC A correspondência entre o total de registros, a quantidade de identificadores distintos e a quantidade de alocações distintas confirma a granularidade de **um registro por `alocacao_principal`**.
# MAGIC
# MAGIC Também foi confirmada a aplicação das regras de padronização definidas a partir do conhecimento do negócio:
# MAGIC
# MAGIC - `NEXA` foi classificada como atividade `MEIO`;
# MAGIC - `NEXA.ADM` foi classificada como atividade `MEIO`;
# MAGIC - `XXX` foi classificada como atividade `FIM`.
# MAGIC
# MAGIC As inconsistências de classificação existentes na fonte foram mantidas na camada Silver e tratadas somente na construção da dimensão Gold, preservando a rastreabilidade entre os dados tratados e as regras de negócio aplicadas ao modelo analítico.
# MAGIC
# MAGIC A `dim_alocacao` passa, assim, a fornecer uma identificação única para cada alocação e sua respectiva classificação como atividade `FIM` ou `MEIO`, informação que será utilizada posteriormente nas análises de faturamento, custos e rentabilidade.
# MAGIC
# MAGIC Dessa forma, a construção e a validação da `dim_alocacao` são consideradas concluídas.