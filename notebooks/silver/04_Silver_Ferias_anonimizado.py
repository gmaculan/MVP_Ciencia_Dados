# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da tabela Silver de Férias
# MAGIC
# MAGIC A tabela Silver de Férias é construída a partir de `workspace.bronze.ferias_anonimizado`.
# MAGIC
# MAGIC Como regra de qualidade dos dados, somente registros com `DRT` preenchido são considerados válidos. O `DRT` é necessário para associar o registro de férias ao respectivo vínculo empregatício.
# MAGIC
# MAGIC Consequentemente, qualquer linha da fonte cujo `DRT` esteja nulo é integralmente descartada antes do tratamento dos demais atributos. Valores existentes em outras colunas dessas linhas não são considerados, pois podem corresponder a preenchimentos residuais, fórmulas ou informações sem vínculo identificável.
# MAGIC
# MAGIC Após a aplicação dessa regra, permanecem **882 registros válidos**, correspondentes a **346 DRTs distintos**.
# MAGIC
# MAGIC ## Atributos selecionados
# MAGIC
# MAGIC Para a camada Silver foram selecionados os atributos necessários para representar o vínculo, o período aquisitivo, as datas de controle e os períodos de gozo das férias:
# MAGIC
# MAGIC - `DRT` → `drt`;
# MAGIC - `SEQUÊNCIA` → `sequencia`;
# MAGIC - `INÍCIO4` → `data_inicio_periodo_aquisitivo`;
# MAGIC - `TÉRMINO5` → `data_termino_periodo_aquisitivo`;
# MAGIC - `DATA LIMITE PARA AVISO` → `data_limite_aviso`;
# MAGIC - `DATA LIMITE PARA INÍCIO` → `data_limite_inicio`;
# MAGIC - `DATA DO AVISO` → `data_aviso`;
# MAGIC - `OPÇÃO PELO ABONO?` → `abono`;
# MAGIC - `INÍCIO12` → `data_inicio_1`;
# MAGIC - `TÉRMINO13` → `data_termino_1`;
# MAGIC - `INÍCIO 2` → `data_inicio_2`;
# MAGIC - `TÉRMINO 2` → `data_termino_2`;
# MAGIC - `INÍCIO 3` → `data_inicio_3`;
# MAGIC - `TÉRMINO 3` → `data_termino_3`.
# MAGIC
# MAGIC `SEQUÊNCIA` é preservada porque permite distinguir os diferentes registros de férias associados ao mesmo DRT.
# MAGIC
# MAGIC `INÍCIO4` e `TÉRMINO5` representam o período aquisitivo. Considerando exclusivamente os 882 registros válidos, ambos estão integralmente preenchidos.
# MAGIC
# MAGIC ## Períodos de gozo
# MAGIC
# MAGIC A fonte possui dois conjuntos parcialmente redundantes relacionados ao primeiro período de gozo.
# MAGIC
# MAGIC A conferência dos registros válidos mostrou que `INÍCIO12` e `TÉRMINO13` preservam 557 períodos, enquanto `INÍCIO 1` e `TÉRMINO 1` preservam 555. Nos registros em que ambos os conjuntos estão preenchidos, as datas correspondem, enquanto `INÍCIO12` e `TÉRMINO13` ainda preservam dois registros adicionais.
# MAGIC
# MAGIC Por esse motivo, `INÍCIO12` e `TÉRMINO13` são utilizados na Silver para representar o primeiro período de gozo, evitando redundância e perda de informação.
# MAGIC
# MAGIC Os períodos adicionais são representados por `INÍCIO 2`/`TÉRMINO 2` e `INÍCIO 3`/`TÉRMINO 3`.
# MAGIC
# MAGIC Considerando somente registros com DRT preenchido, a fonte apresenta:
# MAGIC
# MAGIC - 557 primeiros períodos de gozo;
# MAGIC - 117 segundos períodos de gozo;
# MAGIC - 8 terceiros períodos de gozo.
# MAGIC
# MAGIC ## Tratamento das datas
# MAGIC
# MAGIC A fonte contém datas representadas tanto como células de data do Excel quanto como valores textuais. A transformação trata essas diferentes representações antes da conversão para `DATE`.
# MAGIC
# MAGIC Em `DATA DO AVISO` foram identificados dois valores textuais com erro de digitação:
# MAGIC
# MAGIC - `2603/2021` → `26/03/2021`;
# MAGIC - `1002/2023` → `10/02/2023`.
# MAGIC
# MAGIC Também são removidos espaços adicionais existentes nos valores textuais antes da conversão.
# MAGIC
# MAGIC Valores ausentes nos registros válidos permanecem nulos. Nenhuma informação inexistente na fonte é criada ou inferida.
# MAGIC
# MAGIC ## Campos não selecionados
# MAGIC
# MAGIC Campos auxiliares, fórmulas de controle, quantidades deriváveis e atributos redundantes não são transportados para a Silver quando não acrescentam informação necessária ao escopo analítico definido para o MVP.
# MAGIC
# MAGIC A transformação Bronze → Silver realiza, portanto:
# MAGIC
# MAGIC 1. descarte integral das linhas sem `DRT`;
# MAGIC 2. seleção dos atributos relevantes;
# MAGIC 3. eliminação de campos redundantes e auxiliares;
# MAGIC 4. padronização dos nomes;
# MAGIC 5. tratamento das diferentes representações de data;
# MAGIC 6. preservação dos valores ausentes existentes nos registros válidos.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.silver.ferias_anonimizado AS
# MAGIC
# MAGIC WITH registros_validos AS (
# MAGIC
# MAGIC     -- PRIMEIRA REGRA:
# MAGIC     -- linhas sem DRT são descartadas integralmente antes
# MAGIC     -- de qualquer tratamento dos demais atributos.
# MAGIC     SELECT *
# MAGIC     FROM workspace.bronze.ferias_anonimizado
# MAGIC     WHERE `DRT` IS NOT NULL
# MAGIC       AND TRIM(CAST(`DRT` AS STRING)) <> ''
# MAGIC
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     TRIM(CAST(`DRT` AS STRING)) AS drt,
# MAGIC
# MAGIC     TRY_CAST(`SEQUÊNCIA` AS INT) AS sequencia,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`INÍCIO4` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO4` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`INÍCIO4` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO4` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`INÍCIO4` AS DATE)
# MAGIC     END AS data_inicio_periodo_aquisitivo,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`TÉRMINO5` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO5` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`TÉRMINO5` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO5` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`TÉRMINO5` AS DATE)
# MAGIC     END AS data_termino_periodo_aquisitivo,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`DATA LIMITE PARA AVISO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA LIMITE PARA AVISO` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`DATA LIMITE PARA AVISO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA LIMITE PARA AVISO` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`DATA LIMITE PARA AVISO` AS DATE)
# MAGIC     END AS data_limite_aviso,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN TRIM(CAST(`DATA LIMITE PARA INÍCIO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA LIMITE PARA INÍCIO` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`DATA LIMITE PARA INÍCIO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA LIMITE PARA INÍCIO` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`DATA LIMITE PARA INÍCIO` AS DATE)
# MAGIC     END AS data_limite_inicio,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `DATA DO AVISO` IS NULL
# MAGIC           OR TRIM(CAST(`DATA DO AVISO` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DO AVISO` AS STRING)) = '2603/2021'
# MAGIC             THEN TO_DATE('26/03/2021', 'dd/MM/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DO AVISO` AS STRING)) = '1002/2023'
# MAGIC             THEN TO_DATE('10/02/2023', 'dd/MM/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DO AVISO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA DO AVISO` AS STRING)), 'd/M/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DO AVISO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`DATA DO AVISO` AS STRING)), 'M/d/yy')
# MAGIC
# MAGIC         ELSE TRY_CAST(`DATA DO AVISO` AS DATE)
# MAGIC     END AS data_aviso,
# MAGIC
# MAGIC     NULLIF(
# MAGIC         TRIM(CAST(`OPÇÃO PELO ABONO?` AS STRING)),
# MAGIC         ''
# MAGIC     ) AS abono,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `INÍCIO12` IS NULL
# MAGIC           OR TRIM(CAST(`INÍCIO12` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`INÍCIO12` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO12` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`INÍCIO12` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO12` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`INÍCIO12` AS DATE)
# MAGIC     END AS data_inicio_1,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `TÉRMINO13` IS NULL
# MAGIC           OR TRIM(CAST(`TÉRMINO13` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`TÉRMINO13` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO13` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`TÉRMINO13` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO13` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`TÉRMINO13` AS DATE)
# MAGIC     END AS data_termino_1,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `INÍCIO 2` IS NULL
# MAGIC           OR TRIM(CAST(`INÍCIO 2` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`INÍCIO 2` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO 2` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`INÍCIO 2` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO 2` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`INÍCIO 2` AS DATE)
# MAGIC     END AS data_inicio_2,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `TÉRMINO 2` IS NULL
# MAGIC           OR TRIM(CAST(`TÉRMINO 2` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`TÉRMINO 2` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO 2` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`TÉRMINO 2` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO 2` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`TÉRMINO 2` AS DATE)
# MAGIC     END AS data_termino_2,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `INÍCIO 3` IS NULL
# MAGIC           OR TRIM(CAST(`INÍCIO 3` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`INÍCIO 3` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO 3` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`INÍCIO 3` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`INÍCIO 3` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`INÍCIO 3` AS DATE)
# MAGIC     END AS data_inicio_3,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN `TÉRMINO 3` IS NULL
# MAGIC           OR TRIM(CAST(`TÉRMINO 3` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC         WHEN TRIM(CAST(`TÉRMINO 3` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO 3` AS STRING)), 'd/M/yyyy')
# MAGIC         WHEN TRIM(CAST(`TÉRMINO 3` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(TRIM(CAST(`TÉRMINO 3` AS STRING)), 'M/d/yy')
# MAGIC         ELSE TRY_CAST(`TÉRMINO 3` AS DATE)
# MAGIC     END AS data_termino_3
# MAGIC
# MAGIC FROM registros_validos;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver de Férias
# MAGIC
# MAGIC Após a construção da tabela `workspace.silver.ferias_anonimizado`, será verificada a consistência dos registros resultantes da transformação Bronze → Silver.
# MAGIC
# MAGIC A validação é realizada exclusivamente sobre registros válidos. As linhas da fonte sem `DRT` já foram integralmente descartadas antes do tratamento dos demais atributos e, portanto, não participam de nenhuma das verificações abaixo.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - quantidade de registros válidos;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - eventual existência de DRT nulo ou vazio na Silver;
# MAGIC - preenchimento da sequência;
# MAGIC - preenchimento do período aquisitivo;
# MAGIC - preenchimento das datas-limite;
# MAGIC - quantidade de datas de aviso e opções pelo abono ausentes;
# MAGIC - quantidade de primeiro, segundo e terceiro períodos de gozo;
# MAGIC - existência de períodos de gozo incompletos;
# MAGIC - quantidade de registros válidos que ainda não possuem período de gozo registrado.
# MAGIC
# MAGIC A validação permitirá comparar o resultado da transformação com os registros válidos da fonte e verificar se houve perda indevida de informação durante o tratamento.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros_validos,
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
# MAGIC     SUM(CASE WHEN sequencia IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS sequencia_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_inicio_periodo_aquisitivo IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS inicio_periodo_aquisitivo_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_termino_periodo_aquisitivo IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS termino_periodo_aquisitivo_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_limite_aviso IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_limite_aviso_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_limite_inicio IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_limite_inicio_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_aviso IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS data_aviso_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN abono IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS abono_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN data_inicio_1 IS NOT NULL THEN 1 ELSE 0 END)
# MAGIC         AS primeiro_periodo_preenchido,
# MAGIC
# MAGIC     SUM(CASE WHEN data_inicio_2 IS NOT NULL THEN 1 ELSE 0 END)
# MAGIC         AS segundo_periodo_preenchido,
# MAGIC
# MAGIC     SUM(CASE WHEN data_inicio_3 IS NOT NULL THEN 1 ELSE 0 END)
# MAGIC         AS terceiro_periodo_preenchido,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (data_inicio_1 IS NULL AND data_termino_1 IS NOT NULL)
# MAGIC               OR (data_inicio_1 IS NOT NULL AND data_termino_1 IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS primeiro_periodo_incompleto,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (data_inicio_2 IS NULL AND data_termino_2 IS NOT NULL)
# MAGIC               OR (data_inicio_2 IS NOT NULL AND data_termino_2 IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS segundo_periodo_incompleto,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (data_inicio_3 IS NULL AND data_termino_3 IS NOT NULL)
# MAGIC               OR (data_inicio_3 IS NOT NULL AND data_termino_3 IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS terceiro_periodo_incompleto,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_inicio_1 IS NULL
# MAGIC              AND data_termino_1 IS NULL
# MAGIC              AND data_inicio_2 IS NULL
# MAGIC              AND data_termino_2 IS NULL
# MAGIC              AND data_inicio_3 IS NULL
# MAGIC              AND data_termino_3 IS NULL
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_sem_periodo_gozo
# MAGIC
# MAGIC FROM workspace.silver.ferias_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Conclusão da Validação da tabela Silver de Férias
# MAGIC
# MAGIC A validação da tabela `workspace.silver.ferias_anonimizado` confirmou a preservação dos registros válidos e a consistência das transformações realizadas na passagem da camada Bronze para a Silver.
# MAGIC
# MAGIC Foram obtidos **882 registros válidos**, correspondentes a **346 DRTs distintos**. Não foi identificado nenhum DRT nulo ou vazio na tabela Silver, confirmando que as linhas sem identificação de vínculo foram integralmente descartadas antes do tratamento dos demais atributos.
# MAGIC
# MAGIC Os campos `sequencia`, `data_inicio_periodo_aquisitivo`, `data_termino_periodo_aquisitivo`, `data_limite_aviso` e `data_limite_inicio` não apresentaram valores nulos nos registros válidos.
# MAGIC
# MAGIC Foram encontrados **323 registros sem `data_aviso`** e **324 registros sem informação de `abono`**. Esses valores ausentes foram preservados conforme a fonte, sem preenchimento ou inferência artificial.
# MAGIC
# MAGIC Em relação aos períodos de gozo, foram identificados:
# MAGIC
# MAGIC - **557 registros** com primeiro período de gozo;
# MAGIC - **117 registros** com segundo período de gozo;
# MAGIC - **8 registros** com terceiro período de gozo.
# MAGIC
# MAGIC Não foram encontrados períodos incompletos em nenhuma das três posições: todos os períodos que possuem data de início também possuem a correspondente data de término, e vice-versa.
# MAGIC
# MAGIC Foram identificados **323 registros válidos sem período de gozo registrado**. Esses registros foram preservados, pois possuem DRT e representam informações válidas da fonte, ainda que não apresentem período de gozo preenchido.
# MAGIC
# MAGIC Os resultados obtidos são compatíveis com os registros válidos da fonte e confirmam que a transformação para a camada Silver preservou as informações selecionadas sem introduzir registros sem DRT ou provocar perda indevida de dados.
# MAGIC
# MAGIC Com isso, a construção e a validação da tabela Silver de Férias são consideradas concluídas.