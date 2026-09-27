# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da tabela Silver de Dependentes
# MAGIC
# MAGIC A tabela `workspace.bronze.dependentes_anonimizados` contém os dados dos dependentes associados aos vínculos empregatícios.
# MAGIC
# MAGIC A camada Silver preservará os atributos necessários para identificação do vínculo, caracterização do dependente e posterior determinação do custo de Plano de Saúde:
# MAGIC
# MAGIC - `DRT` → `drt`;
# MAGIC - `GÊNERO` → `genero`;
# MAGIC - `NOME` → `nome`;
# MAGIC - `PARENTESCO` → `parentesco`;
# MAGIC - `NASCIMENTO` → `data_nascimento`.
# MAGIC
# MAGIC O `DRT` identifica o vínculo do empregado titular ao qual o dependente está associado. Cada dependente permanecerá como um registro próprio, preservando a separação entre as entidades Empregado e Dependente.
# MAGIC
# MAGIC A data de nascimento será convertida para o tipo `DATE`, pois será utilizada posteriormente para calcular a idade do dependente na data de referência do vínculo e determinar sua faixa etária para o Plano de Saúde.
# MAGIC
# MAGIC O diagnóstico da camada Bronze identificou 218 registros correspondentes a 130 DRTs, sem valores nulos nos atributos selecionados e sem duplicidades pela combinação entre DRT e nome.
# MAGIC
# MAGIC Registros de dependentes distintos que apresentem a mesma data de nascimento serão preservados, pois essa condição não caracteriza, isoladamente, duplicidade.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.dependentes_anonimizados AS
# MAGIC
# MAGIC SELECT
# MAGIC     CAST(`DRT` AS STRING) AS drt,
# MAGIC     CAST(`GÊNERO` AS STRING) AS genero,
# MAGIC     CAST(`NOME` AS STRING) AS nome,
# MAGIC     CAST(`PARENTESCO` AS STRING) AS parentesco,
# MAGIC
# MAGIC     CASE
# MAGIC         /* Correção de erro de digitação identificado na origem */
# MAGIC         WHEN TRIM(CAST(`NASCIMENTO` AS STRING)) = '26/01;1989'
# MAGIC         THEN TO_DATE('26/01/1989', 'dd/MM/yyyy')
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
# MAGIC                         SPLIT(
# MAGIC                             TRIM(CAST(`NASCIMENTO` AS STRING)),
# MAGIC                             '/'
# MAGIC                         )[2] AS INT
# MAGIC                     ) <= 26
# MAGIC                     THEN CONCAT(
# MAGIC                         '20',
# MAGIC                         SPLIT(
# MAGIC                             TRIM(CAST(`NASCIMENTO` AS STRING)),
# MAGIC                             '/'
# MAGIC                         )[2]
# MAGIC                     )
# MAGIC                     ELSE CONCAT(
# MAGIC                         '19',
# MAGIC                         SPLIT(
# MAGIC                             TRIM(CAST(`NASCIMENTO` AS STRING)),
# MAGIC                             '/'
# MAGIC                         )[2]
# MAGIC                     )
# MAGIC                 END
# MAGIC             ),
# MAGIC             'M/d/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         ELSE NULL
# MAGIC     END AS data_nascimento
# MAGIC
# MAGIC FROM workspace.bronze.dependentes_anonimizados
# MAGIC
# MAGIC WHERE `DRT` IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Conclusão da Construção da tabela Silver de Dependentes
# MAGIC
# MAGIC A tabela `workspace.silver.dependentes_anonimizados` foi criada a partir de `workspace.bronze.dependentes_anonimizados`.
# MAGIC
# MAGIC Foram mantidos os atributos necessários ao escopo analítico do MVP:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `genero`;
# MAGIC - `nome`;
# MAGIC - `parentesco`;
# MAGIC - `data_nascimento`.
# MAGIC
# MAGIC O atributo `drt` foi padronizado como `STRING`, mantendo sua função de identificador do vínculo empregatício ao qual o dependente está associado.
# MAGIC
# MAGIC A data de nascimento foi convertida para o tipo `DATE`, permitindo seu uso posterior no cálculo da idade do dependente na data de referência do vínculo e no respectivo enquadramento por faixa etária do Plano de Saúde.
# MAGIC
# MAGIC A criação da tabela não produziu linhas como saída da célula SQL, comportamento esperado para a operação executada. A quantidade de registros e a consistência dos atributos serão verificadas na etapa seguinte.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Validação da tabela Silver de Dependentes
# MAGIC
# MAGIC Após a criação da tabela Silver, será verificada a quantidade de registros, a quantidade de DRTs distintos, a presença de valores nulos nos atributos selecionados e o intervalo das datas de nascimento.
# MAGIC
# MAGIC A validação permitirá confirmar se os 218 registros identificados no diagnóstico da camada Bronze foram preservados e se a conversão de `data_nascimento` para o tipo `DATE` ocorreu sem perda de informação.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC
# MAGIC     SUM(CASE WHEN drt IS NULL THEN 1 ELSE 0 END) AS drt_nulos,
# MAGIC     SUM(CASE WHEN genero IS NULL THEN 1 ELSE 0 END) AS genero_nulos,
# MAGIC     SUM(CASE WHEN nome IS NULL THEN 1 ELSE 0 END) AS nome_nulos,
# MAGIC     SUM(CASE WHEN parentesco IS NULL THEN 1 ELSE 0 END) AS parentesco_nulos,
# MAGIC     SUM(CASE WHEN data_nascimento IS NULL THEN 1 ELSE 0 END) AS data_nascimento_nulos,
# MAGIC
# MAGIC     MIN(data_nascimento) AS menor_data_nascimento,
# MAGIC     MAX(data_nascimento) AS maior_data_nascimento
# MAGIC
# MAGIC FROM workspace.silver.dependentes_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Conclusão da Validação da tabela Silver de Dependentes
# MAGIC
# MAGIC A validação da tabela `workspace.silver.dependentes_anonimizados` apresentou **218 registros**, associados a **130 DRTs distintos**, reproduzindo as quantidades identificadas anteriormente na camada Bronze.
# MAGIC
# MAGIC Não foram identificados valores nulos nos atributos:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `genero`;
# MAGIC - `nome`;
# MAGIC - `parentesco`;
# MAGIC - `data_nascimento`.
# MAGIC
# MAGIC As datas de nascimento variam entre **05/11/1932 e 13/08/2022**.
# MAGIC
# MAGIC A ausência de valores nulos em `data_nascimento` confirma que a conversão das datas para o tipo `DATE` foi concluída sem perda de registros, incluindo o tratamento específico da ocorrência `26/01;1989`, interpretada como `26/01/1989`.
# MAGIC
# MAGIC Com essas verificações, a construção e a validação da tabela Silver de Dependentes são consideradas concluídas.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Cálculo do Plano de Saúde dos dependentes
# MAGIC
# MAGIC Após a construção e validação da tabela Silver de Dependentes, será determinado o custo de Plano de Saúde correspondente aos dependentes de cada vínculo empregatício.
# MAGIC
# MAGIC O cálculo seguirá as mesmas premissas utilizadas anteriormente para o Plano de Saúde do empregado titular.
# MAGIC
# MAGIC Para cada dependente, será considerada como data de referência:
# MAGIC
# MAGIC - a `data_desligamento` do empregado titular, quando o vínculo estiver encerrado;
# MAGIC - a referência mais recente adotada para o Plano de Saúde, quando o vínculo estiver ativo.
# MAGIC
# MAGIC A idade do dependente será calculada nessa data de referência e utilizada para seu enquadramento na respectiva faixa etária do Plano de Saúde.
# MAGIC
# MAGIC Também será mantida a premissa simplificadora adotada para o MVP de utilização da modalidade de Plano de Saúde de menor custo.
# MAGIC
# MAGIC As vigências anuais do Plano de Saúde serão consideradas a partir do mês de outubro, conforme a regra utilizada no tratamento do Plano de Saúde do titular.
# MAGIC
# MAGIC Os dependentes permanecerão armazenados individualmente em `workspace.silver.dependentes_anonimizados`. Para integração com Benefícios, os custos individuais serão posteriormente agregados por `drt`.
# MAGIC
# MAGIC Na tabela `workspace.silver.beneficio_anonimizado`, o custo dos dependentes será mantido separadamente do custo do titular por meio do atributo `plano_saude_dependentes`.
# MAGIC
# MAGIC Dessa forma:
# MAGIC
# MAGIC - `plano_saude` continuará representando exclusivamente o custo do titular;
# MAGIC - `plano_saude_dependentes` representará a soma dos custos de Plano de Saúde dos dependentes associados ao vínculo;
# MAGIC - `total_beneficios` poderá posteriormente ser recalculado incorporando ambos os componentes.
# MAGIC
# MAGIC Essa separação preserva a origem de cada parcela do custo e permite análises distintas dos gastos com Plano de Saúde do titular e de seus dependentes.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC ALTER TABLE workspace.silver.beneficio_anonimizado
# MAGIC ADD COLUMN plano_saude_dependentes DECIMAL(15,2);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Conclusão do Cálculo do Plano de Saúde dos dependentes
# MAGIC
# MAGIC A estrutura da tabela `workspace.silver.beneficio_anonimizado` foi ampliada com a inclusão do atributo `plano_saude_dependentes`, definido como `DECIMAL(15,2)`.
# MAGIC
# MAGIC A nova coluna permitirá armazenar, para cada `drt`, a soma dos custos de Plano de Saúde dos dependentes associados ao respectivo vínculo empregatício.
# MAGIC
# MAGIC A separação entre os componentes foi preservada:
# MAGIC
# MAGIC - `plano_saude` representa exclusivamente o custo do Plano de Saúde do titular;
# MAGIC - `plano_saude_dependentes` será utilizado para o custo agregado dos dependentes.
# MAGIC
# MAGIC Neste momento, a alteração realizada foi exclusivamente estrutural. Os valores de `plano_saude_dependentes` ainda não foram calculados e serão atribuídos na etapa seguinte.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.1 Atribuição dos valores de Plano de Saúde aos dependentes
# MAGIC
# MAGIC Para preencher `plano_saude_dependentes`, será calculado inicialmente o custo individual de cada dependente.
# MAGIC
# MAGIC Para cada dependente, a data de referência será determinada a partir do vínculo do respectivo titular:
# MAGIC
# MAGIC - para vínculos encerrados, será utilizada a `data_desligamento`;
# MAGIC - para vínculos ativos, será utilizada a referência mais recente adotada para o Plano de Saúde.
# MAGIC
# MAGIC A idade do dependente será calculada nessa data e utilizada para determinar sua faixa etária.
# MAGIC
# MAGIC Será aplicada a mesma premissa utilizada para os titulares, considerando a modalidade de Plano de Saúde de menor custo e a vigência anual iniciada em outubro.
# MAGIC
# MAGIC Após a determinação do valor individual, os custos dos dependentes serão somados por `drt`. O resultado agregado será utilizado para preencher `plano_saude_dependentes` em `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC Os vínculos que não possuírem dependentes receberão valor zero nesse atributo.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC MERGE INTO workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC USING (
# MAGIC     WITH dependentes_referencia AS (
# MAGIC         SELECT
# MAGIC             d.drt,
# MAGIC             d.nome,
# MAGIC             d.data_nascimento,
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN e.data_desligamento IS NOT NULL
# MAGIC                     THEN e.data_desligamento
# MAGIC                 ELSE DATE('2025-10-01')
# MAGIC             END AS data_referencia
# MAGIC
# MAGIC         FROM workspace.silver.dependentes_anonimizados AS d
# MAGIC
# MAGIC         INNER JOIN workspace.silver.empregados_anonimizados AS e
# MAGIC             ON d.drt = e.drt
# MAGIC     ),
# MAGIC
# MAGIC     dependentes_idade AS (
# MAGIC         SELECT
# MAGIC             drt,
# MAGIC             nome,
# MAGIC             data_nascimento,
# MAGIC             data_referencia,
# MAGIC
# MAGIC             FLOOR(
# MAGIC                 MONTHS_BETWEEN(data_referencia, data_nascimento) / 12
# MAGIC             ) AS idade,
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN MONTH(data_referencia) >= 10
# MAGIC                     THEN YEAR(data_referencia)
# MAGIC                 ELSE YEAR(data_referencia) - 1
# MAGIC             END AS ano_vigencia
# MAGIC
# MAGIC         FROM dependentes_referencia
# MAGIC     ),
# MAGIC
# MAGIC     custos_individuais AS (
# MAGIC         SELECT
# MAGIC             drt,
# MAGIC
# MAGIC             CAST(
# MAGIC                 CASE
# MAGIC                     /* Plano Vital - vigências a partir de outubro de 2022 */
# MAGIC                     WHEN ano_vigencia >= 2022 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 395.74
# MAGIC                             WHEN idade <= 23 THEN 466.97
# MAGIC                             WHEN idade <= 28 THEN 565.03
# MAGIC                             WHEN idade <= 33 THEN 678.04
# MAGIC                             WHEN idade <= 38 THEN 772.96
# MAGIC                             WHEN idade <= 43 THEN 796.16
# MAGIC                             WHEN idade <= 48 THEN 969.36
# MAGIC                             WHEN idade <= 53 THEN 1140.16
# MAGIC                             WHEN idade <= 58 THEN 1356.80
# MAGIC                             ELSE 2374.40
# MAGIC                         END
# MAGIC
# MAGIC                     /* Vigência iniciada em outubro de 2021 */
# MAGIC                     WHEN ano_vigencia = 2021 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 569.48
# MAGIC                             WHEN idade <= 23 THEN 834.27
# MAGIC                             WHEN idade <= 28 THEN 959.43
# MAGIC                             WHEN idade <= 33 THEN 1094.17
# MAGIC                             WHEN idade <= 38 THEN 1128.48
# MAGIC                             WHEN idade <= 43 THEN 1290.33
# MAGIC                             WHEN idade <= 48 THEN 1392.82
# MAGIC                             WHEN idade <= 53 THEN 1838.51
# MAGIC                             WHEN idade <= 58 THEN 2138.23
# MAGIC                             ELSE 3404.04
# MAGIC                         END
# MAGIC
# MAGIC                     /* Vigência iniciada em outubro de 2020 */
# MAGIC                     WHEN ano_vigencia = 2020 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 520.79
# MAGIC                             WHEN idade <= 23 THEN 762.94
# MAGIC                             WHEN idade <= 28 THEN 877.39
# MAGIC                             WHEN idade <= 33 THEN 1000.61
# MAGIC                             WHEN idade <= 38 THEN 1031.99
# MAGIC                             WHEN idade <= 43 THEN 1180.00
# MAGIC                             WHEN idade <= 48 THEN 1273.73
# MAGIC                             WHEN idade <= 53 THEN 1681.31
# MAGIC                             WHEN idade <= 58 THEN 1955.40
# MAGIC                             ELSE 3112.98
# MAGIC                         END
# MAGIC
# MAGIC                     /* Vigência iniciada em outubro de 2019 */
# MAGIC                     WHEN ano_vigencia = 2019 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 461.37
# MAGIC                             WHEN idade <= 23 THEN 675.89
# MAGIC                             WHEN idade <= 28 THEN 777.28
# MAGIC                             WHEN idade <= 33 THEN 886.44
# MAGIC                             WHEN idade <= 38 THEN 914.24
# MAGIC                             WHEN idade <= 43 THEN 1045.36
# MAGIC                             WHEN idade <= 48 THEN 1128.40
# MAGIC                             WHEN idade <= 53 THEN 1489.47
# MAGIC                             WHEN idade <= 58 THEN 1732.28
# MAGIC                             ELSE 2757.79
# MAGIC                         END
# MAGIC
# MAGIC                     /* Vigências anteriores */
# MAGIC                     ELSE
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 401.68
# MAGIC                             WHEN idade <= 23 THEN 588.44
# MAGIC                             WHEN idade <= 28 THEN 676.72
# MAGIC                             WHEN idade <= 33 THEN 771.76
# MAGIC                             WHEN idade <= 38 THEN 795.96
# MAGIC                             WHEN idade <= 43 THEN 910.12
# MAGIC                             WHEN idade <= 48 THEN 982.41
# MAGIC                             WHEN idade <= 53 THEN 1296.77
# MAGIC                             WHEN idade <= 58 THEN 1508.17
# MAGIC                             ELSE 2401.00
# MAGIC                         END
# MAGIC                 END
# MAGIC                 AS DECIMAL(15,2)
# MAGIC             ) AS custo_plano_dependente
# MAGIC
# MAGIC         FROM dependentes_idade
# MAGIC     ),
# MAGIC
# MAGIC     custos_por_drt AS (
# MAGIC         SELECT
# MAGIC             drt,
# MAGIC             CAST(
# MAGIC                 SUM(custo_plano_dependente)
# MAGIC                 AS DECIMAL(15,2)
# MAGIC             ) AS plano_saude_dependentes
# MAGIC
# MAGIC         FROM custos_individuais
# MAGIC         GROUP BY drt
# MAGIC     ),
# MAGIC
# MAGIC     resultado AS (
# MAGIC         SELECT
# MAGIC             b.drt,
# MAGIC             COALESCE(c.plano_saude_dependentes, CAST(0 AS DECIMAL(15,2)))
# MAGIC                 AS plano_saude_dependentes
# MAGIC
# MAGIC         FROM workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC         LEFT JOIN custos_por_drt AS c
# MAGIC             ON b.drt = c.drt
# MAGIC     )
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         plano_saude_dependentes
# MAGIC     FROM resultado
# MAGIC
# MAGIC ) AS origem
# MAGIC
# MAGIC ON b.drt = origem.drt
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC     UPDATE SET
# MAGIC         b.plano_saude_dependentes = origem.plano_saude_dependentes;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.1. Conclusão da Atribuição dos valores de Plano de Saúde aos dependentes
# MAGIC
# MAGIC A execução do `MERGE` atualizou os **342 registros** existentes em `workspace.silver.beneficio_anonimizado`, sem inserção ou exclusão de registros.
# MAGIC
# MAGIC Para os vínculos com dependentes, `plano_saude_dependentes` recebeu a soma dos custos individuais dos dependentes associados ao respectivo `drt`.
# MAGIC
# MAGIC Para os vínculos sem dependentes, foi atribuído o valor zero.
# MAGIC
# MAGIC O cálculo individual considerou a data de referência do vínculo, a idade do dependente nessa data, seu enquadramento na respectiva faixa etária, a vigência anual iniciada em outubro e a premissa simplificadora adotada para o MVP de utilização da modalidade de Plano de Saúde de menor custo.
# MAGIC
# MAGIC A execução confirma que todos os registros da tabela de Benefícios foram alcançados pela atualização. A consistência dos valores atribuídos será verificada na etapa seguinte.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. Validação dos valores de Plano de Saúde dos dependentes
# MAGIC
# MAGIC Após a atribuição dos custos de Plano de Saúde dos dependentes, será verificada a cobertura dos 342 vínculos existentes na tabela de Benefícios.
# MAGIC
# MAGIC A validação permitirá identificar:
# MAGIC
# MAGIC - a quantidade de registros com valor nulo;
# MAGIC - a quantidade de vínculos sem custo de dependentes;
# MAGIC - a quantidade de vínculos com custo de dependentes;
# MAGIC - o menor e o maior custo agregado de Plano de Saúde dos dependentes.
# MAGIC
# MAGIC Essa verificação permitirá confirmar se a agregação por `drt` foi aplicada a todos os registros e se os vínculos sem dependentes receberam valor zero conforme definido.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN plano_saude_dependentes IS NULL
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS plano_dependentes_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN plano_saude_dependentes = 0
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS vinculos_sem_custo_dependentes,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN plano_saude_dependentes > 0
# MAGIC         THEN 1 ELSE 0 END
# MAGIC     ) AS vinculos_com_custo_dependentes,
# MAGIC
# MAGIC     MIN(plano_saude_dependentes) AS menor_plano_saude_dependentes,
# MAGIC     MAX(plano_saude_dependentes) AS maior_plano_saude_dependentes
# MAGIC
# MAGIC FROM workspace.silver.beneficio_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.2. Conclusão da Validação dos valores de Plano de Saúde dos dependentes
# MAGIC
# MAGIC A validação de `plano_saude_dependentes` apresentou **342 registros**, sem valores nulos.
# MAGIC
# MAGIC Dos vínculos existentes na tabela de Benefícios:
# MAGIC
# MAGIC - **129** apresentam custo de Plano de Saúde associado a dependentes;
# MAGIC - **213** apresentam valor zero, indicando ausência de dependentes contemplados no cruzamento com a tabela de Benefícios.
# MAGIC
# MAGIC Os valores agregados de `plano_saude_dependentes` variam entre **R$ 0,00 e R$ 3.811,74**.
# MAGIC
# MAGIC A tabela Silver de Dependentes contém dependentes associados a **130 DRTs distintos**, enquanto foram identificados custos de dependentes para 129 vínculos na tabela de Benefícios. Essa diferença é compatível com o fato de a tabela de Benefícios possuir escopo próprio de vínculos e não implica, isoladamente, perda de registros na tabela de Dependentes.
# MAGIC
# MAGIC Não foram identificados valores nulos após a atualização, e os vínculos sem dependentes contemplados receberam valor zero conforme definido.
# MAGIC
# MAGIC Com essas verificações, a atribuição dos custos de Plano de Saúde dos dependentes é considerada concluída e validada.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3.3. Conferência do Plano de Saúde por dependente
# MAGIC
# MAGIC Para verificar individualmente os valores utilizados na composição de `plano_saude_dependentes`, serão apresentados os dependentes com seus respectivos valores de Plano de Saúde.
# MAGIC
# MAGIC A consulta apresentará, para cada dependente:
# MAGIC
# MAGIC - `drt` do empregado titular;
# MAGIC - nome do empregado titular;
# MAGIC - nome do dependente;
# MAGIC - parentesco;
# MAGIC - data de nascimento do dependente;
# MAGIC - data de referência utilizada no cálculo;
# MAGIC - idade do dependente na data de referência;
# MAGIC - valor individual do Plano de Saúde.
# MAGIC
# MAGIC A consulta utiliza as mesmas regras aplicadas anteriormente para o cálculo de `plano_saude_dependentes` e possui exclusivamente finalidade de conferência, sem realizar alterações nas tabelas Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH dependentes_referencia AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         e.nome AS nome_titular,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN e.data_desligamento IS NOT NULL
# MAGIC                 THEN e.data_desligamento
# MAGIC             ELSE DATE('2025-10-01')
# MAGIC         END AS data_referencia
# MAGIC
# MAGIC     FROM workspace.silver.dependentes_anonimizados AS d
# MAGIC
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados AS e
# MAGIC         ON d.drt = e.drt
# MAGIC ),
# MAGIC
# MAGIC dependentes_idade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_titular,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         data_referencia,
# MAGIC
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(data_referencia, data_nascimento) / 12
# MAGIC         ) AS idade,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN MONTH(data_referencia) >= 10
# MAGIC                 THEN YEAR(data_referencia)
# MAGIC             ELSE YEAR(data_referencia) - 1
# MAGIC         END AS ano_vigencia
# MAGIC
# MAGIC     FROM dependentes_referencia
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome_titular,
# MAGIC     nome_dependente,
# MAGIC     parentesco,
# MAGIC     data_nascimento,
# MAGIC     data_referencia,
# MAGIC     idade,
# MAGIC
# MAGIC     CAST(
# MAGIC         CASE
# MAGIC             WHEN ano_vigencia >= 2022 THEN
# MAGIC                 CASE
# MAGIC                     WHEN idade <= 18 THEN 395.74
# MAGIC                     WHEN idade <= 23 THEN 466.97
# MAGIC                     WHEN idade <= 28 THEN 565.03
# MAGIC                     WHEN idade <= 33 THEN 678.04
# MAGIC                     WHEN idade <= 38 THEN 772.96
# MAGIC                     WHEN idade <= 43 THEN 796.16
# MAGIC                     WHEN idade <= 48 THEN 969.36
# MAGIC                     WHEN idade <= 53 THEN 1140.16
# MAGIC                     WHEN idade <= 58 THEN 1356.80
# MAGIC                     ELSE 2374.40
# MAGIC                 END
# MAGIC
# MAGIC             WHEN ano_vigencia = 2021 THEN
# MAGIC                 CASE
# MAGIC                     WHEN idade <= 18 THEN 569.48
# MAGIC                     WHEN idade <= 23 THEN 834.27
# MAGIC                     WHEN idade <= 28 THEN 959.43
# MAGIC                     WHEN idade <= 33 THEN 1094.17
# MAGIC                     WHEN idade <= 38 THEN 1128.48
# MAGIC                     WHEN idade <= 43 THEN 1290.33
# MAGIC                     WHEN idade <= 48 THEN 1392.82
# MAGIC                     WHEN idade <= 53 THEN 1838.51
# MAGIC                     WHEN idade <= 58 THEN 2138.23
# MAGIC                     ELSE 3404.04
# MAGIC                 END
# MAGIC
# MAGIC             WHEN ano_vigencia = 2020 THEN
# MAGIC                 CASE
# MAGIC                     WHEN idade <= 18 THEN 520.79
# MAGIC                     WHEN idade <= 23 THEN 762.94
# MAGIC                     WHEN idade <= 28 THEN 877.39
# MAGIC                     WHEN idade <= 33 THEN 1000.61
# MAGIC                     WHEN idade <= 38 THEN 1031.99
# MAGIC                     WHEN idade <= 43 THEN 1180.00
# MAGIC                     WHEN idade <= 48 THEN 1273.73
# MAGIC                     WHEN idade <= 53 THEN 1681.31
# MAGIC                     WHEN idade <= 58 THEN 1955.40
# MAGIC                     ELSE 3112.98
# MAGIC                 END
# MAGIC
# MAGIC             WHEN ano_vigencia = 2019 THEN
# MAGIC                 CASE
# MAGIC                     WHEN idade <= 18 THEN 461.37
# MAGIC                     WHEN idade <= 23 THEN 675.89
# MAGIC                     WHEN idade <= 28 THEN 777.28
# MAGIC                     WHEN idade <= 33 THEN 886.44
# MAGIC                     WHEN idade <= 38 THEN 914.24
# MAGIC                     WHEN idade <= 43 THEN 1045.36
# MAGIC                     WHEN idade <= 48 THEN 1128.40
# MAGIC                     WHEN idade <= 53 THEN 1489.47
# MAGIC                     WHEN idade <= 58 THEN 1732.28
# MAGIC                     ELSE 2757.79
# MAGIC                 END
# MAGIC
# MAGIC             ELSE
# MAGIC                 CASE
# MAGIC                     WHEN idade <= 18 THEN 401.68
# MAGIC                     WHEN idade <= 23 THEN 588.44
# MAGIC                     WHEN idade <= 28 THEN 676.72
# MAGIC                     WHEN idade <= 33 THEN 771.76
# MAGIC                     WHEN idade <= 38 THEN 795.96
# MAGIC                     WHEN idade <= 43 THEN 910.12
# MAGIC                     WHEN idade <= 48 THEN 982.41
# MAGIC                     WHEN idade <= 53 THEN 1296.77
# MAGIC                     WHEN idade <= 58 THEN 1508.17
# MAGIC                     ELSE 2401.00
# MAGIC                 END
# MAGIC         END
# MAGIC         AS DECIMAL(15,2)
# MAGIC     ) AS valor_plano_saude
# MAGIC
# MAGIC FROM dependentes_idade
# MAGIC
# MAGIC ORDER BY drt, nome_dependente;