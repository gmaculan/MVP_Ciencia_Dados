# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição da Fato_Fornecedor
# MAGIC
# MAGIC A `Fato_Fornecedor` tem como objetivo representar os custos históricos com fornecedores disponíveis no conjunto de dados do MVP, permitindo sua integração com as demais estruturas da camada Gold.
# MAGIC
# MAGIC A fonte será `workspace.silver.fornecedor_anonimizado`, que contém os registros tratados e tipados dos fornecedores presentes na amostra utilizada no projeto.
# MAGIC
# MAGIC ## Granularidade
# MAGIC
# MAGIC A granularidade da `Fato_Fornecedor` será definida a partir dos registros de fornecedor e competência existentes na Silver.
# MAGIC
# MAGIC Cada ocorrência representa um valor de fornecedor associado a uma determinada competência.
# MAGIC
# MAGIC A construção da Gold deverá preservar os valores efetivamente observados na fonte, sem criar registros para competências, fornecedores ou períodos inexistentes nos dados originais.
# MAGIC
# MAGIC ## Natureza da fonte
# MAGIC
# MAGIC Os dados de fornecedores utilizados no MVP constituem uma **amostra** e não representam necessariamente o histórico completo de todos os custos com fornecedores da empresa.
# MAGIC
# MAGIC Consequentemente, os valores observados serão preservados como dados históricos disponíveis, sem extrapolação durante a construção da fato.
# MAGIC
# MAGIC Caso seja necessária posteriormente alguma projeção ou extrapolação para fins analíticos, essa informação deverá ser explicitamente diferenciada dos valores observados na origem.
# MAGIC
# MAGIC ## Dimensões relacionadas
# MAGIC
# MAGIC Os fornecedores já estão representados na `Dim_Entidade` como entidades de natureza de despesa.
# MAGIC
# MAGIC A `Fato_Fornecedor` deverá utilizar essa dimensão para identificação dos fornecedores, evitando a reprodução desnecessária dos atributos da entidade na fato.
# MAGIC
# MAGIC A competência será relacionada à dimensão temporal compartilhada da camada Gold.
# MAGIC
# MAGIC ## Apropriação por alocação
# MAGIC
# MAGIC A fonte de fornecedores não possui informação histórica que permita determinar diretamente a qual projeto ou alocação cada custo pertence.
# MAGIC
# MAGIC Por esse motivo, não será criada uma associação histórica artificial entre fornecedor e alocação durante a construção desta fato.
# MAGIC
# MAGIC Para análises gerenciais posteriores que necessitem apropriar esses custos às alocações, será utilizada a premissa definida para o MVP de distribuição igualitária entre as alocações efetivamente representadas nos dados, mantendo essa distribuição identificada como uma regra analítica e não como informação histórica da origem.
# MAGIC
# MAGIC ## Objetivos analíticos
# MAGIC
# MAGIC A `Fato_Fornecedor` deverá permitir análises como:
# MAGIC
# MAGIC - custo de fornecedores por período;
# MAGIC - evolução histórica dos custos observados;
# MAGIC - custo por fornecedor;
# MAGIC - identificação dos fornecedores com maiores valores;
# MAGIC - participação de cada fornecedor no custo observado;
# MAGIC - integração posterior desses custos às análises gerenciais de custo e margem.
# MAGIC
# MAGIC A construção da Gold preservará a distinção entre os valores efetivamente observados na fonte e eventuais critérios de apropriação ou extrapolação utilizados posteriormente nas análises.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH fornecedores_consolidados AS (
# MAGIC     SELECT
# MAGIC         fornecedor,
# MAGIC         competencia,
# MAGIC         SUM(valor_nf_fornecedor) AS valor_fornecedor
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC     GROUP BY
# MAGIC         fornecedor,
# MAGIC         competencia
# MAGIC ),
# MAGIC
# MAGIC fato_fornecedor AS (
# MAGIC     SELECT
# MAGIC         e.id_entidade,
# MAGIC         f.competencia,
# MAGIC         f.valor_fornecedor
# MAGIC     FROM fornecedores_consolidados f
# MAGIC     LEFT JOIN workspace.gold.dim_entidade e
# MAGIC         ON f.fornecedor = e.nome_entidade
# MAGIC        AND e.natureza_entidade = 'D'
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     id_entidade,
# MAGIC     competencia,
# MAGIC     valor_fornecedor
# MAGIC FROM fato_fornecedor
# MAGIC ORDER BY
# MAGIC     competencia,
# MAGIC     id_entidade;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Construção da Fato_Fornecedor
# MAGIC
# MAGIC A construção da `Fato_Fornecedor` resultou em **848 registros**, correspondentes a **141 fornecedores distintos** distribuídos por **37 competências**, no período de abril de 2015 a dezembro de 2025.
# MAGIC
# MAGIC A granularidade definida de **uma linha por fornecedor e competência** foi atendida, não sendo identificadas duplicidades nessa combinação após a transformação.
# MAGIC
# MAGIC Os 850 registros existentes na Silver foram reduzidos para 848 registros na Gold em decorrência da consolidação das duas combinações de fornecedor e competência que apresentavam mais de uma ocorrência na origem. Os valores dessas ocorrências foram somados, preservando integralmente o valor financeiro observado.
# MAGIC
# MAGIC Todos os fornecedores encontraram correspondência na `Dim_Entidade`, não havendo `id_entidade` nulo no resultado.
# MAGIC
# MAGIC Também não foram identificados valores ou competências nulos, nem valores financeiros menores ou iguais a zero.
# MAGIC
# MAGIC A transformação preserva exclusivamente os valores observados na amostra disponível, sem criar registros, extrapolar períodos ou atribuir artificialmente os custos a alocações.
# MAGIC
# MAGIC Com a estrutura validada, a próxima etapa consiste na persistência da `Fato_Fornecedor` na camada Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Persistência da Fato_Fornecedor
# MAGIC
# MAGIC Após a validação da transformação, a `Fato_Fornecedor` será persistida na camada Gold como `workspace.gold.fato_fornecedor`, utilizando formato Delta.
# MAGIC
# MAGIC A persistência manterá as regras definidas e validadas anteriormente:
# MAGIC
# MAGIC - granularidade de uma linha por fornecedor e competência;
# MAGIC - consolidação dos registros que apresentavam mais de uma ocorrência para o mesmo fornecedor na mesma competência;
# MAGIC - soma dos valores dessas ocorrências, preservando integralmente o valor financeiro observado;
# MAGIC - identificação do fornecedor por meio de `id_entidade`, proveniente da `Dim_Entidade`;
# MAGIC - preservação da competência como referência temporal da fato;
# MAGIC - utilização exclusivamente dos valores observados na amostra disponível;
# MAGIC - ausência de extrapolação de valores ou períodos;
# MAGIC - ausência de associação artificial dos custos a alocações.
# MAGIC
# MAGIC A tabela persistida servirá de base para as análises de custos com fornecedores e para sua posterior integração às análises gerenciais de custos e margens.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.fato_fornecedor
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH fornecedores_consolidados AS (
# MAGIC     SELECT
# MAGIC         fornecedor,
# MAGIC         competencia,
# MAGIC         SUM(valor_nf_fornecedor) AS valor_fornecedor
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC     GROUP BY
# MAGIC         fornecedor,
# MAGIC         competencia
# MAGIC ),
# MAGIC
# MAGIC fato_fornecedor AS (
# MAGIC     SELECT
# MAGIC         e.id_entidade,
# MAGIC         f.competencia,
# MAGIC         f.valor_fornecedor
# MAGIC     FROM fornecedores_consolidados f
# MAGIC     LEFT JOIN workspace.gold.dim_entidade e
# MAGIC         ON f.fornecedor = e.nome_entidade
# MAGIC        AND e.natureza_entidade = 'D'
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     id_entidade,
# MAGIC     competencia,
# MAGIC     valor_fornecedor
# MAGIC FROM fato_fornecedor;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Persistência da Fato_Fornecedor
# MAGIC
# MAGIC A `Fato_Fornecedor` foi persistida na camada Gold como `workspace.gold.fato_fornecedor`, utilizando formato Delta.
# MAGIC
# MAGIC A tabela foi construída com a granularidade definida de **uma linha por fornecedor e competência**, incorporando os tratamentos validados anteriormente.
# MAGIC
# MAGIC Durante a persistência:
# MAGIC
# MAGIC - os registros pertencentes ao mesmo fornecedor e à mesma competência foram consolidados;
# MAGIC - os valores das ocorrências consolidadas foram somados, preservando integralmente o valor financeiro observado na fonte;
# MAGIC - o fornecedor foi representado por `id_entidade`, proveniente da `Dim_Entidade`;
# MAGIC - a competência foi preservada como referência temporal da fato;
# MAGIC - nenhum valor ou período foi extrapolado;
# MAGIC - nenhuma associação artificial entre fornecedores e alocações foi criada.
# MAGIC
# MAGIC Dessa forma, a `Fato_Fornecedor` representa exclusivamente os custos observados na amostra disponível, mantendo separadas as informações efetivamente existentes na origem de eventuais regras analíticas de apropriação que possam ser utilizadas posteriormente.
# MAGIC
# MAGIC Com a persistência concluída, a próxima etapa consiste na validação final de `workspace.gold.fato_fornecedor`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação final da Fato_Fornecedor
# MAGIC
# MAGIC Após a persistência, será realizada a validação final de `workspace.gold.fato_fornecedor`.
# MAGIC
# MAGIC A validação verificará a granularidade definida para a fato, a integridade das relações com a `Dim_Entidade` e a consistência dos principais campos necessários às análises.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de fornecedores distintos;
# MAGIC - quantidade de competências distintas;
# MAGIC - inexistência de duplicidades de fornecedor e competência;
# MAGIC - inexistência de `id_entidade` nulo;
# MAGIC - inexistência de competência nula;
# MAGIC - inexistência de valor nulo;
# MAGIC - inexistência de valores menores ou iguais a zero;
# MAGIC - cobertura temporal dos registros observados.
# MAGIC
# MAGIC Esses controles permitirão confirmar que a tabela persistida mantém a granularidade de uma linha por fornecedor e competência e representa corretamente os valores disponíveis na amostra utilizada no MVP.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT id_entidade) AS total_fornecedores,
# MAGIC
# MAGIC     COUNT(DISTINCT competencia) AS total_competencias,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(
# MAGIC         DISTINCT CONCAT(
# MAGIC             CAST(id_entidade AS STRING),
# MAGIC             '|',
# MAGIC             CAST(competencia AS STRING)
# MAGIC         )
# MAGIC     ) AS duplicidades_fornecedor_competencia,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN id_entidade IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS id_entidade_nulo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN competencia IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS competencia_nula,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN valor_fornecedor IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS valor_nulo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN valor_fornecedor <= 0 THEN 1 ELSE 0 END
# MAGIC     ) AS valor_menor_igual_zero,
# MAGIC
# MAGIC     MIN(competencia) AS primeira_competencia,
# MAGIC
# MAGIC     MAX(competencia) AS ultima_competencia
# MAGIC
# MAGIC FROM workspace.gold.fato_fornecedor;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação final da Fato_Fornecedor
# MAGIC
# MAGIC A validação final de `workspace.gold.fato_fornecedor` confirmou a consistência da estrutura persistida e dos tratamentos aplicados durante sua construção.
# MAGIC
# MAGIC A tabela apresentou:
# MAGIC
# MAGIC - **848 registros**;
# MAGIC - **141 fornecedores distintos**;
# MAGIC - **37 competências distintas**;
# MAGIC - **0 duplicidades de fornecedor e competência**;
# MAGIC - **0 registros com `id_entidade` nulo**;
# MAGIC - **0 competências nulas**;
# MAGIC - **0 valores nulos**;
# MAGIC - **0 valores menores ou iguais a zero**.
# MAGIC
# MAGIC A cobertura temporal dos registros observados compreende o período de **abril de 2015 a dezembro de 2025**.
# MAGIC
# MAGIC A ausência de duplicidades confirma a granularidade definida para a fato: **uma linha por fornecedor e competência**.
# MAGIC
# MAGIC Os dois casos identificados na origem com mais de uma ocorrência para o mesmo fornecedor na mesma competência foram consolidados por meio da soma dos respectivos valores. Dessa forma, os 850 registros existentes na Silver resultaram em 848 registros na Gold, sem perda dos valores financeiros observados.
# MAGIC
# MAGIC Todos os fornecedores encontraram correspondência na `Dim_Entidade`, confirmando a integridade da associação utilizada na construção da fato.
# MAGIC
# MAGIC A `Fato_Fornecedor` representa exclusivamente os dados observados na amostra disponível. Não foram realizadas extrapolações de valores ou períodos, nem foram criadas associações artificiais entre fornecedores e alocações.
# MAGIC
# MAGIC Eventuais critérios posteriores de apropriação desses custos às alocações deverão permanecer explicitamente identificados como premissas analíticas do MVP, sem serem confundidos com informações históricas existentes na fonte.
# MAGIC
# MAGIC Com os controles estruturais e de qualidade atendidos, a `Fato_Fornecedor` é considerada concluída para utilização nas análises do MVP.