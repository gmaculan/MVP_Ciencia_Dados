# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição da estrutura da dimensão de saúde
# MAGIC
# MAGIC A `dim_saude` será construída a partir da estrutura histórica utilizada para registrar os valores dos planos de saúde até 2022.
# MAGIC
# MAGIC Essa estrutura será preservada na camada Gold e ampliada com os valores disponíveis a partir de 2022, permitindo manter em uma única dimensão a evolução dos preços dos planos e de suas respectivas faixas etárias.
# MAGIC
# MAGIC A tabela posterior a 2022 não será tratada como uma estrutura independente. Seus valores serão incorporados à estrutura histórica existente, respeitando a correspondência entre os planos e as faixas etárias.
# MAGIC
# MAGIC Os campos `Quantidade` e `Valor Total (R$)` existentes na fonte posterior a 2022 não serão incorporados à dimensão. Esses campos representam a quantidade de beneficiários observada e o valor total decorrente dessa quantidade em determinado momento, não constituindo parâmetros da tabela de preços dos planos.
# MAGIC
# MAGIC A dimensão deverá preservar os valores de todas as faixas etárias, inclusive quando não houver atualmente beneficiários em determinada faixa. Isso permitirá calcular o custo de novos beneficiários e atualizar o custo de beneficiários existentes quando ocorrer mudança de faixa etária.
# MAGIC
# MAGIC Os planos possuem data-base anual no início de outubro. Novos valores deverão ser incorporados à estrutura preservando as vigências anteriores, permitindo consultas históricas e futuras atualizações da tabela de preços.
# MAGIC
# MAGIC O IOF aplicável aos valores posteriores a 2022 permanece em **2,38%**.
# MAGIC
# MAGIC A alíquota de reajuste correspondente à nova vigência poderá ser obtida pela comparação entre os valores anteriores e posteriores disponíveis nas fontes, sendo tratada como informação derivada quando não estiver explicitamente registrada na origem.
# MAGIC
# MAGIC Nesta etapa, a fonte posterior a 2022 será incorporada conceitualmente à estrutura histórica para que seja definida a carga da `dim_saude`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH fonte AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         `Rede: Nacional` AS faixa_etaria,
# MAGIC         `Região: Rio de Janeiro` AS valor_unitario_saude,
# MAGIC         ROW_NUMBER() OVER (ORDER BY monotonically_increasing_id()) AS ordem
# MAGIC     FROM workspace.bronze.plano_saude_vital_de_2022_em_diante
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC marcacao_plano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         MAX(
# MAGIC             CASE
# MAGIC                 WHEN faixa_etaria = 'Rede: Premium' THEN ordem
# MAGIC             END
# MAGIC         ) OVER () AS inicio_executivo
# MAGIC     FROM fonte
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC valores AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CASE
# MAGIC             WHEN ordem < inicio_executivo THEN 'ESPECIAL'
# MAGIC             WHEN ordem > inicio_executivo THEN 'EXECUTIVO'
# MAGIC         END AS plano,
# MAGIC
# MAGIC         faixa_etaria,
# MAGIC
# MAGIC         CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     TRIM(valor_unitario_saude),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             ) AS DECIMAL(15,2)
# MAGIC         ) AS valor_saude
# MAGIC
# MAGIC     FROM marcacao_plano
# MAGIC
# MAGIC     WHERE
# MAGIC         (
# MAGIC             ordem < inicio_executivo
# MAGIC             OR ordem > inicio_executivo
# MAGIC         )
# MAGIC         AND faixa_etaria NOT IN ('Faixa Etária', 'Total')
# MAGIC         AND faixa_etaria IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC faixas AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         plano,
# MAGIC
# MAGIC         CASE faixa_etaria
# MAGIC             WHEN 'Até 18 anos' THEN 0
# MAGIC             WHEN '19 a 23' THEN 19
# MAGIC             WHEN '24 a 28' THEN 24
# MAGIC             WHEN '29 a 33' THEN 29
# MAGIC             WHEN '34 a 38' THEN 34
# MAGIC             WHEN '39 a 43' THEN 39
# MAGIC             WHEN '44 a 48' THEN 44
# MAGIC             WHEN '49 a 53' THEN 49
# MAGIC             WHEN '54 a 58' THEN 54
# MAGIC             WHEN '59 adiante' THEN 59
# MAGIC         END AS idade_inicial,
# MAGIC
# MAGIC         valor_saude
# MAGIC
# MAGIC     FROM valores
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     plano,
# MAGIC     idade_inicial,
# MAGIC     valor_saude
# MAGIC FROM faixas
# MAGIC WHERE idade_inicial IS NOT NULL
# MAGIC ORDER BY
# MAGIC     plano,
# MAGIC     idade_inicial;

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Conclusão da Definição da estrutura da dimensão de saúde
# MAGIC
# MAGIC A análise da fonte posterior a 2022 confirmou que os valores podem ser incorporados à estrutura histórica utilizada até 2022.
# MAGIC
# MAGIC Foram identificadas **20 combinações de plano e faixa etária**, distribuídas da seguinte forma:
# MAGIC
# MAGIC - **10 faixas etárias** para o plano `ESPECIAL`;
# MAGIC - **10 faixas etárias** para o plano `EXECUTIVO`.
# MAGIC
# MAGIC Em ambos os planos foram identificadas as mesmas idades iniciais de faixa:
# MAGIC
# MAGIC `0, 19, 24, 29, 34, 39, 44, 49, 54 e 59 anos`.
# MAGIC
# MAGIC Os campos relacionados à quantidade de beneficiários e ao valor total foram desconsiderados, permanecendo apenas os valores unitários necessários à tabela de referência dos planos.
# MAGIC
# MAGIC Dessa forma, a fonte posterior a 2022 pode ser incorporada à estrutura histórica existente, preservando a organização por plano, faixa etária e vigência.
# MAGIC
# MAGIC Antes da criação da `dim_saude`, os novos valores serão comparados com os últimos valores disponíveis na estrutura histórica até 2022. Essa comparação permitirá calcular a alíquota de reajuste correspondente à nova vigência.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Cálculo do reajuste para incorporação da nova vigência
# MAGIC
# MAGIC Para incorporar os valores posteriores a 2022 à estrutura histórica, será realizada a comparação entre os novos valores e os últimos valores disponíveis na tabela de referência anterior.
# MAGIC
# MAGIC A comparação será feita individualmente para cada combinação de plano e faixa etária.
# MAGIC
# MAGIC A alíquota de reajuste será calculada por:
# MAGIC
# MAGIC **reajuste = (valor novo / valor anterior) - 1**
# MAGIC
# MAGIC O resultado permitirá verificar a variação observada entre as duas referências e preparar a nova vigência para incorporação à `dim_saude`.
# MAGIC
# MAGIC O IOF de **2,38%** será preservado como componente próprio da estrutura e não será confundido com a alíquota de reajuste do plano.
# MAGIC
# MAGIC Nesta etapa será realizado somente o cálculo e a conferência dos valores, sem criação ou alteração de tabelas na camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH historico_2022 AS (
# MAGIC
# MAGIC     SELECT *
# MAGIC     FROM VALUES
# MAGIC
# MAGIC         ('ESPECIAL',   0, CAST(679.96  AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  19, CAST(996.12  AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  24, CAST(1145.55 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  29, CAST(1306.43 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  34, CAST(1347.40 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  39, CAST(1540.65 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  44, CAST(1663.03 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  49, CAST(2195.18 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  54, CAST(2553.04 AS DECIMAL(15,2))),
# MAGIC         ('ESPECIAL',  59, CAST(4064.42 AS DECIMAL(15,2))),
# MAGIC
# MAGIC         ('EXECUTIVO',  0, CAST(1520.98 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 19, CAST(2749.44 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 24, CAST(2859.42 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 29, CAST(3088.20 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 34, CAST(3242.57 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 39, CAST(3534.42 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 44, CAST(3718.79 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 49, CAST(4942.24 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 54, CAST(5710.79 AS DECIMAL(15,2))),
# MAGIC         ('EXECUTIVO', 59, CAST(9091.57 AS DECIMAL(15,2)))
# MAGIC
# MAGIC     AS t(plano, idade_inicial, valor_jul_2022)
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC fonte_nova AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         `Rede: Nacional` AS faixa_etaria,
# MAGIC         `Região: Rio de Janeiro` AS valor_unitario_saude,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY monotonically_increasing_id()
# MAGIC         ) AS ordem
# MAGIC
# MAGIC     FROM workspace.bronze.plano_saude_vital_de_2022_em_diante
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC marcacao_plano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         MAX(
# MAGIC             CASE
# MAGIC                 WHEN faixa_etaria = 'Rede: Premium'
# MAGIC                 THEN ordem
# MAGIC             END
# MAGIC         ) OVER () AS inicio_executivo
# MAGIC
# MAGIC     FROM fonte_nova
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC valores_novos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CASE
# MAGIC             WHEN ordem < inicio_executivo THEN 'ESPECIAL'
# MAGIC             WHEN ordem > inicio_executivo THEN 'EXECUTIVO'
# MAGIC         END AS plano,
# MAGIC
# MAGIC         CASE faixa_etaria
# MAGIC             WHEN 'Até 18 anos' THEN 0
# MAGIC             WHEN '19 a 23'     THEN 19
# MAGIC             WHEN '24 a 28'     THEN 24
# MAGIC             WHEN '29 a 33'     THEN 29
# MAGIC             WHEN '34 a 38'     THEN 34
# MAGIC             WHEN '39 a 43'     THEN 39
# MAGIC             WHEN '44 a 48'     THEN 44
# MAGIC             WHEN '49 a 53'     THEN 49
# MAGIC             WHEN '54 a 58'     THEN 54
# MAGIC             WHEN '59 adiante'  THEN 59
# MAGIC         END AS idade_inicial,
# MAGIC
# MAGIC         CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     TRIM(valor_unitario_saude),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             ) AS DECIMAL(15,2)
# MAGIC         ) AS valor_novo
# MAGIC
# MAGIC     FROM marcacao_plano
# MAGIC
# MAGIC     WHERE
# MAGIC         (
# MAGIC             ordem < inicio_executivo
# MAGIC             OR ordem > inicio_executivo
# MAGIC         )
# MAGIC         AND faixa_etaria NOT IN ('Faixa Etária', 'Total')
# MAGIC         AND faixa_etaria IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC comparacao AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         h.plano,
# MAGIC         h.idade_inicial,
# MAGIC         h.valor_jul_2022,
# MAGIC         n.valor_novo,
# MAGIC
# MAGIC         ROUND(
# MAGIC             (n.valor_novo / h.valor_jul_2022 - 1) * 100,
# MAGIC             2
# MAGIC         ) AS reajuste_percentual
# MAGIC
# MAGIC     FROM historico_2022 h
# MAGIC
# MAGIC     INNER JOIN valores_novos n
# MAGIC         ON  h.plano = n.plano
# MAGIC         AND h.idade_inicial = n.idade_inicial
# MAGIC
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     plano,
# MAGIC     idade_inicial,
# MAGIC     valor_jul_2022,
# MAGIC     valor_novo,
# MAGIC     reajuste_percentual
# MAGIC
# MAGIC FROM comparacao
# MAGIC
# MAGIC ORDER BY
# MAGIC     plano,
# MAGIC     idade_inicial;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão do Cálculo do reajuste para incorporação da nova vigência
# MAGIC
# MAGIC A comparação entre os últimos valores disponíveis na estrutura histórica até 2022 e os valores da tabela posterior a 2022 identificou uma descontinuidade entre as duas referências.
# MAGIC
# MAGIC Essa descontinuidade decorre da **troca da operadora do plano de saúde**. Por simplificação adotada no MVP, as duas operadoras foram tratadas como uma única empresa, embora os valores disponíveis antes e depois da mudança pertençam a estruturas comerciais distintas.
# MAGIC
# MAGIC Consequentemente, a variação entre o último valor da operadora anterior e o primeiro valor da nova operadora **não será interpretada como reajuste do plano**.
# MAGIC
# MAGIC Para essa transição, o campo de reajuste permanecerá sem valor (`NULL`), evitando a criação de uma alíquota artificial a partir de preços que não são diretamente comparáveis.
# MAGIC
# MAGIC Os reajustes existentes nos períodos anteriores serão preservados conforme disponíveis na fonte histórica. Da mesma forma, reajustes posteriores poderão ser mantidos quando houver valores sucessivos comparáveis dentro da nova estrutura.
# MAGIC
# MAGIC A tabela posterior a 2022 será incorporada à estrutura histórica como continuidade da referência de preços utilizada pelo MVP, mantendo-se essa simplificação explicitamente documentada.
# MAGIC
# MAGIC Os valores posteriores a 2022 serão considerados valores-base do plano, sem inclusão de IOF. O IOF será mantido separadamente, com alíquota de **2,38%**, salvo indicação explícita em contrário na fonte.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Definição da carga da dimensão de saúde
# MAGIC
# MAGIC A `dim_saude` será construída preservando a estrutura histórica utilizada para os valores dos planos de saúde até 2022 e incorporando os valores posteriores à troca de operadora.
# MAGIC
# MAGIC Por simplificação do MVP, as duas operadoras serão representadas de forma contínua na mesma dimensão, sem criação de estruturas distintas por operadora.
# MAGIC
# MAGIC A dimensão preservará os valores correspondentes aos planos e às respectivas faixas etárias ao longo do tempo. Dessa forma, será possível utilizar a tabela de referência adequada ao período analisado e determinar o valor aplicável de acordo com a idade do titular ou dependente.
# MAGIC
# MAGIC Os valores históricos e seus reajustes serão preservados quando disponíveis na fonte. Na transição entre as operadoras, entretanto, o reajuste permanecerá `NULL`, pois os preços anteriores e posteriores não são diretamente comparáveis como reajustes sucessivos de um mesmo contrato.
# MAGIC
# MAGIC Os reajustes posteriores à mudança de operadora poderão ser incorporados normalmente quando houver dados comparáveis entre vigências sucessivas.
# MAGIC
# MAGIC Os campos `Quantidade` e `Valor Total (R$)` da fonte posterior a 2022 não serão utilizados, pois representam a utilização observada em determinado momento e não parâmetros da tabela de preços.
# MAGIC
# MAGIC Os valores da fonte posterior a 2022 serão tratados como valores-base, sem IOF. A alíquota de IOF será mantida separadamente em **2,38%**, permitindo seu tratamento específico nos cálculos de custo.
# MAGIC
# MAGIC Nesta etapa será preparada a estrutura consolidada que servirá de base para a criação da `dim_saude`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.dim_saude
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH fonte_nova AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         `Rede: Nacional` AS faixa_etaria,
# MAGIC         `Região: Rio de Janeiro` AS valor_unitario_saude,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY monotonically_increasing_id()
# MAGIC         ) AS ordem
# MAGIC
# MAGIC     FROM workspace.bronze.plano_saude_vital_de_2022_em_diante
# MAGIC ),
# MAGIC
# MAGIC marcacao_plano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         MAX(
# MAGIC             CASE
# MAGIC                 WHEN faixa_etaria = 'Rede: Premium'
# MAGIC                 THEN ordem
# MAGIC             END
# MAGIC         ) OVER () AS inicio_executivo
# MAGIC
# MAGIC     FROM fonte_nova
# MAGIC ),
# MAGIC
# MAGIC valores_novos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CASE
# MAGIC             WHEN ordem < inicio_executivo THEN 'ESPECIAL'
# MAGIC             WHEN ordem > inicio_executivo THEN 'EXECUTIVO'
# MAGIC         END AS plano,
# MAGIC
# MAGIC         CASE faixa_etaria
# MAGIC             WHEN 'Até 18 anos' THEN 0
# MAGIC             WHEN '19 a 23'     THEN 19
# MAGIC             WHEN '24 a 28'     THEN 24
# MAGIC             WHEN '29 a 33'     THEN 29
# MAGIC             WHEN '34 a 38'     THEN 34
# MAGIC             WHEN '39 a 43'     THEN 39
# MAGIC             WHEN '44 a 48'     THEN 44
# MAGIC             WHEN '49 a 53'     THEN 49
# MAGIC             WHEN '54 a 58'     THEN 54
# MAGIC             WHEN '59 adiante'  THEN 59
# MAGIC         END AS idade_inicial,
# MAGIC
# MAGIC         TRIM(valor_unitario_saude) AS valor_saude
# MAGIC
# MAGIC     FROM marcacao_plano
# MAGIC
# MAGIC     WHERE
# MAGIC         (ordem < inicio_executivo OR ordem > inicio_executivo)
# MAGIC         AND faixa_etaria NOT IN ('Faixa Etária', 'Total')
# MAGIC         AND faixa_etaria IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC valores_pivotados AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 0  THEN valor_saude END) AS esp_0,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 19 THEN valor_saude END) AS esp_19,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 24 THEN valor_saude END) AS esp_24,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 29 THEN valor_saude END) AS esp_29,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 34 THEN valor_saude END) AS esp_34,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 39 THEN valor_saude END) AS esp_39,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 44 THEN valor_saude END) AS esp_44,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 49 THEN valor_saude END) AS esp_49,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 54 THEN valor_saude END) AS esp_54,
# MAGIC         MAX(CASE WHEN plano = 'ESPECIAL' AND idade_inicial = 59 THEN valor_saude END) AS esp_59,
# MAGIC
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 0  THEN valor_saude END) AS exe_0,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 19 THEN valor_saude END) AS exe_19,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 24 THEN valor_saude END) AS exe_24,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 29 THEN valor_saude END) AS exe_29,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 34 THEN valor_saude END) AS exe_34,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 39 THEN valor_saude END) AS exe_39,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 44 THEN valor_saude END) AS exe_44,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 49 THEN valor_saude END) AS exe_49,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 54 THEN valor_saude END) AS exe_54,
# MAGIC         MAX(CASE WHEN plano = 'EXECUTIVO' AND idade_inicial = 59 THEN valor_saude END) AS exe_59
# MAGIC
# MAGIC     FROM valores_novos
# MAGIC ),
# MAGIC
# MAGIC historico_numerado AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         h.*,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY monotonically_increasing_id()
# MAGIC         ) AS ordem_historico
# MAGIC
# MAGIC     FROM workspace.bronze.plano_saude_ate_2022 h
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     h.`MÊS REF.` AS mes_ref,
# MAGIC     h.* EXCEPT (`MÊS REF.`),
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(h.`MÊS REF.`) = 'PLANO:' THEN
# MAGIC             'VITAL'
# MAGIC
# MAGIC         WHEN TRIM(h.`MÊS REF.`) = 'REAJUSTE:' THEN
# MAGIC             NULL
# MAGIC
# MAGIC         WHEN TRIM(h.`MÊS REF.`) = 'IOF:' THEN
# MAGIC             '2,38%'
# MAGIC
# MAGIC         WHEN h.ordem_historico BETWEEN 6 AND 15 THEN
# MAGIC             CASE TRIM(h.`MÊS REF.`)
# MAGIC                 WHEN '0'  THEN CONCAT('R$ ', v.esp_0)
# MAGIC                 WHEN '19' THEN CONCAT('R$ ', v.esp_19)
# MAGIC                 WHEN '24' THEN CONCAT('R$ ', v.esp_24)
# MAGIC                 WHEN '29' THEN CONCAT('R$ ', v.esp_29)
# MAGIC                 WHEN '34' THEN CONCAT('R$ ', v.esp_34)
# MAGIC                 WHEN '39' THEN CONCAT('R$ ', v.esp_39)
# MAGIC                 WHEN '44' THEN CONCAT('R$ ', v.esp_44)
# MAGIC                 WHEN '49' THEN CONCAT('R$ ', v.esp_49)
# MAGIC                 WHEN '54' THEN CONCAT('R$ ', v.esp_54)
# MAGIC                 WHEN '59' THEN CONCAT('R$ ', v.esp_59)
# MAGIC             END
# MAGIC
# MAGIC         WHEN h.ordem_historico = 16 THEN
# MAGIC             CONCAT('R$ ', v.esp_59)
# MAGIC
# MAGIC         WHEN h.ordem_historico BETWEEN 19 AND 28 THEN
# MAGIC             CASE TRIM(h.`MÊS REF.`)
# MAGIC                 WHEN '0'  THEN CONCAT('R$ ', v.exe_0)
# MAGIC                 WHEN '19' THEN CONCAT('R$ ', v.exe_19)
# MAGIC                 WHEN '24' THEN CONCAT('R$ ', v.exe_24)
# MAGIC                 WHEN '29' THEN CONCAT('R$ ', v.exe_29)
# MAGIC                 WHEN '34' THEN CONCAT('R$ ', v.exe_34)
# MAGIC                 WHEN '39' THEN CONCAT('R$ ', v.exe_39)
# MAGIC                 WHEN '44' THEN CONCAT('R$ ', v.exe_44)
# MAGIC                 WHEN '49' THEN CONCAT('R$ ', v.exe_49)
# MAGIC                 WHEN '54' THEN CONCAT('R$ ', v.exe_54)
# MAGIC                 WHEN '59' THEN CONCAT('R$ ', v.exe_59)
# MAGIC             END
# MAGIC
# MAGIC         WHEN h.ordem_historico = 29 THEN
# MAGIC             CONCAT('R$ ', v.exe_59)
# MAGIC
# MAGIC         ELSE NULL
# MAGIC
# MAGIC     END AS `24-10-22`
# MAGIC
# MAGIC FROM historico_numerado h
# MAGIC
# MAGIC CROSS JOIN valores_pivotados v;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Definição da carga da dimensão de saúde
# MAGIC
# MAGIC A estrutura da `dim_saude` foi consolidada preservando o histórico disponível dos valores dos planos de saúde e incorporando a nova referência decorrente da troca de operadora ocorrida em **24/10/2022**.
# MAGIC
# MAGIC A estrutura histórica foi mantida conforme os dados disponíveis na origem, inclusive nos casos em que determinadas combinações de período e faixa etária não possuem valor registrado. Esses dados ausentes foram preservados, sem preenchimento, interpolação ou criação de valores não existentes na fonte.
# MAGIC
# MAGIC Os valores da nova operadora foram incorporados às mesmas faixas etárias dos planos `ESPECIAL` e `EXECUTIVO`, permitindo a continuidade da estrutura utilizada no MVP. Por simplificação do projeto, as duas operadoras são tratadas de forma contínua na dimensão, embora representem estruturas comerciais distintas.
# MAGIC
# MAGIC Na referência de **24/10/2022**, o campo de reajuste foi mantido como `NULL`, pois a diferença em relação aos valores anteriores decorre da troca de operadora e não representa um reajuste diretamente comparável. Os reajustes existentes antes dessa transição permanecem preservados, assim como poderão ser incorporados reajustes posteriores quando houver dados comparáveis entre vigências sucessivas.
# MAGIC
# MAGIC O IOF aplicável à nova referência foi mantido em **2,38%**, separado do valor-base do plano. Os valores posteriores a 2022 foram considerados valores-base, sem inclusão do IOF, salvo indicação explícita em contrário na fonte.
# MAGIC
# MAGIC Os campos de quantidade de beneficiários e valor total existentes na fonte posterior a 2022 não foram incorporados, pois representam utilização observada em determinado momento e não parâmetros da tabela de preços.
# MAGIC
# MAGIC Com essa consolidação, a `dim_saude` preserva as referências necessárias para determinar os valores dos planos de saúde por período, plano e faixa etária, fornecendo a base para o cálculo posterior dos custos de saúde de titulares e dependentes na camada Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação da dimensão de saúde persistida
# MAGIC
# MAGIC Após a consolidação das referências históricas e da nova operadora, a `dim_saude` foi persistida na camada Gold.
# MAGIC
# MAGIC Nesta etapa será verificada a estrutura da tabela criada, confirmando sua disponibilidade para utilização posterior no cálculo dos custos de saúde dos titulares e dependentes.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC DESCRIBE workspace.gold.dim_saude;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação da dimensão de saúde persistida
# MAGIC
# MAGIC A `dim_saude` foi persistida com sucesso na camada Gold como `workspace.gold.dim_saude`.
# MAGIC
# MAGIC A dimensão preserva a estrutura histórica disponível na origem, contendo as referências de valores dos planos de saúde entre `out-09` e `jul-22`, além da nova referência correspondente à troca de operadora em `24-10-22`.
# MAGIC
# MAGIC O campo original de referência foi normalizado para `mes_ref`, permitindo a persistência da tabela em formato Delta sem alterar o conteúdo analítico da dimensão.
# MAGIC
# MAGIC A coluna `ordem_historico` foi mantida como apoio à organização da estrutura consolidada.
# MAGIC
# MAGIC Com a dimensão persistida, as referências históricas de plano, faixa etária, valores e IOF passam a estar disponíveis na camada Gold para o cálculo posterior dos custos de saúde dos titulares e dependentes.