# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da camada Silver — Empregados
# MAGIC
# MAGIC Este notebook realiza a transformação dos dados de empregados da camada Bronze para a camada Silver.
# MAGIC
# MAGIC A tabela de origem é `workspace.bronze.empregados_anonimizados`. Ela possui 155 colunas e 734 registros físicos, dos quais 347 possuem DRT preenchido e representam os vínculos empregatícios considerados válidos para esta etapa.
# MAGIC
# MAGIC A camada Silver não reproduzirá todas as colunas existentes na Bronze. Serão selecionados exclusivamente os 15 atributos considerados necessários ao modelo e às análises previstas no MVP. As demais colunas da Bronze não serão propagadas para a Silver.
# MAGIC
# MAGIC Durante a transformação Bronze → Silver serão aplicados os seguintes tratamentos:
# MAGIC
# MAGIC - exclusão dos registros sem DRT;
# MAGIC - seleção exclusiva dos 15 atributos definidos para a entidade Empregado;
# MAGIC - renomeação dos atributos conforme a nomenclatura definida para a Silver;
# MAGIC - conversão e padronização de `ADMISSÃO`, `DESLIGAMENTO11` e `NASCIMENTO` para o tipo `DATE`;
# MAGIC - tratamento das diferentes representações de data produzidas pela ingestão das células do Excel na camada Bronze;
# MAGIC - correção explícita do valor anômalo `30/10/983`, existente em `NASCIMENTO`, para `30/10/1983`;
# MAGIC - tratamento do valor `135` existente em `DESLIGAMENTO11` como nulo, por não representar uma data válida de desligamento;
# MAGIC - incorporação de `MOTIVO PRINCIPAL` como `motivo_desligamento`, permitindo análises relacionadas às causas de desligamento dos vínculos;
# MAGIC - tratamento do valor `135` existente em `MOTIVO PRINCIPAL` como nulo, por corresponder a erro conhecido de ingestão e não representar uma categoria válida de motivo de desligamento;
# MAGIC - preservação dos valores nulos existentes nos demais atributos selecionados, sem criação ou inferência de informações ausentes;
# MAGIC - manutenção do DRT como identificador do vínculo empregatício;
# MAGIC - manutenção do CPF anonimizado como identificador da mesma pessoa entre vínculos empregatícios distintos.
# MAGIC
# MAGIC A data de desligamento é mantida como atributo temporal do vínculo empregatício. Sua ausência identifica os vínculos que permanecem ativos no período representado pelos dados.
# MAGIC
# MAGIC O motivo de desligamento complementa essa informação temporal e permitirá análises da distribuição e evolução das causas de desligamento e de sua relação com o tempo de permanência dos empregados, sem alterar a granularidade da entidade.
# MAGIC
# MAGIC A transformação preservará a rastreabilidade em relação à camada Bronze e não realizará nova anonimização dos dados.
# MAGIC
# MAGIC A tabela Silver será criada diretamente a partir da Bronze por meio de `CREATE OR REPLACE TABLE AS SELECT`, realizando simultaneamente a seleção, transformação e carga dos 347 vínculos empregatícios considerados no escopo.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.empregados_anonimizados AS
# MAGIC
# MAGIC SELECT
# MAGIC     CAST(`DRT` AS STRING) AS drt,
# MAGIC     CAST(`NOME ANONIMIZADO` AS STRING) AS nome,
# MAGIC     CAST(`GÊNERO` AS STRING) AS genero,
# MAGIC     CAST(`CPF ANONIMIZADO` AS STRING) AS cpf,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`ADMISSÃO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             TRIM(CAST(`ADMISSÃO` AS STRING)),
# MAGIC             'd/M/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         WHEN TRIM(CAST(`ADMISSÃO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             CONCAT(
# MAGIC                 SPLIT(TRIM(CAST(`ADMISSÃO` AS STRING)), '/')[0], '/',
# MAGIC                 SPLIT(TRIM(CAST(`ADMISSÃO` AS STRING)), '/')[1], '/20',
# MAGIC                 SPLIT(TRIM(CAST(`ADMISSÃO` AS STRING)), '/')[2]
# MAGIC             ),
# MAGIC             'M/d/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         ELSE NULL
# MAGIC     END AS data_admissao,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`DESLIGAMENTO11` AS STRING)) = '135'
# MAGIC         THEN NULL
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DESLIGAMENTO11` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             TRIM(CAST(`DESLIGAMENTO11` AS STRING)),
# MAGIC             'd/M/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DESLIGAMENTO11` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             CONCAT(
# MAGIC                 SPLIT(TRIM(CAST(`DESLIGAMENTO11` AS STRING)), '/')[0], '/',
# MAGIC                 SPLIT(TRIM(CAST(`DESLIGAMENTO11` AS STRING)), '/')[1], '/20',
# MAGIC                 SPLIT(TRIM(CAST(`DESLIGAMENTO11` AS STRING)), '/')[2]
# MAGIC             ),
# MAGIC             'M/d/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         ELSE NULL
# MAGIC     END AS data_desligamento,
# MAGIC
# MAGIC     CAST(`ESTADO CIVIL` AS STRING) AS estado_civil,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`NASCIMENTO` AS STRING)) = '30/10/983'
# MAGIC         THEN TO_DATE('30/10/1983', 'dd/MM/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`NASCIMENTO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             TRIM(CAST(`NASCIMENTO` AS STRING)),
# MAGIC             'd/M/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         WHEN TRIM(CAST(`NASCIMENTO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             CONCAT(
# MAGIC                 SPLIT(TRIM(CAST(`NASCIMENTO` AS STRING)), '/')[0], '/',
# MAGIC                 SPLIT(TRIM(CAST(`NASCIMENTO` AS STRING)), '/')[1], '/',
# MAGIC                 CASE
# MAGIC                     WHEN CAST(
# MAGIC                         SPLIT(TRIM(CAST(`NASCIMENTO` AS STRING)), '/')[2]
# MAGIC                         AS INT
# MAGIC                     ) <= 24
# MAGIC                     THEN CONCAT(
# MAGIC                         '20',
# MAGIC                         SPLIT(TRIM(CAST(`NASCIMENTO` AS STRING)), '/')[2]
# MAGIC                     )
# MAGIC                     ELSE CONCAT(
# MAGIC                         '19',
# MAGIC                         SPLIT(TRIM(CAST(`NASCIMENTO` AS STRING)), '/')[2]
# MAGIC                     )
# MAGIC                 END
# MAGIC             ),
# MAGIC             'M/d/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         ELSE NULL
# MAGIC     END AS data_nascimento,
# MAGIC
# MAGIC     CAST(`GRAU DE INSTRUÇÃO` AS STRING) AS grau_instrucao,
# MAGIC     CAST(`ENDEREÇO` AS STRING) AS logradouro,
# MAGIC     CAST(`BAIRRO` AS STRING) AS bairro,
# MAGIC     CAST(`MUNICÍPIO75` AS STRING) AS cidade,
# MAGIC     CAST(`UF76` AS STRING) AS estado,
# MAGIC     CAST(`CEP` AS STRING) AS cep,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`MOTIVO PRINCIPAL` AS STRING)) = '135'
# MAGIC         THEN NULL
# MAGIC         ELSE TRIM(CAST(`MOTIVO PRINCIPAL` AS STRING))
# MAGIC     END AS motivo_desligamento
# MAGIC
# MAGIC FROM workspace.bronze.empregados_anonimizados
# MAGIC
# MAGIC WHERE `DRT` IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Conclusão da Construção da camada Silver — Empregados
# MAGIC
# MAGIC A execução da transformação Bronze → Silver foi concluída sem erros, resultando na atualização da tabela `workspace.silver.empregados_anonimizados`.
# MAGIC
# MAGIC A tabela foi construída diretamente a partir de `workspace.bronze.empregados_anonimizados`, considerando somente os registros com DRT preenchido e os 15 atributos definidos para a entidade Empregado.
# MAGIC
# MAGIC Além dos tratamentos anteriormente aplicados aos dados cadastrais e às datas de admissão e nascimento, a transformação passou a contemplar:
# MAGIC
# MAGIC - `DESLIGAMENTO11`, transformado em `data_desligamento` e convertido para o tipo `DATE`;
# MAGIC - o valor anômalo `135` em `DESLIGAMENTO11`, tratado como nulo por não representar uma data válida;
# MAGIC - `MOTIVO PRINCIPAL`, transformado em `motivo_desligamento`;
# MAGIC - o valor `135` em `MOTIVO PRINCIPAL`, tratado como nulo por corresponder a erro conhecido de ingestão e não representar um motivo de desligamento válido.
# MAGIC
# MAGIC A inclusão de `data_desligamento` e `motivo_desligamento` permite representar tanto o momento quanto a causa do encerramento do vínculo empregatício, mantendo o DRT como granularidade da entidade.
# MAGIC
# MAGIC A conclusão da construção da tabela, entretanto, não é suficiente para considerar a transformação validada. Na próxima etapa serão verificados o volume de registros, a unicidade dos DRTs, as conversões dos campos de data e a consistência entre `data_desligamento` e `motivo_desligamento`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver — Empregados
# MAGIC
# MAGIC Esta etapa valida a tabela `workspace.silver.empregados_anonimizados` após sua atualização.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - o total de registros, esperado em 347 vínculos empregatícios;
# MAGIC - o total de DRTs distintos, esperado também em 347;
# MAGIC - a existência de valores nulos em `data_admissao` e `data_nascimento`;
# MAGIC - as menores e maiores datas de admissão e nascimento;
# MAGIC - a quantidade de vínculos com e sem `data_desligamento`;
# MAGIC - a quantidade de vínculos com e sem `motivo_desligamento`;
# MAGIC - a consistência entre `data_desligamento` e `motivo_desligamento`;
# MAGIC - a inexistência do valor anômalo `135` em `motivo_desligamento`.
# MAGIC
# MAGIC Para os campos de data, a validação permite confirmar que as diferentes representações existentes na camada Bronze foram convertidas corretamente para o tipo `DATE`, sem perda indevida de informações.
# MAGIC
# MAGIC Para os dados de desligamento, espera-se que os vínculos desligados apresentem `data_desligamento` e `motivo_desligamento`, enquanto os vínculos ativos permaneçam sem essas informações. O valor `135`, identificado como erro de ingestão, não deve permanecer como categoria válida de motivo de desligamento.
# MAGIC
# MAGIC A validação permitirá confirmar que a atualização preservou os 347 vínculos anteriormente validados e incorporou as informações de desligamento sem alterar a granularidade da tabela.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS drts_distintos,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_admissao IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS admissoes_nulas,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_nascimento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS nascimentos_nulos,
# MAGIC
# MAGIC     MIN(data_admissao) AS menor_data_admissao,
# MAGIC     MAX(data_admissao) AS maior_data_admissao,
# MAGIC
# MAGIC     MIN(data_nascimento) AS menor_data_nascimento,
# MAGIC     MAX(data_nascimento) AS maior_data_nascimento,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS vinculos_desligados,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS vinculos_ativos,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN motivo_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS vinculos_com_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN motivo_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS vinculos_sem_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NOT NULL
# MAGIC          AND motivo_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS desligados_com_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NOT NULL
# MAGIC          AND motivo_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS desligados_sem_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NULL
# MAGIC          AND motivo_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS ativos_com_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN motivo_desligamento = '135'
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS motivo_135
# MAGIC
# MAGIC FROM workspace.silver.empregados_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Conclusão da Validação da tabela Silver — Empregados
# MAGIC
# MAGIC A validação da tabela `workspace.silver.empregados_anonimizados` confirmou a preservação dos 347 registros e dos 347 DRTs distintos, mantendo a granularidade de um registro por vínculo empregatício.
# MAGIC
# MAGIC Os campos de data anteriormente existentes permaneceram consistentes após a atualização:
# MAGIC
# MAGIC - `data_admissao` não apresentou valores nulos, com datas entre 14/08/2000 e 07/02/2024;
# MAGIC - `data_nascimento` não apresentou valores nulos, com datas entre 30/04/1943 e 13/08/2003.
# MAGIC
# MAGIC Em relação aos dados de desligamento, foram identificados:
# MAGIC
# MAGIC - 333 vínculos com `data_desligamento`;
# MAGIC - 14 vínculos sem `data_desligamento`, correspondentes aos vínculos ativos;
# MAGIC - 333 vínculos com `motivo_desligamento`;
# MAGIC - 14 vínculos sem `motivo_desligamento`;
# MAGIC - 333 vínculos desligados com motivo preenchido;
# MAGIC - nenhum vínculo desligado sem motivo;
# MAGIC - nenhum vínculo ativo com motivo de desligamento;
# MAGIC - nenhuma ocorrência do valor anômalo `135` em `motivo_desligamento`.
# MAGIC
# MAGIC Os resultados demonstram correspondência integral entre a existência da data e do motivo de desligamento: os 333 vínculos desligados possuem motivo, enquanto os 14 vínculos ativos não possuem motivo de desligamento.
# MAGIC
# MAGIC Dessa forma, a atualização da tabela Silver de Empregados está validada quanto ao volume de registros, unicidade do DRT, conversão dos campos de data e consistência das informações de desligamento.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Validação da estrutura e dos valores nulos
# MAGIC
# MAGIC Após a validação do volume de registros, dos campos de data e das informações de desligamento, esta etapa verifica a estrutura final da tabela Silver e a ocorrência de valores nulos nos 15 atributos selecionados.
# MAGIC
# MAGIC A validação tem como objetivos:
# MAGIC
# MAGIC - confirmar que a tabela Silver contém exclusivamente os 15 atributos definidos para a entidade Empregado;
# MAGIC - verificar os tipos de dados resultantes da transformação;
# MAGIC - confirmar a ocorrência de valores nulos nos atributos selecionados;
# MAGIC - verificar especificamente os valores nulos em `data_desligamento` e `motivo_desligamento`, cuja ausência é esperada para os vínculos ativos;
# MAGIC - comparar o resultado com os diagnósticos realizados anteriormente, garantindo que valores ausentes não tenham sido preenchidos ou inferidos durante a transformação.
# MAGIC
# MAGIC Os valores nulos existentes na fonte serão preservados quando não houver informação objetiva que permita seu preenchimento.
# MAGIC
# MAGIC Para `data_desligamento` e `motivo_desligamento`, a existência de 14 valores nulos em cada atributo é esperada e corresponde aos 14 vínculos ativos identificados na validação anterior. Portanto, esses valores nulos possuem significado de negócio e não representam, nesse contexto, falha de qualidade dos dados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(CASE WHEN drt IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS drt_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN nome IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS nome_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN genero IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS genero_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN cpf IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cpf_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_admissao IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_admissao_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_desligamento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_desligamento_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN estado_civil IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS estado_civil_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_nascimento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_nascimento_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN grau_instrucao IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS grau_instrucao_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN logradouro IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS logradouro_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN bairro IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS bairro_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN cidade IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cidade_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN estado IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS estado_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN cep IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cep_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN motivo_desligamento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS motivo_desligamento_nulos
# MAGIC
# MAGIC FROM workspace.silver.empregados_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Conclusão da Validação da estrutura e dos valores nulos
# MAGIC
# MAGIC A validação final da tabela `workspace.silver.empregados_anonimizados` confirmou a consistência dos valores nulos nos 15 atributos selecionados para a entidade Empregado.
# MAGIC
# MAGIC Nos 347 vínculos empregatícios foram observados:
# MAGIC
# MAGIC - nenhum valor nulo em DRT, nome, gênero, CPF, data de admissão, estado civil, data de nascimento e grau de instrução;
# MAGIC - 14 valores nulos em `data_desligamento`;
# MAGIC - 14 valores nulos em `motivo_desligamento`;
# MAGIC - 1 valor nulo em logradouro;
# MAGIC - 1 valor nulo em bairro;
# MAGIC - 1 valor nulo em cidade;
# MAGIC - 1 valor nulo em estado;
# MAGIC - 3 valores nulos em CEP.
# MAGIC
# MAGIC Os 14 valores nulos em `data_desligamento` e `motivo_desligamento` correspondem aos 14 vínculos ativos identificados na validação anterior. Dessa forma, essas ausências possuem significado de negócio e não representam falha de qualidade dos dados.
# MAGIC
# MAGIC Os valores nulos existentes nos campos de endereço foram preservados conforme a fonte, sem preenchimento ou inferência de informações inexistentes.
# MAGIC
# MAGIC Considerando conjuntamente as validações realizadas, a tabela Silver de Empregados mantém 347 registros e 347 DRTs distintos, preserva a granularidade de um registro por vínculo empregatício e apresenta consistência entre a situação do vínculo, a data de desligamento e o respectivo motivo.
# MAGIC
# MAGIC Dessa forma, a atualização da tabela `workspace.silver.empregados_anonimizados` está concluída e validada, estando a entidade Empregado novamente fechada na camada Silver e pronta para utilização nas etapas posteriores do pipeline.