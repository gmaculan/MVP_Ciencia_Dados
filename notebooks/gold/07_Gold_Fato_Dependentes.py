# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da base histórica da Fato_Dependentes
# MAGIC
# MAGIC A `Fato_Dependentes` será construída com histórico anual, diferentemente das tabelas Bronze e Silver de dependentes, que representam o cadastro disponível na fonte.
# MAGIC
# MAGIC O grão definido para a fato é:
# MAGIC
# MAGIC **uma linha por dependente × DRT × ano.**
# MAGIC
# MAGIC O DRT identifica o vínculo empregatício do titular ao qual o dependente está associado.
# MAGIC
# MAGIC A tabela `workspace.silver.dependentes_anonimizados` fornece os dados cadastrais do dependente, incluindo nome, parentesco e data de nascimento. As datas de admissão e desligamento do vínculo serão obtidas da tabela `workspace.silver.empregados_anonimizados`.
# MAGIC
# MAGIC Como a fonte de dependentes não possui datas próprias de inclusão e exclusão no plano de saúde, será adotada como premissa do MVP a utilização do período do vínculo empregatício do titular como limite temporal do histórico do dependente.
# MAGIC
# MAGIC O início do período considerado para cada dependente será a maior data entre:
# MAGIC
# MAGIC - a data de admissão do titular;
# MAGIC - a data de nascimento do dependente.
# MAGIC
# MAGIC Dessa forma, não serão gerados registros anteriores à existência do vínculo empregatício nem anteriores ao nascimento do dependente.
# MAGIC
# MAGIC Quando houver data de desligamento, ela determinará o limite final do histórico. Para vínculos sem data de desligamento, será utilizado como limite o último ano disponível nas referências históricas de custo utilizadas pelo projeto.
# MAGIC
# MAGIC Nesta primeira etapa será construída e validada somente a base histórica dependente × DRT × ano. O cálculo da idade, da faixa etária e do custo do plano de saúde será realizado posteriormente.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_historico AS (
# MAGIC     SELECT MAX(ano) AS ultimo_ano
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC base_dependentes AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         GREATEST(e.data_admissao, d.data_nascimento) AS data_inicio_historico,
# MAGIC         COALESCE(
# MAGIC             e.data_desligamento,
# MAGIC             MAKE_DATE(l.ultimo_ano, 12, 31)
# MAGIC         ) AS data_fim_historico
# MAGIC     FROM workspace.silver.dependentes_anonimizados d
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados e
# MAGIC         ON d.drt = e.drt
# MAGIC     CROSS JOIN limite_historico l
# MAGIC ),
# MAGIC
# MAGIC historico_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 YEAR(data_inicio_historico),
# MAGIC                 YEAR(data_fim_historico)
# MAGIC             )
# MAGIC         ) AS ano
# MAGIC     FROM base_dependentes
# MAGIC     WHERE data_inicio_historico <= data_fim_historico
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome_dependente,
# MAGIC     parentesco,
# MAGIC     data_nascimento,
# MAGIC     ano
# MAGIC FROM historico_dependentes
# MAGIC ORDER BY drt, nome_dependente, ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Conclusão da Construção da base histórica da Fato_Dependentes
# MAGIC
# MAGIC A construção inicial da base histórica resultou em:
# MAGIC
# MAGIC - **712 registros dependente × DRT × ano**;
# MAGIC - **218 dependentes distintos**;
# MAGIC - **130 DRTs distintos**;
# MAGIC - período histórico entre **2010 e 2026**;
# MAGIC - nenhuma duplicidade no grão dependente × DRT × ano;
# MAGIC - nenhum valor nulo nos atributos produzidos.
# MAGIC
# MAGIC Os 218 dependentes existentes na tabela Silver foram preservados na expansão histórica.
# MAGIC
# MAGIC O histórico foi delimitado pelo vínculo empregatício do titular e pela data de nascimento do dependente, conforme as premissas estabelecidas para o MVP.
# MAGIC
# MAGIC Antes do cálculo dos custos, será realizada uma validação dos limites temporais da expansão para confirmar que não foram produzidos registros anteriores à admissão do titular, anteriores ao nascimento do dependente ou posteriores ao desligamento do vínculo.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_historico AS (
# MAGIC     SELECT MAX(ano) AS ultimo_ano
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC base_dependentes AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         GREATEST(e.data_admissao, d.data_nascimento) AS data_inicio_historico,
# MAGIC         COALESCE(
# MAGIC             e.data_desligamento,
# MAGIC             MAKE_DATE(l.ultimo_ano, 12, 31)
# MAGIC         ) AS data_fim_historico
# MAGIC     FROM workspace.silver.dependentes_anonimizados d
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados e
# MAGIC         ON d.drt = e.drt
# MAGIC     CROSS JOIN limite_historico l
# MAGIC ),
# MAGIC
# MAGIC historico_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 YEAR(data_inicio_historico),
# MAGIC                 YEAR(data_fim_historico)
# MAGIC             )
# MAGIC         ) AS ano
# MAGIC     FROM base_dependentes
# MAGIC     WHERE data_inicio_historico <= data_fim_historico
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC     COUNT(DISTINCT CONCAT(CAST(drt AS STRING), '|', nome_dependente)) AS total_dependentes,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(DISTINCT CONCAT(CAST(drt AS STRING), '|', nome_dependente, '|', CAST(ano AS STRING)))
# MAGIC         AS duplicidades,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN ano < YEAR(data_admissao) THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS anterior_admissao,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN ano < YEAR(data_nascimento) THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS anterior_nascimento,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN data_desligamento IS NOT NULL
# MAGIC          AND ano > YEAR(data_desligamento) THEN 1
# MAGIC         ELSE 0
# MAGIC     END) AS posterior_desligamento,
# MAGIC
# MAGIC     MIN(ano) AS primeiro_ano,
# MAGIC     MAX(ano) AS ultimo_ano
# MAGIC
# MAGIC FROM historico_dependentes;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Validação dos limites temporais do histórico de dependentes
# MAGIC
# MAGIC A validação confirmou a consistência da expansão histórica dos dependentes.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **712 registros dependente × DRT × ano**;
# MAGIC - **218 dependentes distintos**;
# MAGIC - **130 DRTs distintos**;
# MAGIC - período histórico entre **2010 e 2026**;
# MAGIC - **0 duplicidades** no grão dependente × DRT × ano;
# MAGIC - **0 registros anteriores à admissão do titular**;
# MAGIC - **0 registros anteriores ao nascimento do dependente**;
# MAGIC - **0 registros posteriores ao desligamento do titular**.
# MAGIC
# MAGIC Dessa forma, os limites temporais definidos para a construção do histórico foram respeitados.
# MAGIC
# MAGIC A base histórica anual está validada e poderá ser utilizada nas próximas etapas para o cálculo da idade e do custo histórico do plano de saúde de cada dependente.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT *
# MAGIC FROM workspace.gold.dim_saude
# MAGIC WHERE UPPER(TRIM(mes_ref)) LIKE 'IOF%';

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Cálculo histórico do custo do plano de saúde dos dependentes
# MAGIC
# MAGIC Nesta etapa será calculado o custo histórico do plano de saúde de cada dependente.
# MAGIC
# MAGIC Todos os dependentes são considerados pertencentes ao plano **ESPECIAL**, conforme a regra de negócio definida para o MVP. Por esse motivo, o tipo de plano não será armazenado como atributo da `Fato_Dependentes`.
# MAGIC
# MAGIC O cálculo será realizado mensalmente, pois o valor do plano pode variar ao longo de um mesmo ano em função de:
# MAGIC
# MAGIC - mudança da idade do dependente e, consequentemente, de sua faixa etária;
# MAGIC - entrada em vigor de uma nova referência de preços do plano de saúde.
# MAGIC
# MAGIC Para cada mês em que o dependente estiver compreendido no período histórico definido, será determinada sua idade e a correspondente faixa etária. Em seguida, será utilizado o valor histórico aplicável existente na `Dim_Saude`.
# MAGIC
# MAGIC A `Dim_Saude` registra **IOF de 2,38% em todas as referências históricas disponíveis**. Dessa forma, o custo mensal do plano de saúde será calculado pela aplicação do IOF sobre o respectivo valor-base:
# MAGIC
# MAGIC **Custo do plano de saúde = Valor-base × 1,0238**
# MAGIC
# MAGIC Esse mesmo critério será aplicado aos titulares e aos dependentes, garantindo uniformidade no tratamento do custo do plano de saúde nas estruturas Gold.
# MAGIC
# MAGIC Após o cálculo mensal, os valores serão consolidados por dependente, DRT e ano, produzindo o **custo mensal médio do plano de saúde do dependente no respectivo ano**.
# MAGIC
# MAGIC A utilização da granularidade mensal durante o cálculo permite representar mudanças ocorridas dentro do ano sem alterar o grão anual definido para a fato.
# MAGIC
# MAGIC Valores não disponíveis nas referências históricas de saúde deverão permanecer como `NULL`, sem criação ou extrapolação de custos inexistentes na fonte.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_historico AS (
# MAGIC     SELECT MAX(data) AS ultima_data
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC base_dependentes AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         GREATEST(e.data_admissao, d.data_nascimento) AS data_inicio_historico,
# MAGIC         LEAST(
# MAGIC             COALESCE(e.data_desligamento, l.ultima_data),
# MAGIC             l.ultima_data
# MAGIC         ) AS data_fim_historico
# MAGIC     FROM workspace.silver.dependentes_anonimizados d
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados e
# MAGIC         ON d.drt = e.drt
# MAGIC     CROSS JOIN limite_historico l
# MAGIC ),
# MAGIC
# MAGIC meses_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', data_inicio_historico),
# MAGIC                 DATE_TRUNC('MONTH', data_fim_historico),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC     FROM base_dependentes
# MAGIC     WHERE data_inicio_historico <= data_fim_historico
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_idade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         mes_referencia,
# MAGIC         YEAR(mes_referencia) AS ano,
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(
# MAGIC                 LAST_DAY(mes_referencia),
# MAGIC                 data_nascimento
# MAGIC             ) / 12
# MAGIC         ) AS idade
# MAGIC     FROM meses_dependentes
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_faixa AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         CASE
# MAGIC             WHEN idade <= 18 THEN 0
# MAGIC             WHEN idade BETWEEN 19 AND 23 THEN 19
# MAGIC             WHEN idade BETWEEN 24 AND 28 THEN 24
# MAGIC             WHEN idade BETWEEN 29 AND 33 THEN 29
# MAGIC             WHEN idade BETWEEN 34 AND 38 THEN 34
# MAGIC             WHEN idade BETWEEN 39 AND 43 THEN 39
# MAGIC             WHEN idade BETWEEN 44 AND 48 THEN 44
# MAGIC             WHEN idade BETWEEN 49 AND 53 THEN 49
# MAGIC             WHEN idade BETWEEN 54 AND 58 THEN 54
# MAGIC             ELSE 59
# MAGIC         END AS idade_inicio_faixa
# MAGIC     FROM dependentes_com_idade
# MAGIC ),
# MAGIC
# MAGIC saude_especial AS (
# MAGIC     SELECT
# MAGIC         CAST(mes_ref AS INT) AS idade_inicio_faixa,
# MAGIC         referencia,
# MAGIC         CAST(
# MAGIC             REPLACE(
# MAGIC                 REGEXP_REPLACE(valor_base, '[^0-9,]', ''),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             ) AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC     FROM (
# MAGIC         SELECT *
# MAGIC         FROM workspace.gold.dim_saude
# MAGIC         WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC     )
# MAGIC     UNPIVOT INCLUDE NULLS (
# MAGIC         valor_base FOR referencia IN (
# MAGIC             `out-09`,
# MAGIC             `jul-10`,
# MAGIC             `jul-11`,
# MAGIC             `jul-12`,
# MAGIC             `jul-13`,
# MAGIC             `jul-14`,
# MAGIC             `jul-15`,
# MAGIC             `jul-16`,
# MAGIC             `jul-17`,
# MAGIC             `jul-18`,
# MAGIC             `jul-19`,
# MAGIC             `jul-20`,
# MAGIC             `jul-21`,
# MAGIC             `jul-22`,
# MAGIC             `24-10-22`
# MAGIC         )
# MAGIC     )
# MAGIC ),
# MAGIC
# MAGIC vigencias_saude AS (
# MAGIC     SELECT
# MAGIC         idade_inicio_faixa,
# MAGIC         CASE referencia
# MAGIC             WHEN 'out-09'   THEN DATE '2009-10-01'
# MAGIC             WHEN 'jul-10'   THEN DATE '2010-07-01'
# MAGIC             WHEN 'jul-11'   THEN DATE '2011-07-01'
# MAGIC             WHEN 'jul-12'   THEN DATE '2012-07-01'
# MAGIC             WHEN 'jul-13'   THEN DATE '2013-07-01'
# MAGIC             WHEN 'jul-14'   THEN DATE '2014-07-01'
# MAGIC             WHEN 'jul-15'   THEN DATE '2015-07-01'
# MAGIC             WHEN 'jul-16'   THEN DATE '2016-07-01'
# MAGIC             WHEN 'jul-17'   THEN DATE '2017-07-01'
# MAGIC             WHEN 'jul-18'   THEN DATE '2018-07-01'
# MAGIC             WHEN 'jul-19'   THEN DATE '2019-07-01'
# MAGIC             WHEN 'jul-20'   THEN DATE '2020-07-01'
# MAGIC             WHEN 'jul-21'   THEN DATE '2021-07-01'
# MAGIC             WHEN 'jul-22'   THEN DATE '2022-07-01'
# MAGIC             WHEN '24-10-22' THEN DATE '2022-10-24'
# MAGIC         END AS data_vigencia,
# MAGIC         valor_base
# MAGIC     FROM saude_especial
# MAGIC ),
# MAGIC
# MAGIC custo_mensal AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade,
# MAGIC         MAX_BY(
# MAGIC             s.valor_base,
# MAGIC             s.data_vigencia
# MAGIC         ) AS valor_base
# MAGIC     FROM dependentes_com_faixa d
# MAGIC     LEFT JOIN vigencias_saude s
# MAGIC         ON d.idade_inicio_faixa = s.idade_inicio_faixa
# MAGIC        AND s.data_vigencia <= LAST_DAY(d.mes_referencia)
# MAGIC     GROUP BY
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade
# MAGIC ),
# MAGIC
# MAGIC custo_anual AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC         ROUND(AVG(idade), 2) AS idade_media,
# MAGIC         ROUND(
# MAGIC             AVG(
# MAGIC                 CASE
# MAGIC                     WHEN valor_base IS NOT NULL
# MAGIC                     THEN valor_base * 1.0238
# MAGIC                 END
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS custo_plano_saude
# MAGIC     FROM custo_mensal
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome_dependente,
# MAGIC     parentesco,
# MAGIC     data_nascimento,
# MAGIC     ano,
# MAGIC     idade_media,
# MAGIC     custo_plano_saude
# MAGIC FROM custo_anual
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     nome_dependente,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão do Cálculo histórico do custo do plano de saúde dos dependentes
# MAGIC
# MAGIC O cálculo histórico do custo do plano de saúde dos dependentes foi concluído utilizando a granularidade mensal para determinar a idade, a faixa etária e o valor vigente do plano em cada mês.
# MAGIC
# MAGIC Todos os dependentes foram considerados pertencentes ao plano **ESPECIAL**, conforme a regra de negócio definida para o MVP.
# MAGIC
# MAGIC Sobre o valor-base correspondente à faixa etária e à referência histórica foi aplicado o **IOF de 2,38%**, de forma que:
# MAGIC
# MAGIC **Custo do plano de saúde = Valor-base × 1,0238**
# MAGIC
# MAGIC Após o cálculo mensal, os valores foram consolidados no grão anual definido para a fato.
# MAGIC
# MAGIC O resultado apresentou:
# MAGIC
# MAGIC - **712 registros dependente × DRT × ano**;
# MAGIC - **218 dependentes distintos**;
# MAGIC - **130 DRTs distintos**;
# MAGIC - período histórico entre **2010 e 2026**;
# MAGIC - nenhuma duplicidade no grão dependente × DRT × ano;
# MAGIC - nenhum valor nulo no custo do plano de saúde.
# MAGIC
# MAGIC Os valores obtidos apresentam variação histórica decorrente das diferentes referências de preços e das mudanças de faixa etária dos dependentes.
# MAGIC
# MAGIC A coluna `custo_plano_saude` representa o **custo mensal médio do plano de saúde do dependente no respectivo ano**, incluindo o IOF de 2,38%.
# MAGIC
# MAGIC O cálculo está validado para prosseguimento da construção da `Fato_Dependentes`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação da estrutura final da Fato_Dependentes
# MAGIC
# MAGIC Nesta etapa será realizada a validação da estrutura calculada para a `Fato_Dependentes` antes de sua persistência na camada Gold.
# MAGIC
# MAGIC A validação verificará:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - quantidade de dependentes distintos;
# MAGIC - unicidade do grão dependente × DRT × ano;
# MAGIC - período histórico;
# MAGIC - presença de valores nulos nos atributos da fato;
# MAGIC - presença de custos de plano de saúde nulos ou não positivos.
# MAGIC
# MAGIC São esperados **712 registros**, correspondentes a **218 dependentes** associados a **130 DRTs**, sem duplicidades no grão definido.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_historico AS (
# MAGIC     SELECT MAX(data) AS ultima_data
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC base_dependentes AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         GREATEST(e.data_admissao, d.data_nascimento) AS data_inicio_historico,
# MAGIC         LEAST(
# MAGIC             COALESCE(e.data_desligamento, l.ultima_data),
# MAGIC             l.ultima_data
# MAGIC         ) AS data_fim_historico
# MAGIC     FROM workspace.silver.dependentes_anonimizados d
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados e
# MAGIC         ON d.drt = e.drt
# MAGIC     CROSS JOIN limite_historico l
# MAGIC ),
# MAGIC
# MAGIC meses_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', data_inicio_historico),
# MAGIC                 DATE_TRUNC('MONTH', data_fim_historico),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC     FROM base_dependentes
# MAGIC     WHERE data_inicio_historico <= data_fim_historico
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_idade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         mes_referencia,
# MAGIC         YEAR(mes_referencia) AS ano,
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(
# MAGIC                 LAST_DAY(mes_referencia),
# MAGIC                 data_nascimento
# MAGIC             ) / 12
# MAGIC         ) AS idade
# MAGIC     FROM meses_dependentes
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_faixa AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         CASE
# MAGIC             WHEN idade <= 18 THEN 0
# MAGIC             WHEN idade BETWEEN 19 AND 23 THEN 19
# MAGIC             WHEN idade BETWEEN 24 AND 28 THEN 24
# MAGIC             WHEN idade BETWEEN 29 AND 33 THEN 29
# MAGIC             WHEN idade BETWEEN 34 AND 38 THEN 34
# MAGIC             WHEN idade BETWEEN 39 AND 43 THEN 39
# MAGIC             WHEN idade BETWEEN 44 AND 48 THEN 44
# MAGIC             WHEN idade BETWEEN 49 AND 53 THEN 49
# MAGIC             WHEN idade BETWEEN 54 AND 58 THEN 54
# MAGIC             ELSE 59
# MAGIC         END AS idade_inicio_faixa
# MAGIC     FROM dependentes_com_idade
# MAGIC ),
# MAGIC
# MAGIC saude_especial AS (
# MAGIC     SELECT
# MAGIC         CAST(mes_ref AS INT) AS idade_inicio_faixa,
# MAGIC         referencia,
# MAGIC         CAST(
# MAGIC             REPLACE(
# MAGIC                 REGEXP_REPLACE(valor_base, '[^0-9,]', ''),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             ) AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC     FROM (
# MAGIC         SELECT *
# MAGIC         FROM workspace.gold.dim_saude
# MAGIC         WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC     )
# MAGIC     UNPIVOT INCLUDE NULLS (
# MAGIC         valor_base FOR referencia IN (
# MAGIC             `out-09`,
# MAGIC             `jul-10`,
# MAGIC             `jul-11`,
# MAGIC             `jul-12`,
# MAGIC             `jul-13`,
# MAGIC             `jul-14`,
# MAGIC             `jul-15`,
# MAGIC             `jul-16`,
# MAGIC             `jul-17`,
# MAGIC             `jul-18`,
# MAGIC             `jul-19`,
# MAGIC             `jul-20`,
# MAGIC             `jul-21`,
# MAGIC             `jul-22`,
# MAGIC             `24-10-22`
# MAGIC         )
# MAGIC     )
# MAGIC ),
# MAGIC
# MAGIC vigencias_saude AS (
# MAGIC     SELECT
# MAGIC         idade_inicio_faixa,
# MAGIC         CASE referencia
# MAGIC             WHEN 'out-09'   THEN DATE '2009-10-01'
# MAGIC             WHEN 'jul-10'   THEN DATE '2010-07-01'
# MAGIC             WHEN 'jul-11'   THEN DATE '2011-07-01'
# MAGIC             WHEN 'jul-12'   THEN DATE '2012-07-01'
# MAGIC             WHEN 'jul-13'   THEN DATE '2013-07-01'
# MAGIC             WHEN 'jul-14'   THEN DATE '2014-07-01'
# MAGIC             WHEN 'jul-15'   THEN DATE '2015-07-01'
# MAGIC             WHEN 'jul-16'   THEN DATE '2016-07-01'
# MAGIC             WHEN 'jul-17'   THEN DATE '2017-07-01'
# MAGIC             WHEN 'jul-18'   THEN DATE '2018-07-01'
# MAGIC             WHEN 'jul-19'   THEN DATE '2019-07-01'
# MAGIC             WHEN 'jul-20'   THEN DATE '2020-07-01'
# MAGIC             WHEN 'jul-21'   THEN DATE '2021-07-01'
# MAGIC             WHEN 'jul-22'   THEN DATE '2022-07-01'
# MAGIC             WHEN '24-10-22' THEN DATE '2022-10-24'
# MAGIC         END AS data_vigencia,
# MAGIC         valor_base
# MAGIC     FROM saude_especial
# MAGIC ),
# MAGIC
# MAGIC custo_mensal AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade,
# MAGIC         MAX_BY(s.valor_base, s.data_vigencia) AS valor_base
# MAGIC     FROM dependentes_com_faixa d
# MAGIC     LEFT JOIN vigencias_saude s
# MAGIC         ON d.idade_inicio_faixa = s.idade_inicio_faixa
# MAGIC        AND s.data_vigencia <= LAST_DAY(d.mes_referencia)
# MAGIC     GROUP BY
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade
# MAGIC ),
# MAGIC
# MAGIC fato_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC         ROUND(AVG(idade), 2) AS idade_media,
# MAGIC         ROUND(
# MAGIC             AVG(
# MAGIC                 CASE
# MAGIC                     WHEN valor_base IS NOT NULL
# MAGIC                     THEN valor_base * 1.0238
# MAGIC                 END
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS custo_plano_saude
# MAGIC     FROM custo_mensal
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC     COUNT(DISTINCT CONCAT(CAST(drt AS STRING), '|', nome_dependente)) AS total_dependentes,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(DISTINCT CONCAT(
# MAGIC         CAST(drt AS STRING), '|',
# MAGIC         nome_dependente, '|',
# MAGIC         CAST(ano AS STRING)
# MAGIC     )) AS duplicidades,
# MAGIC
# MAGIC     MIN(ano) AS primeiro_ano,
# MAGIC     MAX(ano) AS ultimo_ano,
# MAGIC
# MAGIC     SUM(CASE WHEN nome_dependente IS NULL THEN 1 ELSE 0 END) AS nome_null,
# MAGIC     SUM(CASE WHEN parentesco IS NULL THEN 1 ELSE 0 END) AS parentesco_null,
# MAGIC     SUM(CASE WHEN data_nascimento IS NULL THEN 1 ELSE 0 END) AS data_nascimento_null,
# MAGIC     SUM(CASE WHEN idade_media IS NULL THEN 1 ELSE 0 END) AS idade_null,
# MAGIC     SUM(CASE WHEN custo_plano_saude IS NULL THEN 1 ELSE 0 END) AS custo_null,
# MAGIC     SUM(CASE WHEN custo_plano_saude <= 0 THEN 1 ELSE 0 END) AS custo_nao_positivo
# MAGIC
# MAGIC FROM fato_dependentes;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação da estrutura final da Fato_Dependentes
# MAGIC
# MAGIC A estrutura calculada para a `Fato_Dependentes` foi validada antes de sua persistência na camada Gold.
# MAGIC
# MAGIC A validação apresentou:
# MAGIC
# MAGIC - **712 registros**;
# MAGIC - **218 dependentes distintos**;
# MAGIC - **130 DRTs distintos**;
# MAGIC - período histórico entre **2010 e 2026**;
# MAGIC - **0 duplicidades** no grão dependente × DRT × ano;
# MAGIC - nenhum nome de dependente nulo;
# MAGIC - nenhum parentesco nulo;
# MAGIC - nenhuma data de nascimento nula;
# MAGIC - nenhuma idade média nula;
# MAGIC - nenhum custo de plano de saúde nulo;
# MAGIC - nenhum custo de plano de saúde igual ou inferior a zero.
# MAGIC
# MAGIC Os resultados confirmam a consistência da estrutura histórica e dos atributos que comporão a `Fato_Dependentes`.
# MAGIC
# MAGIC A estrutura está validada para persistência na camada Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Persistência da Fato_Dependentes
# MAGIC
# MAGIC Nesta etapa será persistida na camada Gold a estrutura final da `Fato_Dependentes`.
# MAGIC
# MAGIC O grão da fato é:
# MAGIC
# MAGIC **uma linha por dependente × DRT × ano.**
# MAGIC
# MAGIC A estrutura final será composta por:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `nome_dependente`;
# MAGIC - `parentesco`;
# MAGIC - `data_nascimento`;
# MAGIC - `ano`;
# MAGIC - `idade_media`;
# MAGIC - `custo_plano_saude`.
# MAGIC
# MAGIC A coluna `idade_media` representa a idade média do dependente nos meses considerados no respectivo ano.
# MAGIC
# MAGIC A coluna `custo_plano_saude` representa o custo mensal médio do plano de saúde do dependente no respectivo ano, considerando:
# MAGIC
# MAGIC - plano ESPECIAL;
# MAGIC - idade do dependente em cada mês;
# MAGIC - respectiva faixa etária;
# MAGIC - valor-base vigente;
# MAGIC - IOF de 2,38%.
# MAGIC
# MAGIC O período histórico de cada dependente é delimitado pelo vínculo empregatício do titular e pela data de nascimento do dependente, conforme as premissas definidas para o MVP.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.fato_dependentes
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH limite_historico AS (
# MAGIC     SELECT MAX(data) AS ultima_data
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC base_dependentes AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome AS nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         GREATEST(e.data_admissao, d.data_nascimento) AS data_inicio_historico,
# MAGIC         LEAST(
# MAGIC             COALESCE(e.data_desligamento, l.ultima_data),
# MAGIC             l.ultima_data
# MAGIC         ) AS data_fim_historico
# MAGIC     FROM workspace.silver.dependentes_anonimizados d
# MAGIC     INNER JOIN workspace.silver.empregados_anonimizados e
# MAGIC         ON d.drt = e.drt
# MAGIC     CROSS JOIN limite_historico l
# MAGIC ),
# MAGIC
# MAGIC meses_dependentes AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', data_inicio_historico),
# MAGIC                 DATE_TRUNC('MONTH', data_fim_historico),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC     FROM base_dependentes
# MAGIC     WHERE data_inicio_historico <= data_fim_historico
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_idade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome_dependente,
# MAGIC         parentesco,
# MAGIC         data_nascimento,
# MAGIC         mes_referencia,
# MAGIC         YEAR(mes_referencia) AS ano,
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(
# MAGIC                 LAST_DAY(mes_referencia),
# MAGIC                 data_nascimento
# MAGIC             ) / 12
# MAGIC         ) AS idade
# MAGIC     FROM meses_dependentes
# MAGIC ),
# MAGIC
# MAGIC dependentes_com_faixa AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         CASE
# MAGIC             WHEN idade <= 18 THEN 0
# MAGIC             WHEN idade BETWEEN 19 AND 23 THEN 19
# MAGIC             WHEN idade BETWEEN 24 AND 28 THEN 24
# MAGIC             WHEN idade BETWEEN 29 AND 33 THEN 29
# MAGIC             WHEN idade BETWEEN 34 AND 38 THEN 34
# MAGIC             WHEN idade BETWEEN 39 AND 43 THEN 39
# MAGIC             WHEN idade BETWEEN 44 AND 48 THEN 44
# MAGIC             WHEN idade BETWEEN 49 AND 53 THEN 49
# MAGIC             WHEN idade BETWEEN 54 AND 58 THEN 54
# MAGIC             ELSE 59
# MAGIC         END AS idade_inicio_faixa
# MAGIC     FROM dependentes_com_idade
# MAGIC ),
# MAGIC
# MAGIC saude_especial AS (
# MAGIC     SELECT
# MAGIC         CAST(mes_ref AS INT) AS idade_inicio_faixa,
# MAGIC         referencia,
# MAGIC         CAST(
# MAGIC             REPLACE(
# MAGIC                 REGEXP_REPLACE(valor_base, '[^0-9,]', ''),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             ) AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC     FROM (
# MAGIC         SELECT *
# MAGIC         FROM workspace.gold.dim_saude
# MAGIC         WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC     )
# MAGIC     UNPIVOT INCLUDE NULLS (
# MAGIC         valor_base FOR referencia IN (
# MAGIC             `out-09`,
# MAGIC             `jul-10`,
# MAGIC             `jul-11`,
# MAGIC             `jul-12`,
# MAGIC             `jul-13`,
# MAGIC             `jul-14`,
# MAGIC             `jul-15`,
# MAGIC             `jul-16`,
# MAGIC             `jul-17`,
# MAGIC             `jul-18`,
# MAGIC             `jul-19`,
# MAGIC             `jul-20`,
# MAGIC             `jul-21`,
# MAGIC             `jul-22`,
# MAGIC             `24-10-22`
# MAGIC         )
# MAGIC     )
# MAGIC ),
# MAGIC
# MAGIC vigencias_saude AS (
# MAGIC     SELECT
# MAGIC         idade_inicio_faixa,
# MAGIC         CASE referencia
# MAGIC             WHEN 'out-09'   THEN DATE '2009-10-01'
# MAGIC             WHEN 'jul-10'   THEN DATE '2010-07-01'
# MAGIC             WHEN 'jul-11'   THEN DATE '2011-07-01'
# MAGIC             WHEN 'jul-12'   THEN DATE '2012-07-01'
# MAGIC             WHEN 'jul-13'   THEN DATE '2013-07-01'
# MAGIC             WHEN 'jul-14'   THEN DATE '2014-07-01'
# MAGIC             WHEN 'jul-15'   THEN DATE '2015-07-01'
# MAGIC             WHEN 'jul-16'   THEN DATE '2016-07-01'
# MAGIC             WHEN 'jul-17'   THEN DATE '2017-07-01'
# MAGIC             WHEN 'jul-18'   THEN DATE '2018-07-01'
# MAGIC             WHEN 'jul-19'   THEN DATE '2019-07-01'
# MAGIC             WHEN 'jul-20'   THEN DATE '2020-07-01'
# MAGIC             WHEN 'jul-21'   THEN DATE '2021-07-01'
# MAGIC             WHEN 'jul-22'   THEN DATE '2022-07-01'
# MAGIC             WHEN '24-10-22' THEN DATE '2022-10-24'
# MAGIC         END AS data_vigencia,
# MAGIC         valor_base
# MAGIC     FROM saude_especial
# MAGIC ),
# MAGIC
# MAGIC custo_mensal AS (
# MAGIC     SELECT
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade,
# MAGIC         MAX_BY(
# MAGIC             s.valor_base,
# MAGIC             s.data_vigencia
# MAGIC         ) AS valor_base
# MAGIC     FROM dependentes_com_faixa d
# MAGIC     LEFT JOIN vigencias_saude s
# MAGIC         ON d.idade_inicio_faixa = s.idade_inicio_faixa
# MAGIC        AND s.data_vigencia <= LAST_DAY(d.mes_referencia)
# MAGIC     GROUP BY
# MAGIC         d.drt,
# MAGIC         d.nome_dependente,
# MAGIC         d.parentesco,
# MAGIC         d.data_nascimento,
# MAGIC         d.ano,
# MAGIC         d.mes_referencia,
# MAGIC         d.idade
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome_dependente,
# MAGIC     parentesco,
# MAGIC     data_nascimento,
# MAGIC     ano,
# MAGIC     ROUND(AVG(idade), 2) AS idade_media,
# MAGIC     ROUND(
# MAGIC         AVG(
# MAGIC             CASE
# MAGIC                 WHEN valor_base IS NOT NULL
# MAGIC                 THEN valor_base * 1.0238
# MAGIC             END
# MAGIC         ),
# MAGIC         2
# MAGIC     ) AS custo_plano_saude
# MAGIC FROM custo_mensal
# MAGIC GROUP BY
# MAGIC     drt,
# MAGIC     nome_dependente,
# MAGIC     parentesco,
# MAGIC     data_nascimento,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Conclusão da Persistência da Fato_Dependentes
# MAGIC
# MAGIC A `Fato_Dependentes` foi persistida na camada Gold como `workspace.gold.fato_dependentes`.
# MAGIC
# MAGIC A tabela mantém o grão definido de **uma linha por dependente × DRT × ano** e armazena o histórico anual dos dependentes associado ao vínculo empregatício do titular.
# MAGIC
# MAGIC O custo do plano de saúde foi calculado a partir dos valores históricos do plano ESPECIAL, considerando a faixa etária aplicável em cada mês e a incidência de IOF de 2,38%.
# MAGIC
# MAGIC Após a persistência, será realizada uma validação final diretamente sobre a tabela Gold para confirmar que a estrutura gravada mantém os resultados anteriormente validados.

# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Validação da Fato_Dependentes persistida
# MAGIC
# MAGIC Após a persistência da `Fato_Dependentes` na camada Gold, será realizada a validação final da tabela.
# MAGIC
# MAGIC A validação verificará:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - quantidade de dependentes distintos;
# MAGIC - unicidade do grão dependente × DRT × ano;
# MAGIC - período histórico armazenado;
# MAGIC - presença de valores nulos nos atributos;
# MAGIC - presença de custos de plano de saúde nulos ou não positivos.
# MAGIC
# MAGIC São esperados **712 registros**, correspondentes a **218 dependentes** associados a **130 DRTs**, sem duplicidades no grão definido.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC     COUNT(DISTINCT CONCAT(CAST(drt AS STRING), '|', nome_dependente)) AS total_dependentes,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(DISTINCT CONCAT(
# MAGIC         CAST(drt AS STRING), '|',
# MAGIC         nome_dependente, '|',
# MAGIC         CAST(ano AS STRING)
# MAGIC     )) AS duplicidades,
# MAGIC
# MAGIC     MIN(ano) AS primeiro_ano,
# MAGIC     MAX(ano) AS ultimo_ano,
# MAGIC
# MAGIC     SUM(CASE WHEN drt IS NULL THEN 1 ELSE 0 END) AS drt_null,
# MAGIC     SUM(CASE WHEN nome_dependente IS NULL THEN 1 ELSE 0 END) AS nome_null,
# MAGIC     SUM(CASE WHEN parentesco IS NULL THEN 1 ELSE 0 END) AS parentesco_null,
# MAGIC     SUM(CASE WHEN data_nascimento IS NULL THEN 1 ELSE 0 END) AS data_nascimento_null,
# MAGIC     SUM(CASE WHEN ano IS NULL THEN 1 ELSE 0 END) AS ano_null,
# MAGIC     SUM(CASE WHEN idade_media IS NULL THEN 1 ELSE 0 END) AS idade_null,
# MAGIC     SUM(CASE WHEN custo_plano_saude IS NULL THEN 1 ELSE 0 END) AS custo_null,
# MAGIC     SUM(CASE WHEN custo_plano_saude <= 0 THEN 1 ELSE 0 END) AS custo_nao_positivo
# MAGIC
# MAGIC FROM workspace.gold.fato_dependentes;

# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Conclusão da Validação da Fato_Dependentes persistida
# MAGIC
# MAGIC A `Fato_Dependentes` foi persistida e validada na camada Gold como `workspace.gold.fato_dependentes`.
# MAGIC
# MAGIC A validação final apresentou:
# MAGIC
# MAGIC - **712 registros**;
# MAGIC - **218 dependentes distintos**;
# MAGIC - **130 DRTs distintos**;
# MAGIC - período histórico entre **2010 e 2026**;
# MAGIC - **0 duplicidades** no grão dependente × DRT × ano;
# MAGIC - nenhum DRT nulo;
# MAGIC - nenhum nome de dependente nulo;
# MAGIC - nenhum parentesco nulo;
# MAGIC - nenhuma data de nascimento nula;
# MAGIC - nenhum ano nulo;
# MAGIC - nenhuma idade média nula;
# MAGIC - nenhum custo de plano de saúde nulo;
# MAGIC - nenhum custo de plano de saúde igual ou inferior a zero.
# MAGIC
# MAGIC Cada registro representa um dependente associado a determinado vínculo empregatício em determinado ano.
# MAGIC
# MAGIC A coluna `idade_media` representa a idade média do dependente nos meses considerados naquele ano.
# MAGIC
# MAGIC A coluna `custo_plano_saude` representa o custo mensal médio do plano de saúde do dependente no respectivo ano, calculado a partir do plano ESPECIAL, da faixa etária aplicável, dos valores históricos vigentes e do IOF de 2,38%.
# MAGIC
# MAGIC Com a persistência e a validação concluídas, a `Fato_Dependentes` está finalizada na camada Gold.