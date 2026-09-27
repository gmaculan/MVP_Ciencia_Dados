# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição e grão da Fato_Ferias
# MAGIC
# MAGIC A `Fato_Ferias` tem como objetivo preservar, na camada Gold, o histórico de férias associado aos vínculos empregatícios da empresa.
# MAGIC
# MAGIC A manutenção desse histórico é relevante para o RH, pois permite consultar os diferentes ciclos de férias de cada vínculo e acompanhar as informações registradas desde a aquisição do direito até os respectivos períodos de gozo.
# MAGIC
# MAGIC Cada período aquisitivo representa, conceitualmente, a aquisição de um novo direito a férias.
# MAGIC
# MAGIC Como as férias podem ser usufruídas em mais de um período, os diferentes períodos de gozo serão representados em linhas distintas na `Fato_Ferias`.
# MAGIC
# MAGIC O grão definido para a fato é:
# MAGIC
# MAGIC **uma linha por período de gozo associado a um registro histórico de férias de determinado DRT.**
# MAGIC
# MAGIC Dessa forma, quando um registro possuir:
# MAGIC
# MAGIC - um período de gozo, será gerada uma linha;
# MAGIC - dois períodos de gozo, serão geradas duas linhas;
# MAGIC - três períodos de gozo, serão geradas três linhas.
# MAGIC
# MAGIC Os registros históricos que ainda não possuam período de gozo informado também serão preservados, garantindo que nenhum registro existente na camada Silver seja eliminado durante a transformação.
# MAGIC
# MAGIC Para organizar cronologicamente o histórico, será criado o campo `numero_direito_ferias`, que identifica sequencialmente os períodos aquisitivos de cada DRT.
# MAGIC
# MAGIC Também será utilizado o campo `numero_periodo_gozo`, que identifica o período de gozo dentro daquele direito de férias.
# MAGIC
# MAGIC A partir dessas informações será criado `sequencial_ferias`, um identificador textual destinado a facilitar a leitura do histórico.
# MAGIC
# MAGIC Quando houver apenas um período de gozo para determinado direito, o identificador será representado apenas pelo número do direito:
# MAGIC
# MAGIC `1`, `2`, `3`, `4`, `5`...
# MAGIC
# MAGIC Quando o mesmo direito possuir mais de um período de gozo, o identificador utilizará a forma:
# MAGIC
# MAGIC `4.1`, `4.2`
# MAGIC
# MAGIC ou, no caso de três períodos:
# MAGIC
# MAGIC `4.1`, `4.2`, `4.3`.
# MAGIC
# MAGIC A parte anterior ao ponto identifica o direito de férias e a parte posterior identifica cada período de gozo daquele mesmo direito.
# MAGIC
# MAGIC O campo `sequencial_ferias` será textual e terá finalidade exclusivamente identificadora, não sendo utilizado como medida numérica.
# MAGIC
# MAGIC Além dessas informações, serão preservados:
# MAGIC
# MAGIC - DRT do vínculo empregatício;
# MAGIC - início do período aquisitivo;
# MAGIC - término do período aquisitivo;
# MAGIC - data-limite para aviso;
# MAGIC - data-limite para início das férias;
# MAGIC - data do aviso;
# MAGIC - indicação de abono;
# MAGIC - data de início do período de gozo;
# MAGIC - data de término do período de gozo.
# MAGIC
# MAGIC A sequência existente na fonte não será transportada para a `Fato_Ferias`. A ordenação do histórico na camada Gold será construída a partir dos períodos aquisitivos e dos respectivos períodos de gozo.
# MAGIC
# MAGIC Eventuais registros repetidos ou inconsistentes existentes na Silver serão preservados. A camada Gold não realizará correções inferenciais destinadas a determinar qual teria sido o lançamento pretendido pelo RH.
# MAGIC
# MAGIC As informações cadastrais do empregado, como nome e CPF, não serão replicadas na fato, pois podem ser obtidas por meio da `Dim_Empregado`.
# MAGIC
# MAGIC Não serão criadas, neste MVP, inferências sobre quem definiu o período de férias nem mecanismos de acompanhamento preventivo de sua programação. Como evolução futura, poderão ser implementados controles de integridade na entrada dos dados e mecanismos de acompanhamento utilizando informações como a data de aviso e a data-limite para início das férias.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Construção da Fato_Ferias
# MAGIC
# MAGIC Nesta etapa, os registros históricos disponíveis em `workspace.silver.ferias_anonimizado` serão reorganizados para formar a estrutura analítica da `Fato_Ferias`.
# MAGIC
# MAGIC Na Silver, cada registro pode armazenar até três períodos de gozo em conjuntos distintos de colunas. Na Gold, esses períodos serão transformados em linhas, de modo que cada linha represente um período de gozo associado ao respectivo direito de férias.
# MAGIC
# MAGIC Os registros referentes a estagiários, identificados no projeto por DRT com mais de três caracteres, não fazem parte do escopo analítico da fato e serão excluídos antes das demais transformações.
# MAGIC
# MAGIC ## Tratamento de duplicidades da origem
# MAGIC
# MAGIC A fonte histórica de férias foi mantida manualmente em planilha. Durante a análise dos dados, foram identificados casos em que o mesmo DRT apresenta mais de um registro com exatamente o mesmo período aquisitivo.
# MAGIC
# MAGIC A inspeção dessas ocorrências confirmou que os registros repetidos possuem valores consecutivos no campo `sequencia`, sendo a ocorrência de maior sequência o lançamento posterior.
# MAGIC
# MAGIC Considerando que cada período aquisitivo corresponde a um único direito de férias e o processo de origem era baseado na replicação manual de registros anteriores, será aplicada a seguinte regra de qualidade:
# MAGIC
# MAGIC **quando existirem registros com o mesmo DRT, início do período aquisitivo e término do período aquisitivo, será mantida a ocorrência de menor `sequencia`.**
# MAGIC
# MAGIC A `sequencia` da fonte será utilizada exclusivamente para esse tratamento de qualidade e não será transportada para a `Fato_Ferias`.
# MAGIC
# MAGIC As demais informações históricas não serão corrigidas por inferência.
# MAGIC
# MAGIC ## Organização dos direitos e períodos de gozo
# MAGIC
# MAGIC Após o tratamento das duplicidades, os períodos aquisitivos de cada DRT serão ordenados cronologicamente e receberão o campo `numero_direito_ferias`.
# MAGIC
# MAGIC Os diferentes períodos de gozo existentes na Silver serão então transformados em linhas.
# MAGIC
# MAGIC Quando determinado direito possuir somente um período de gozo, o campo textual `sequencial_ferias` será representado apenas pelo número do direito:
# MAGIC
# MAGIC `1`, `2`, `3`, `4`...
# MAGIC
# MAGIC Quando houver mais de um período de gozo associado ao mesmo direito, os períodos serão numerados cronologicamente e identificados como:
# MAGIC
# MAGIC `4.1`, `4.2`
# MAGIC
# MAGIC ou, quando aplicável:
# MAGIC
# MAGIC `4.1`, `4.2`, `4.3`.
# MAGIC
# MAGIC O campo `numero_periodo_gozo` armazenará separadamente a ordem do período de gozo dentro daquele direito.
# MAGIC
# MAGIC Registros históricos que não possuam período de gozo informado também serão preservados. Nesses casos, o direito continuará identificado por `numero_direito_ferias` e `sequencial_ferias`, enquanto `numero_periodo_gozo`, `data_inicio_gozo` e `data_termino_gozo` permanecerão nulos.
# MAGIC
# MAGIC Dessa forma, a transformação preserva o histórico necessário para análise, trata a duplicidade comprovadamente decorrente do processo manual de origem e reorganiza os períodos de gozo em uma estrutura adequada ao consumo analítico da camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH ferias_origem AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         sequencia,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1,
# MAGIC         data_termino_1,
# MAGIC         data_inicio_2,
# MAGIC         data_termino_2,
# MAGIC         data_inicio_3,
# MAGIC         data_termino_3,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 data_inicio_periodo_aquisitivo,
# MAGIC                 data_termino_periodo_aquisitivo
# MAGIC             ORDER BY sequencia
# MAGIC         ) AS ordem_duplicidade
# MAGIC
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC ferias_sem_duplicidade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1,
# MAGIC         data_termino_1,
# MAGIC         data_inicio_2,
# MAGIC         data_termino_2,
# MAGIC         data_inicio_3,
# MAGIC         data_termino_3
# MAGIC
# MAGIC     FROM ferias_origem
# MAGIC
# MAGIC     WHERE ordem_duplicidade = 1
# MAGIC ),
# MAGIC
# MAGIC ferias_base AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         DENSE_RANK() OVER (
# MAGIC             PARTITION BY drt
# MAGIC             ORDER BY
# MAGIC                 data_inicio_periodo_aquisitivo,
# MAGIC                 data_termino_periodo_aquisitivo
# MAGIC         ) AS numero_direito_ferias
# MAGIC
# MAGIC     FROM ferias_sem_duplicidade
# MAGIC ),
# MAGIC
# MAGIC periodos_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1 AS data_inicio_gozo,
# MAGIC         data_termino_1 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_1 IS NOT NULL
# MAGIC        OR data_termino_1 IS NOT NULL
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_2 AS data_inicio_gozo,
# MAGIC         data_termino_2 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_2 IS NOT NULL
# MAGIC        OR data_termino_2 IS NOT NULL
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_3 AS data_inicio_gozo,
# MAGIC         data_termino_3 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_3 IS NOT NULL
# MAGIC        OR data_termino_3 IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC gozos_numerados AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 numero_direito_ferias
# MAGIC             ORDER BY
# MAGIC                 data_inicio_gozo,
# MAGIC                 data_termino_gozo
# MAGIC         ) AS numero_periodo_gozo,
# MAGIC
# MAGIC         COUNT(*) OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 numero_direito_ferias
# MAGIC         ) AS quantidade_periodos_gozo
# MAGIC
# MAGIC     FROM periodos_gozo
# MAGIC ),
# MAGIC
# MAGIC com_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN quantidade_periodos_gozo > 1
# MAGIC             THEN CONCAT(
# MAGIC                 CAST(numero_direito_ferias AS STRING),
# MAGIC                 '.',
# MAGIC                 CAST(numero_periodo_gozo AS STRING)
# MAGIC             )
# MAGIC             ELSE CAST(numero_direito_ferias AS STRING)
# MAGIC         END AS sequencial_ferias,
# MAGIC
# MAGIC         numero_periodo_gozo,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_gozo,
# MAGIC         data_termino_gozo
# MAGIC
# MAGIC     FROM gozos_numerados
# MAGIC ),
# MAGIC
# MAGIC sem_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         CAST(numero_direito_ferias AS STRING) AS sequencial_ferias,
# MAGIC         CAST(NULL AS INT) AS numero_periodo_gozo,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         CAST(NULL AS DATE) AS data_inicio_gozo,
# MAGIC         CAST(NULL AS DATE) AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_1 IS NULL
# MAGIC       AND data_termino_1 IS NULL
# MAGIC       AND data_inicio_2 IS NULL
# MAGIC       AND data_termino_2 IS NULL
# MAGIC       AND data_inicio_3 IS NULL
# MAGIC       AND data_termino_3 IS NULL
# MAGIC ),
# MAGIC
# MAGIC fato_ferias AS (
# MAGIC     SELECT * FROM com_gozo
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM sem_gozo
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     numero_direito_ferias,
# MAGIC     sequencial_ferias,
# MAGIC     numero_periodo_gozo,
# MAGIC     data_inicio_periodo_aquisitivo,
# MAGIC     data_termino_periodo_aquisitivo,
# MAGIC     data_limite_aviso,
# MAGIC     data_limite_inicio,
# MAGIC     data_aviso,
# MAGIC     abono,
# MAGIC     data_inicio_gozo,
# MAGIC     data_termino_gozo
# MAGIC
# MAGIC FROM fato_ferias
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     numero_direito_ferias,
# MAGIC     numero_periodo_gozo,
# MAGIC     data_inicio_gozo;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Construção da Fato_Ferias
# MAGIC
# MAGIC A transformação realizada reorganizou o histórico de férias da camada Silver para o grão definido para a `Fato_Ferias`, representando os diferentes períodos de gozo em linhas.
# MAGIC
# MAGIC Os registros referentes a estagiários, identificados no projeto por DRT com mais de três caracteres, foram excluídos do escopo da fato.
# MAGIC
# MAGIC Também foi aplicado o tratamento das duplicidades identificadas na origem. Nos casos em que o mesmo DRT apresentava mais de um registro para exatamente o mesmo período aquisitivo, foi preservada a ocorrência de menor `sequencia`, correspondente ao primeiro lançamento, e descartada a ocorrência posterior decorrente do processo manual de manutenção da planilha.
# MAGIC
# MAGIC A `sequencia` original foi utilizada exclusivamente para esse tratamento de qualidade e não foi transportada para a estrutura analítica da Gold.
# MAGIC
# MAGIC Após os tratamentos e a transformação dos períodos de gozo, foram obtidos:
# MAGIC
# MAGIC - **995 registros** na estrutura da fato;
# MAGIC - **340 DRTs distintos**;
# MAGIC - **873 direitos de férias**;
# MAGIC - **679 períodos de gozo registrados**;
# MAGIC - **316 direitos sem período de gozo registrado**;
# MAGIC - **557 primeiros períodos de gozo**;
# MAGIC - **114 segundos períodos de gozo**;
# MAGIC - **8 terceiros períodos de gozo**;
# MAGIC - **nenhum DRT com mais de três caracteres**;
# MAGIC - **nenhuma duplicidade de DRT + sequencial_ferias**.
# MAGIC
# MAGIC Os registros sem período de gozo permaneceram preservados, mantendo as informações referentes ao respectivo direito de férias e deixando nulos apenas os campos específicos do gozo.
# MAGIC
# MAGIC O novo `sequencial_ferias` passou a identificar o histórico de forma consistente. Direitos usufruídos em um único período são representados por identificadores como `1`, `2` e `3`, enquanto direitos fracionados são representados por identificadores como `3.1` e `3.2`.
# MAGIC
# MAGIC A transformação mantém, portanto, o histórico necessário às análises de RH, elimina apenas as duplicidades cuja origem foi identificada no processo manual de manutenção dos dados e não realiza correções inferenciais sobre as demais informações históricas.
# MAGIC
# MAGIC A limitação decorrente do controle manual de férias e a recomendação de adoção futura de mecanismos de integridade e validação na entrada dos dados deverão ser registradas no README do projeto.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Persistência da Fato_Ferias
# MAGIC
# MAGIC Após a validação da estrutura e das regras de transformação, a `Fato_Ferias` será persistida na camada Gold como tabela Delta.
# MAGIC
# MAGIC A construção utilizará as regras validadas nas etapas anteriores:
# MAGIC
# MAGIC - exclusão dos estagiários, identificados por DRT com mais de três caracteres;
# MAGIC - tratamento das duplicidades de DRT e período aquisitivo, mantendo a ocorrência de menor `sequencia`;
# MAGIC - criação de `numero_direito_ferias` a partir da ordem cronológica dos períodos aquisitivos de cada DRT;
# MAGIC - transformação dos diferentes períodos de gozo da origem em linhas;
# MAGIC - criação de `numero_periodo_gozo`;
# MAGIC - criação do identificador textual `sequencial_ferias`;
# MAGIC - preservação dos direitos que ainda não possuem período de gozo registrado.
# MAGIC
# MAGIC A `sequencia` existente na origem será utilizada somente durante o tratamento das duplicidades e não fará parte da estrutura persistida.
# MAGIC
# MAGIC ## Correção pontual de qualidade — DRT 325
# MAGIC
# MAGIC Durante a validação da estrutura foi identificado um período aquisitivo inconsistente para o DRT 325:
# MAGIC
# MAGIC - início do período aquisitivo: `17/06/2014`;
# MAGIC - término registrado na origem: `16/06/2014`.
# MAGIC
# MAGIC Essa combinação é temporalmente inválida, pois a data de término ocorre antes da data de início.
# MAGIC
# MAGIC A conferência do registro na fonte e do período aquisitivo imediatamente anterior confirmou a sequência histórica:
# MAGIC
# MAGIC - período anterior: `17/06/2013` a `16/06/2014`;
# MAGIC - período seguinte registrado com erro: `17/06/2014` a `16/06/2014`.
# MAGIC
# MAGIC O registro seguinte encontra-se ainda identificado na fonte como referente a férias indenizadas na rescisão.
# MAGIC
# MAGIC Diante da continuidade anual observada no histórico do próprio vínculo, foi identificado um erro de input no ano da data de término do segundo período.
# MAGIC
# MAGIC Para a construção da Gold, será aplicada uma correção pontual:
# MAGIC
# MAGIC **DRT 325 — término do período aquisitivo alterado de `16/06/2014` para `16/06/2015`.**
# MAGIC
# MAGIC A correção será realizada exclusivamente durante a construção da `Fato_Ferias`. As camadas anteriores permanecerão inalteradas, preservando o dado recebido da origem e a rastreabilidade do tratamento realizado na Gold.
# MAGIC
# MAGIC A tabela resultante será persistida como `workspace.gold.fato_ferias`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.fato_ferias
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH ferias_corrigidas AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         sequencia,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN drt = 325
# MAGIC              AND data_inicio_periodo_aquisitivo = DATE '2014-06-17'
# MAGIC              AND data_termino_periodo_aquisitivo = DATE '2014-06-16'
# MAGIC             THEN DATE '2015-06-16'
# MAGIC             ELSE data_termino_periodo_aquisitivo
# MAGIC         END AS data_termino_periodo_aquisitivo,
# MAGIC
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1,
# MAGIC         data_termino_1,
# MAGIC         data_inicio_2,
# MAGIC         data_termino_2,
# MAGIC         data_inicio_3,
# MAGIC         data_termino_3
# MAGIC
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC ferias_origem AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 data_inicio_periodo_aquisitivo,
# MAGIC                 data_termino_periodo_aquisitivo
# MAGIC             ORDER BY sequencia
# MAGIC         ) AS ordem_duplicidade
# MAGIC
# MAGIC     FROM ferias_corrigidas
# MAGIC ),
# MAGIC
# MAGIC ferias_sem_duplicidade AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1,
# MAGIC         data_termino_1,
# MAGIC         data_inicio_2,
# MAGIC         data_termino_2,
# MAGIC         data_inicio_3,
# MAGIC         data_termino_3
# MAGIC
# MAGIC     FROM ferias_origem
# MAGIC
# MAGIC     WHERE ordem_duplicidade = 1
# MAGIC ),
# MAGIC
# MAGIC ferias_base AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         DENSE_RANK() OVER (
# MAGIC             PARTITION BY drt
# MAGIC             ORDER BY
# MAGIC                 data_inicio_periodo_aquisitivo,
# MAGIC                 data_termino_periodo_aquisitivo
# MAGIC         ) AS numero_direito_ferias
# MAGIC
# MAGIC     FROM ferias_sem_duplicidade
# MAGIC ),
# MAGIC
# MAGIC periodos_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_1 AS data_inicio_gozo,
# MAGIC         data_termino_1 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_1 IS NOT NULL
# MAGIC        OR data_termino_1 IS NOT NULL
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_2 AS data_inicio_gozo,
# MAGIC         data_termino_2 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_2 IS NOT NULL
# MAGIC        OR data_termino_2 IS NOT NULL
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_3 AS data_inicio_gozo,
# MAGIC         data_termino_3 AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_3 IS NOT NULL
# MAGIC        OR data_termino_3 IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC gozos_numerados AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 numero_direito_ferias
# MAGIC             ORDER BY
# MAGIC                 data_inicio_gozo,
# MAGIC                 data_termino_gozo
# MAGIC         ) AS numero_periodo_gozo,
# MAGIC
# MAGIC         COUNT(*) OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 numero_direito_ferias
# MAGIC         ) AS quantidade_periodos_gozo
# MAGIC
# MAGIC     FROM periodos_gozo
# MAGIC ),
# MAGIC
# MAGIC com_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN quantidade_periodos_gozo > 1
# MAGIC             THEN CONCAT(
# MAGIC                 CAST(numero_direito_ferias AS STRING),
# MAGIC                 '.',
# MAGIC                 CAST(numero_periodo_gozo AS STRING)
# MAGIC             )
# MAGIC             ELSE CAST(numero_direito_ferias AS STRING)
# MAGIC         END AS sequencial_ferias,
# MAGIC
# MAGIC         numero_periodo_gozo,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         data_inicio_gozo,
# MAGIC         data_termino_gozo
# MAGIC
# MAGIC     FROM gozos_numerados
# MAGIC ),
# MAGIC
# MAGIC sem_gozo AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         numero_direito_ferias,
# MAGIC         CAST(numero_direito_ferias AS STRING) AS sequencial_ferias,
# MAGIC         CAST(NULL AS INT) AS numero_periodo_gozo,
# MAGIC         data_inicio_periodo_aquisitivo,
# MAGIC         data_termino_periodo_aquisitivo,
# MAGIC         data_limite_aviso,
# MAGIC         data_limite_inicio,
# MAGIC         data_aviso,
# MAGIC         abono,
# MAGIC         CAST(NULL AS DATE) AS data_inicio_gozo,
# MAGIC         CAST(NULL AS DATE) AS data_termino_gozo
# MAGIC
# MAGIC     FROM ferias_base
# MAGIC
# MAGIC     WHERE data_inicio_1 IS NULL
# MAGIC       AND data_termino_1 IS NULL
# MAGIC       AND data_inicio_2 IS NULL
# MAGIC       AND data_termino_2 IS NULL
# MAGIC       AND data_inicio_3 IS NULL
# MAGIC       AND data_termino_3 IS NULL
# MAGIC ),
# MAGIC
# MAGIC fato_ferias AS (
# MAGIC     SELECT * FROM com_gozo
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM sem_gozo
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     numero_direito_ferias,
# MAGIC     sequencial_ferias,
# MAGIC     numero_periodo_gozo,
# MAGIC     data_inicio_periodo_aquisitivo,
# MAGIC     data_termino_periodo_aquisitivo,
# MAGIC     data_limite_aviso,
# MAGIC     data_limite_inicio,
# MAGIC     data_aviso,
# MAGIC     abono,
# MAGIC     data_inicio_gozo,
# MAGIC     data_termino_gozo
# MAGIC
# MAGIC FROM fato_ferias;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Persistência da Fato_Ferias
# MAGIC
# MAGIC A `Fato_Ferias` foi persistida com sucesso na camada Gold como `workspace.gold.fato_ferias`, utilizando formato Delta.
# MAGIC
# MAGIC A construção incorporou as regras definidas e validadas para o tratamento do histórico de férias:
# MAGIC
# MAGIC - exclusão dos estagiários, identificados por DRT com mais de três caracteres;
# MAGIC - tratamento das duplicidades decorrentes do processo manual de origem, mantendo, para o mesmo DRT e período aquisitivo, a ocorrência de menor `sequencia`;
# MAGIC - utilização da `sequencia` da origem exclusivamente para esse tratamento, sem transportá-la para a estrutura final da fato;
# MAGIC - ordenação cronológica dos períodos aquisitivos de cada DRT para criação de `numero_direito_ferias`;
# MAGIC - transformação dos diferentes períodos de gozo originalmente armazenados em colunas para registros em linhas;
# MAGIC - criação de `numero_periodo_gozo`;
# MAGIC - criação do identificador textual `sequencial_ferias`;
# MAGIC - preservação dos direitos que ainda não possuem período de gozo registrado.
# MAGIC
# MAGIC Durante a validação anterior à persistência, foi identificada uma inconsistência específica no DRT 325. O registro apresentava início do período aquisitivo em `17/06/2014` e término em `16/06/2014`, resultando em um período temporalmente inválido.
# MAGIC
# MAGIC A conferência da fonte e do histórico do próprio vínculo mostrou que o período imediatamente anterior era `17/06/2013` a `16/06/2014`, confirmando erro de input no ano da data de término do registro seguinte.
# MAGIC
# MAGIC Foi aplicada, portanto, a correção pontual:
# MAGIC
# MAGIC **DRT 325 — término do período aquisitivo de `16/06/2014` para `16/06/2015`.**
# MAGIC
# MAGIC A correção foi realizada exclusivamente durante a construção da camada Gold. As informações existentes nas camadas anteriores foram mantidas inalteradas, preservando a rastreabilidade entre o dado recebido da origem e o tratamento aplicado para consumo analítico.
# MAGIC
# MAGIC Com a persistência concluída, a próxima etapa consiste na validação final da tabela `workspace.gold.fato_ferias`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação final da Fato_Ferias
# MAGIC
# MAGIC Após a persistência de `workspace.gold.fato_ferias`, será realizada a validação final da tabela criada.
# MAGIC
# MAGIC A validação tem como objetivo confirmar que as regras definidas para a fato foram corretamente aplicadas e que a estrutura persistida permanece consistente após os tratamentos realizados.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - quantidade de direitos de férias;
# MAGIC - quantidade de períodos de gozo efetivamente registrados;
# MAGIC - quantidade de direitos sem período de gozo registrado;
# MAGIC - distribuição entre primeiro, segundo e terceiro períodos de gozo;
# MAGIC - inexistência de estagiários no escopo da fato;
# MAGIC - inexistência de duplicidades de `DRT + sequencial_ferias`;
# MAGIC - ausência de DRT nulo;
# MAGIC - ausência de período aquisitivo nulo;
# MAGIC - inexistência de períodos aquisitivos com término anterior ao início;
# MAGIC - inexistência de períodos de gozo incompletos;
# MAGIC - inexistência de períodos de gozo com término anterior ao início.
# MAGIC
# MAGIC Essa validação também permitirá confirmar a correção pontual aplicada ao DRT 325, cujo término do período aquisitivo foi corrigido de `16/06/2014` para `16/06/2015` durante a construção da camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC
# MAGIC     COUNT(
# MAGIC         DISTINCT CONCAT(
# MAGIC             CAST(drt AS STRING),
# MAGIC             '|',
# MAGIC             CAST(numero_direito_ferias AS STRING)
# MAGIC         )
# MAGIC     ) AS total_direitos_ferias,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_gozo IS NOT NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS total_periodos_gozo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_gozo IS NULL
# MAGIC              AND data_termino_gozo IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS direitos_sem_gozo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN numero_periodo_gozo = 1 THEN 1 ELSE 0 END
# MAGIC     ) AS periodos_gozo_1,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN numero_periodo_gozo = 2 THEN 1 ELSE 0 END
# MAGIC     ) AS periodos_gozo_2,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN numero_periodo_gozo = 3 THEN 1 ELSE 0 END
# MAGIC     ) AS periodos_gozo_3,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN LENGTH(TRIM(CAST(drt AS STRING))) > 3 THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS drts_estagiarios,
# MAGIC
# MAGIC     COUNT(*) -
# MAGIC     COUNT(
# MAGIC         DISTINCT CONCAT(
# MAGIC             CAST(drt AS STRING),
# MAGIC             '|',
# MAGIC             sequencial_ferias
# MAGIC         )
# MAGIC     ) AS duplicidades_drt_sequencial,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN drt IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS drt_nulo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_periodo_aquisitivo IS NULL
# MAGIC               OR data_termino_periodo_aquisitivo IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS periodo_aquisitivo_nulo,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_periodo_aquisitivo >
# MAGIC                  data_termino_periodo_aquisitivo THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS periodo_aquisitivo_invertido,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_gozo IS NULL
# MAGIC              AND data_termino_gozo IS NOT NULL THEN 1
# MAGIC             WHEN data_inicio_gozo IS NOT NULL
# MAGIC              AND data_termino_gozo IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS gozo_incompleto,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_gozo > data_termino_gozo THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS periodo_gozo_invertido
# MAGIC
# MAGIC FROM workspace.gold.fato_ferias;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação final da Fato_Ferias
# MAGIC
# MAGIC A validação final de `workspace.gold.fato_ferias` confirmou a consistência da estrutura persistida e dos tratamentos aplicados durante sua construção.
# MAGIC
# MAGIC A tabela apresentou:
# MAGIC
# MAGIC - **995 registros**;
# MAGIC - **340 DRTs distintos**;
# MAGIC - **873 direitos de férias**;
# MAGIC - **679 períodos de gozo registrados**;
# MAGIC - **316 direitos sem período de gozo registrado**;
# MAGIC - **557 primeiros períodos de gozo**;
# MAGIC - **114 segundos períodos de gozo**;
# MAGIC - **8 terceiros períodos de gozo**.
# MAGIC
# MAGIC Os controles de qualidade não identificaram inconsistências na estrutura final:
# MAGIC
# MAGIC - 0 registros de estagiários;
# MAGIC - 0 duplicidades de `DRT + sequencial_ferias`;
# MAGIC - 0 DRTs nulos;
# MAGIC - 0 períodos aquisitivos nulos;
# MAGIC - 0 períodos aquisitivos com término anterior ao início;
# MAGIC - 0 períodos de gozo incompletos;
# MAGIC - 0 períodos de gozo com término anterior ao início.
# MAGIC
# MAGIC A validação também confirmou o tratamento do erro de input identificado para o DRT 325. Na origem, o período aquisitivo estava registrado como `17/06/2014` a `16/06/2014`. A análise do histórico do próprio vínculo confirmou a continuidade anual dos períodos aquisitivos, permitindo corrigir o término para `16/06/2015` durante a construção da camada Gold.
# MAGIC
# MAGIC Após essa correção, o indicador de períodos aquisitivos invertidos passou de 1 para 0, sem alteração das demais quantidades de controle da fato.
# MAGIC
# MAGIC Também foi mantido o tratamento das duplicidades identificadas na planilha de origem, decorrentes de seu processo de manutenção manual. Para ocorrências com o mesmo DRT e exatamente o mesmo período aquisitivo, foi preservado o registro de menor `sequencia`, correspondente à ocorrência anterior, sendo a `sequencia` utilizada exclusivamente para esse tratamento e não incorporada à estrutura final da Gold.
# MAGIC
# MAGIC As camadas Bronze e Silver permaneceram inalteradas, preservando os dados recebidos da origem e permitindo rastrear os tratamentos de qualidade realizados na camada Gold.
# MAGIC
# MAGIC Com os controles estruturais e de qualidade atendidos, a `Fato_Ferias` é considerada concluída para utilização nas análises do MVP.
# MAGIC
# MAGIC Como melhoria futura, recomenda-se substituir o controle manual de férias por um processo com validações de entrada e regras de integridade, reduzindo a possibilidade de duplicidades e inconsistências de datas. O mesmo processo poderá incorporar mecanismos preventivos de acompanhamento de prazos e programação de férias.