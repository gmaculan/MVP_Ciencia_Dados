# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Férias e Dependentes
# MAGIC
# MAGIC Este notebook será destinado à análise e à transformação dos dados relacionados a **férias e dependentes** dos empregados, dando continuidade ao processo de construção da camada Silver.
# MAGIC
# MAGIC As duas informações serão tratadas no mesmo notebook por estarem diretamente relacionadas à gestão dos vínculos empregatícios e às análises de Recursos Humanos previstas no MVP.
# MAGIC
# MAGIC O processamento seguirá a mesma metodologia adotada nos notebooks anteriores: inicialmente serão analisadas as estruturas disponíveis na camada Bronze, identificando os atributos relevantes e definindo seu destino na camada Silver. Em seguida, serão realizadas as análises de qualidade necessárias e, posteriormente, os tratamentos de padronização, conversão de tipos e demais transformações necessárias para a construção das tabelas Silver.
# MAGIC
# MAGIC Embora férias e dependentes sejam tratados no mesmo notebook, suas estruturas serão analisadas separadamente, respeitando as características e regras de negócio de cada conjunto de dados.
# MAGIC
# MAGIC ## 1.1 Férias
# MAGIC
# MAGIC A análise será iniciada pelos dados de **férias**, com o objetivo de compreender a estrutura disponível na camada Bronze e a forma como os períodos de férias dos vínculos empregatícios estão registrados.
# MAGIC
# MAGIC ### 1.1.1 Identificação das colunas e tipos de dados de FÉRIAS
# MAGIC
# MAGIC O primeiro passo consiste em identificar todas as colunas existentes em `workspace.bronze.ferias_anonimizado` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações ou exclusões de atributos. O objetivo é documentar a estrutura atual da fonte antes de definir o mapeamento dos atributos e os tratamentos necessários para a camada Silver.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.ferias_anonimizado;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.2 Mapeamento de atributos — FÉRIAS: Bronze → Silver
# MAGIC
# MAGIC A tabela `workspace.bronze.ferias_anonimizado` possui **35 colunas**. Nesta etapa, cada atributo será avaliado quanto ao seu significado, necessidade analítica e destino na camada Silver.
# MAGIC
# MAGIC A estrutura da fonte reflete diferentes formas de controle das férias utilizadas ao longo do tempo. As colunas `INÍCIO4` e `TÉRMINO5`, correspondentes originalmente às colunas E e F da planilha, eram utilizadas no período em que as férias não podiam ser fracionadas. Posteriormente, com a possibilidade de divisão das férias em diferentes períodos de gozo, foram introduzidas as colunas `INÍCIO12` e `TÉRMINO13`, originalmente localizadas nas colunas M e N.
# MAGIC
# MAGIC Como a própria fonte contém os períodos de férias efetivamente gozados, essas informações anteriores de início e término tornam-se redundantes para a finalidade analítica do MVP e não serão utilizadas na camada Silver.
# MAGIC
# MAGIC Da mesma forma, `DIAS DE GOZO14`, `DIAS ABONO` e `DIAS LICENÇAS`, correspondentes às colunas O a Q, não serão mantidos, pois seus valores podem ser derivados a partir das demais informações disponíveis.
# MAGIC
# MAGIC As colunas a partir da coluna X da planilha de origem foram utilizadas como campos auxiliares para fórmulas e controles. Por não representarem informações de negócio necessárias ao modelo analítico, não serão utilizadas na camada Silver.
# MAGIC
# MAGIC Além desses grupos, `UNIDADE`, `SEQUÊNCIA`, `ACERTO` e `OPÇÃO PELO ADTO. 13o?` também não serão utilizados no escopo do MVP.
# MAGIC
# MAGIC | # | Cabeçalho Bronze | Tipo Bronze | Cabeçalho Silver | Tipo Silver | Observação / destino |
# MAGIC |---:|---|---|---|---|---|
# MAGIC | 1 | `UNIDADE` | STRING | — | — | **Não utilizado em FÉRIAS.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 2 | `DRT` | BIGINT | `drt` | STRING | **Utilizado em FÉRIAS.** Identifica o vínculo empregatício. Convertido para STRING por possuir natureza de identificador. |
# MAGIC | 3 | `NOME REDUZIDO` | STRING | — | — | **Não utilizado em FÉRIAS.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 4 | `SEQUÊNCIA` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Informação de controle da fonte sem necessidade analítica para o MVP. |
# MAGIC | 5 | `INÍCIO4` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo originalmente localizado na coluna E e utilizado no período em que as férias não podiam ser fracionadas. Torna-se redundante diante dos períodos efetivamente gozados registrados na fonte. |
# MAGIC | 6 | `TÉRMINO5` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo originalmente localizado na coluna F e utilizado no período em que as férias não podiam ser fracionadas. Torna-se redundante diante dos períodos efetivamente gozados registrados na fonte. |
# MAGIC | 7 | `DATA LIMITE PARA AVISO` | TIMESTAMP | `data_limite_aviso` | DATE | **Utilizado em FÉRIAS.** Registra a data limite para que o empregado seja avisado de suas férias. |
# MAGIC | 8 | `DATA LIMITE PARA INÍCIO` | TIMESTAMP | `data_limite_inicio` | DATE | **Utilizado em FÉRIAS.** Registra a data de início limite que o empregado pode sair de férias. |
# MAGIC | 9 | `ACERTO` | STRING | — | — | **Não utilizado em FÉRIAS.** Informação de controle da origem sem necessidade analítica para o MVP. |
# MAGIC | 10 | `DATA DO AVISO` | STRING | `data_aviso` | DATE | **Utilizado em FÉRIAS.** Registra a data em que o empregado foi efetivamente avisado de suas férias. |
# MAGIC | 11 | `OPÇÃO PELO ABONO?` | STRING | `abono` | STRING | **Utilizado em FÉRIAS.** Registra se o empregado optou pelo abono. |
# MAGIC | 12 | `OPÇÃO PELO ADTO. 13o?` | STRING | — | — | **Não utilizado em FÉRIAS.** Informação que não será considerada no escopo do MVP. |
# MAGIC | 13 | `INÍCIO12` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo originalmente localizado na coluna M e introduzido com a possibilidade de fracionamento das férias. Torna-se redundante diante dos períodos efetivamente gozados registrados na fonte. |
# MAGIC | 14 | `TÉRMINO13` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo originalmente localizado na coluna N e introduzido com a possibilidade de fracionamento das férias. Torna-se redundante diante dos períodos efetivamente gozados registrados na fonte. |
# MAGIC | 15 | `DIAS DE GOZO14` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Informação derivável a partir dos períodos de férias mantidos na estrutura. |
# MAGIC | 16 | `DIAS ABONO` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Informação derivável a partir das demais informações mantidas na estrutura. |
# MAGIC | 17 | `DIAS LICENÇAS` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Informação derivável a partir das demais informações mantidas na estrutura. |
# MAGIC | 18 | `INÍCIO 1` | STRING | `inicio_1` | DATE | **Utilizado em FÉRIAS.** Registra a data de início do primeiro período de férias efetivamente gozado. |
# MAGIC | 19 | `TÉRMINO 1` | STRING | `termino_1` | DATE | **Utilizado em FÉRIAS.** Registra a data de término do primeiro período de férias efetivamente gozado. |
# MAGIC | 20 | `INÍCIO 2` | TIMESTAMP | `inicio_2` | DATE | **Utilizado em FÉRIAS.** Registra a data de início do segundo período de férias, quando houver fracionamento. |
# MAGIC | 21 | `TÉRMINO 2` | TIMESTAMP | `termino_2` | DATE | **Utilizado em FÉRIAS.** Registra a data de término do segundo período de férias, quando houver fracionamento. |
# MAGIC | 22 | `INÍCIO 3` | TIMESTAMP | `inicio_3` | DATE | **Utilizado em FÉRIAS.** Registra a data de início do terceiro período de férias, quando houver fracionamento. |
# MAGIC | 23 | `TÉRMINO 3` | TIMESTAMP | `termino_3` | DATE | **Utilizado em FÉRIAS.** Registra a data de término do terceiro período de férias, quando houver fracionamento. |
# MAGIC | 24 | `DIAS DE GOZO23` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Informação derivável a partir das demais informações mantidas na estrutura. |
# MAGIC | 25 | `1` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado em fórmulas e controles da planilha de origem. |
# MAGIC | 26 | `2` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado em fórmulas e controles da planilha de origem. |
# MAGIC | 27 | `3` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado em fórmulas e controles da planilha de origem. |
# MAGIC | 28 | `FÉRIAS COLETIVAS?` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo pertencente ao conjunto de colunas auxiliares utilizado para fórmulas e controles na planilha de origem. |
# MAGIC | 29 | `INÍCIO OFICIAL` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo pertencente ao conjunto de colunas auxiliares utilizado para fórmulas e controles na planilha de origem. |
# MAGIC | 30 | `DIAS NO MÊS` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado em fórmulas e controles da planilha de origem. |
# MAGIC | 31 | `DIAS NO MÊS SEGUINTE` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado em fórmulas e controles da planilha de origem. |
# MAGIC | 32 | `TÉRMINO OFICIAL` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo pertencente ao conjunto de colunas auxiliares utilizado para fórmulas e controles na planilha de origem. |
# MAGIC | 33 | `CHECK DIAS` | BIGINT | — | — | **Não utilizado em FÉRIAS.** Campo auxiliar utilizado para conferência e controle por fórmula na planilha de origem. |
# MAGIC | 34 | `ÚLTIMA ATUALIZAÇÃO` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo administrativo da origem sem necessidade analítica para o MVP. |
# MAGIC | 35 | `POR` | STRING | — | — | **Não utilizado em FÉRIAS.** Campo administrativo da origem sem necessidade analítica para o MVP. |

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.3 Diagnóstico dos registros de FÉRIAS
# MAGIC
# MAGIC Após a definição dos atributos que serão utilizados na camada Silver, será realizada a análise dos registros existentes em `workspace.bronze.ferias_anonimizado`.
# MAGIC
# MAGIC Inicialmente, será verificada a quantidade total de registros da fonte, a presença de registros sem identificação do vínculo empregatício (`DRT`) e a quantidade de DRTs distintos.
# MAGIC
# MAGIC Essa análise permitirá compreender a dimensão da base e sua relação com os vínculos empregatícios antes da avaliação dos períodos de férias e da qualidade dos demais atributos selecionados para a camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DRT) AS registros_com_drt,
# MAGIC     SUM(CASE WHEN DRT IS NULL THEN 1 ELSE 0 END) AS registros_sem_drt,
# MAGIC     COUNT(DISTINCT DRT) AS drts_distintos
# MAGIC FROM workspace.bronze.ferias_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC **Resultado da análise**
# MAGIC
# MAGIC A tabela `workspace.bronze.ferias_anonimizado` possui **882 registros**, todos com `DRT` preenchido, não sendo identificados registros sem vínculo empregatício associado.
# MAGIC
# MAGIC Foram encontrados **346 DRTs distintos**. Como a quantidade de registros é superior à quantidade de vínculos, um mesmo DRT pode possuir múltiplos registros na fonte, comportamento compatível com o caráter histórico dos dados de férias.
# MAGIC
# MAGIC Não foram identificados, nesta etapa, problemas relacionados à ausência de `DRT`.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.4 Quantidade de registros de férias por DRT
# MAGIC
# MAGIC Após confirmar que todos os registros possuem `DRT`, será analisada a quantidade de registros existente para cada vínculo empregatício.
# MAGIC
# MAGIC Como a tabela de férias possui caráter histórico, espera-se que um mesmo DRT possa apresentar múltiplos registros ao longo do tempo. Para auxiliar essa análise, também serão apresentadas a primeira e a última `DATA LIMITE PARA INÍCIO` registradas para cada vínculo.
# MAGIC
# MAGIC O objetivo é verificar a distribuição dos registros entre os DRTs e utilizar a data limite para início das férias como controle adicional da extensão temporal dos registros de cada vínculo.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     COUNT(*) AS qtd_registros,
# MAGIC     MIN(`DATA LIMITE PARA INÍCIO`) AS primeira_data_limite_inicio,
# MAGIC     MAX(`DATA LIMITE PARA INÍCIO`) AS ultima_data_limite_inicio
# MAGIC FROM workspace.bronze.ferias_anonimizado
# MAGIC GROUP BY DRT
# MAGIC ORDER BY qtd_registros DESC, DRT;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.4 Resultada da análise da quantidade de registros de férias por DRT**
# MAGIC
# MAGIC Foram identificados **346 DRTs distintos**, totalizando **882 registros de férias**. A quantidade de registros por vínculo varia de **1 a 24**, confirmando que a fonte mantém informações históricas e que um mesmo DRT pode possuir múltiplos registros de férias ao longo do tempo.
# MAGIC
# MAGIC Dos 346 vínculos, **198 possuem apenas 1 registro** e **67 possuem 2 registros**. Os demais apresentam históricos progressivamente maiores, chegando a **24 registros para um mesmo DRT**.
# MAGIC
# MAGIC A utilização de `DATA LIMITE PARA INÍCIO` como controle adicional também evidenciou a extensão temporal dos registros. Vínculos com maior quantidade de ocorrências apresentam períodos históricos mais extensos, enquanto vínculos com menor quantidade de registros tendem a apresentar históricos mais curtos.
# MAGIC
# MAGIC Não foram identificados DRTs sem `DATA LIMITE PARA INÍCIO` nesta análise.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.5 Verificação de repetição por DRT e data limite para início
# MAGIC
# MAGIC Como um mesmo `DRT` pode possuir diversos registros de férias ao longo do tempo, será verificado se a combinação entre `DRT` e `DATA LIMITE PARA INÍCIO` se repete na fonte.
# MAGIC
# MAGIC A `DATA LIMITE PARA INÍCIO` será utilizada nesta etapa como referência adicional para distinguir as diferentes ocorrências de férias associadas a um mesmo vínculo.
# MAGIC
# MAGIC O objetivo é identificar eventuais registros com a mesma combinação de `DRT` e `DATA LIMITE PARA INÍCIO`, permitindo avaliar posteriormente se essas ocorrências representam duplicidades ou situações distintas registradas na fonte.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA INÍCIO` AS data_limite_inicio,
# MAGIC     COUNT(*) AS qtd_registros
# MAGIC FROM workspace.bronze.ferias_anonimizado
# MAGIC GROUP BY
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA INÍCIO`
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY
# MAGIC     qtd_registros DESC,
# MAGIC     DRT,
# MAGIC     data_limite_inicio;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.5 Resultado da análise da verificação de repetição por DRT e data limite para início**
# MAGIC
# MAGIC Foram identificadas **3 combinações de `DRT` e `DATA LIMITE PARA INÍCIO` com repetição**, correspondentes aos DRTs `280`, `288` e `325`. Em cada caso foram encontrados dois registros com a mesma combinação.
# MAGIC
# MAGIC A origem desses dados deve ser considerada na interpretação dessas ocorrências. O controle de férias era realizado manualmente em planilha Excel e, para cadastrar uma nova ocorrência, era comum utilizar o registro anterior do empregado como base, copiando a linha e alterando posteriormente os campos pertinentes.
# MAGIC
# MAGIC Como esse processo não possuía as validações e críticas normalmente existentes em um sistema transacional, determinadas informações poderiam permanecer indevidamente inalteradas durante o lançamento.
# MAGIC
# MAGIC Dessa forma, a repetição de `DRT` e `DATA LIMITE PARA INÍCIO` não será considerada, isoladamente, evidência de duplicidade. Os registros identificados deverão ser comparados por meio dos demais atributos relevantes antes de qualquer decisão de tratamento.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.6 Análise dos registros com repetição de DRT e data limite para início
# MAGIC
# MAGIC As ocorrências identificadas na etapa anterior serão analisadas individualmente para verificar se representam registros efetivamente duplicados ou diferentes períodos de férias que compartilham a mesma `DATA LIMITE PARA INÍCIO`.
# MAGIC
# MAGIC Para essa análise serão apresentados os campos relevantes mantidos para a camada Silver, permitindo comparar as informações registradas em cada ocorrência.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA AVISO`,
# MAGIC     `DATA LIMITE PARA INÍCIO`,
# MAGIC     `DATA DO AVISO`,
# MAGIC     `OPÇÃO PELO ABONO?`,
# MAGIC     `INÍCIO 1`,
# MAGIC     `TÉRMINO 1`,
# MAGIC     `INÍCIO 2`,
# MAGIC     `TÉRMINO 2`,
# MAGIC     `INÍCIO 3`,
# MAGIC     `TÉRMINO 3`
# MAGIC FROM workspace.bronze.ferias_anonimizado
# MAGIC WHERE DRT IN (280, 288, 325)
# MAGIC ORDER BY
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA INÍCIO`,
# MAGIC     `INÍCIO 1`;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.6 Resultado da análise dos registros com repetição de DRT e data limite para início**
# MAGIC
# MAGIC A análise individual das combinações repetidas de `DRT` e `DATA LIMITE PARA INÍCIO` mostrou que a repetição desses dois atributos não representa, necessariamente, duplicidade de registros.
# MAGIC
# MAGIC Para o DRT `280`, os dois registros associados à mesma `DATA LIMITE PARA INÍCIO` possuem diferentes datas de aviso e diferentes períodos de férias efetivamente gozados, caracterizando ocorrências distintas.
# MAGIC
# MAGIC Nos DRTs `288` e `325`, cada combinação repetida apresenta um registro sem preenchimento das informações relacionadas ao aviso, opção pelo abono e períodos efetivamente gozados, enquanto o outro registro contém essas informações preenchidas.
# MAGIC
# MAGIC Esse comportamento é compatível com o processo manual utilizado na manutenção da planilha de origem, no qual registros anteriores podiam ser copiados como base para novos lançamentos e posteriormente alterados. Como a planilha não possuía mecanismos automáticos de validação, poderiam permanecer registros incompletos ou informações repetidas.
# MAGIC
# MAGIC Dessa forma, a combinação `DRT` + `DATA LIMITE PARA INÍCIO` não será considerada identificador único de um registro de férias, e nenhuma exclusão será realizada exclusivamente com base na repetição desses atributos.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.7 Verificação de registros sem período de férias gozado
# MAGIC
# MAGIC A análise das ocorrências com repetição de `DRT` e `DATA LIMITE PARA INÍCIO` revelou a existência de registros nos quais não há preenchimento das datas correspondentes aos períodos de férias efetivamente gozados.
# MAGIC
# MAGIC Antes de definir qualquer tratamento para essas ocorrências, será verificada sua frequência em toda a tabela.
# MAGIC
# MAGIC Para esta análise, será considerado sem período de gozo o registro em que os seis campos correspondentes aos três possíveis períodos de férias (`INÍCIO 1`, `TÉRMINO 1`, `INÍCIO 2`, `TÉRMINO 2`, `INÍCIO 3` e `TÉRMINO 3`) estejam simultaneamente nulos.
# MAGIC
# MAGIC O objetivo é determinar se esses registros constituem ocorrências pontuais ou um padrão existente na fonte, sem realizar exclusões ou transformações nesta etapa.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN `INÍCIO 1` IS NULL
# MAGIC              AND `TÉRMINO 1` IS NULL
# MAGIC              AND `INÍCIO 2` IS NULL
# MAGIC              AND `TÉRMINO 2` IS NULL
# MAGIC              AND `INÍCIO 3` IS NULL
# MAGIC              AND `TÉRMINO 3` IS NULL
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_sem_periodo_gozado,
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN `INÍCIO 1` IS NOT NULL
# MAGIC               OR `TÉRMINO 1` IS NOT NULL
# MAGIC               OR `INÍCIO 2` IS NOT NULL
# MAGIC               OR `TÉRMINO 2` IS NOT NULL
# MAGIC               OR `INÍCIO 3` IS NOT NULL
# MAGIC               OR `TÉRMINO 3` IS NOT NULL
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_com_periodo_gozado
# MAGIC FROM workspace.bronze.ferias_anonimizado;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.7 Resultado da verificação de registros sem período de férias gozado**
# MAGIC
# MAGIC Dos **882 registros** existentes na tabela de férias, **878 possuem pelo menos uma informação preenchida nos campos correspondentes aos períodos de férias efetivamente gozados**.
# MAGIC
# MAGIC Foram identificados apenas **4 registros** nos quais os seis campos de início e término dos três possíveis períodos de gozo estão simultaneamente sem preenchimento.
# MAGIC
# MAGIC Esses registros representam uma parcela reduzida da base e, considerando o processo manual de manutenção da planilha de origem, não serão descartados automaticamente. Antes da definição de qualquer tratamento na camada Silver, essas ocorrências serão analisadas individualmente para compreender sua natureza.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.8 Análise dos registros sem período de férias gozado
# MAGIC
# MAGIC Os quatro registros identificados sem preenchimento de qualquer período de férias serão analisados individualmente.
# MAGIC
# MAGIC Nesta etapa, além dos atributos selecionados para a camada Silver, serão utilizados `NOME REDUZIDO` e `SEQUÊNCIA` apenas como informações auxiliares para a interpretação dos registros na fonte. A utilização desses campos no diagnóstico não altera a decisão de descartá-los na construção da camada Silver.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `NOME REDUZIDO`,
# MAGIC     `SEQUÊNCIA`,
# MAGIC     `DATA LIMITE PARA AVISO`,
# MAGIC     `DATA LIMITE PARA INÍCIO`,
# MAGIC     `DATA DO AVISO`,
# MAGIC     `OPÇÃO PELO ABONO?`,
# MAGIC     `INÍCIO 1`,
# MAGIC     `TÉRMINO 1`,
# MAGIC     `INÍCIO 2`,
# MAGIC     `TÉRMINO 2`,
# MAGIC     `INÍCIO 3`,
# MAGIC     `TÉRMINO 3`
# MAGIC FROM workspace.bronze.ferias_anonimizado
# MAGIC WHERE `INÍCIO 1` IS NULL
# MAGIC   AND `TÉRMINO 1` IS NULL
# MAGIC   AND `INÍCIO 2` IS NULL
# MAGIC   AND `TÉRMINO 2` IS NULL
# MAGIC   AND `INÍCIO 3` IS NULL
# MAGIC   AND `TÉRMINO 3` IS NULL
# MAGIC ORDER BY
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA INÍCIO`;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `SEQUÊNCIA`,
# MAGIC     `DATA LIMITE PARA AVISO`,
# MAGIC     `DATA LIMITE PARA INÍCIO`,
# MAGIC     `DATA DO AVISO`,
# MAGIC     `INÍCIO 1`,
# MAGIC     `TÉRMINO 1`,
# MAGIC     `INÍCIO 2`,
# MAGIC     `TÉRMINO 2`,
# MAGIC     `INÍCIO 3`,
# MAGIC     `TÉRMINO 3`
# MAGIC FROM workspace.bronze.ferias_anonimizado
# MAGIC WHERE DRT IN (476, 493)
# MAGIC ORDER BY
# MAGIC     DRT,
# MAGIC     `DATA LIMITE PARA INÍCIO`;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.8 Resultado da análise dos registros sem período de férias gozado**
# MAGIC
# MAGIC Foram identificados **4 registros sem preenchimento de qualquer período de férias efetivamente gozado**, pertencentes a apenas dois vínculos: DRTs `476` e `493`.
# MAGIC
# MAGIC A análise do histórico completo desses vínculos mostrou que esses registros se encontram no final das respectivas sequências de férias.
# MAGIC
# MAGIC A ausência das datas de gozo no registro mais recente de um vínculo **não caracteriza necessariamente um erro ou problema de qualidade dos dados**. Dependendo do momento em que a planilha foi gerada e disponibilizada para utilização no MVP, o empregado poderia ainda não ter definido ou realizado o respectivo período de férias. Nesse caso, o registro poderia existir para fins de controle, mesmo sem as datas do período efetivamente gozado preenchidas.
# MAGIC
# MAGIC Entretanto, a existência de mais de um registro consecutivo sem período de gozo permite uma análise adicional. Quando já existe para o mesmo `DRT` um registro posterior, com uma `DATA LIMITE PARA INÍCIO` mais recente, a ausência das datas de gozo no registro imediatamente anterior deixa de poder ser explicada apenas pelo fato de o período mais recente ainda não ter sido definido no momento da extração.
# MAGIC
# MAGIC Dessa forma, os registros mais recentes sem período de gozo podem representar situações ainda em aberto na data de extração da fonte, enquanto registros anteriores também sem período de gozo apresentam indício de informação histórica incompleta.
# MAGIC
# MAGIC Como os dados disponíveis não permitem reconstruir com segurança os períodos de férias ausentes, nenhum valor será inferido ou preenchido artificialmente. Os registros serão preservados, mantendo-se os valores nulos existentes na fonte.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.9 Verificação de consistência dos períodos de férias
# MAGIC
# MAGIC Como os períodos efetivamente gozados serão representados na camada Silver pelas datas de início e término dos três possíveis períodos de férias, será verificada a consistência desses pares de datas.
# MAGIC
# MAGIC A análise buscará identificar registros em que apenas uma das datas do período esteja preenchida, bem como situações em que a data de término seja anterior à respectiva data de início.
# MAGIC
# MAGIC Essa verificação permitirá identificar eventuais inconsistências nos períodos de férias antes da realização das transformações para a camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (`INÍCIO 1` IS NULL AND `TÉRMINO 1` IS NOT NULL)
# MAGIC               OR (`INÍCIO 1` IS NOT NULL AND `TÉRMINO 1` IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS inconsistencias_periodo_1,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (`INÍCIO 2` IS NULL AND `TÉRMINO 2` IS NOT NULL)
# MAGIC               OR (`INÍCIO 2` IS NOT NULL AND `TÉRMINO 2` IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS inconsistencias_periodo_2,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN (`INÍCIO 3` IS NULL AND `TÉRMINO 3` IS NOT NULL)
# MAGIC               OR (`INÍCIO 3` IS NOT NULL AND `TÉRMINO 3` IS NULL)
# MAGIC             THEN 1 ELSE 0
# MAGIC         END
# MAGIC     ) AS inconsistencias_periodo_3
# MAGIC FROM workspace.bronze.ferias_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.9 Resultado da verificação de consistência dos períodos de férias**
# MAGIC
# MAGIC Não foram identificadas inconsistências de preenchimento nos três possíveis períodos de férias.
# MAGIC
# MAGIC Para os períodos 1, 2 e 3, não existem registros em que apenas a data de início ou apenas a data de término esteja preenchida. Sempre que um período possui uma das datas registrada, a respectiva data complementar também está presente.
# MAGIC
# MAGIC O resultado indica consistência estrutural no preenchimento dos pares de datas que representam os períodos de férias efetivamente gozados.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.10 Verificação da consistência cronológica dos períodos de férias
# MAGIC
# MAGIC Após a verificação da integridade do preenchimento dos pares de início e término, será analisada a consistência cronológica das datas relacionadas ao gozo das férias.
# MAGIC
# MAGIC A análise considerará a sequência esperada entre a data do aviso e os períodos de férias efetivamente gozados. Quando houver fracionamento, será verificado se os períodos foram registrados em ordem cronológica, considerando seus respectivos inícios e términos.
# MAGIC
# MAGIC Serão verificadas as seguintes condições:
# MAGIC
# MAGIC - a `DATA DO AVISO` deve ser anterior ao início do primeiro período de férias;
# MAGIC - o término de cada período não deve ser anterior ao respectivo início;
# MAGIC - quando houver segundo período, seu início deve ser posterior ao término do primeiro;
# MAGIC - quando houver terceiro período, seu início deve ser posterior ao término do segundo;
# MAGIC - o início do último período de férias registrado deve ser anterior ou igual à `DATA LIMITE PARA INÍCIO`.
# MAGIC
# MAGIC Para a última verificação será adotada uma regra simplificada para o MVP. Em situações de férias fracionadas, a determinação do prazo aplicável pode depender também da quantidade de dias já gozados nos períodos anteriores e das regras relacionadas ao fracionamento das férias. Essa complexidade não será reproduzida neste projeto. Assim, a `DATA LIMITE PARA INÍCIO` será utilizada apenas como referência para verificar se o último período registrado se inicia até essa data.
# MAGIC
# MAGIC A ausência dos períodos 2 e 3 não será considerada inconsistência, pois as férias podem ter sido gozadas em um único período ou fracionadas em quantidade menor de períodos.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH ferias_datas AS (
# MAGIC     SELECT
# MAGIC         DRT,
# MAGIC         `SEQUÊNCIA`,
# MAGIC
# MAGIC         `DATA DO AVISO` AS data_aviso_original,
# MAGIC         `DATA LIMITE PARA INÍCIO` AS data_limite_inicio_original,
# MAGIC         `INÍCIO 1` AS inicio_1_original,
# MAGIC         `TÉRMINO 1` AS termino_1_original,
# MAGIC         `INÍCIO 2` AS inicio_2_original,
# MAGIC         `TÉRMINO 2` AS termino_2_original,
# MAGIC         `INÍCIO 3` AS inicio_3_original,
# MAGIC         `TÉRMINO 3` AS termino_3_original,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             try_to_date(`DATA DO AVISO`, 'M/d/yy'),
# MAGIC             try_to_date(`DATA DO AVISO`, 'dd/MM/yyyy')
# MAGIC         ) AS data_aviso,
# MAGIC
# MAGIC         CAST(`DATA LIMITE PARA INÍCIO` AS DATE) AS data_limite_inicio,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             try_to_date(`INÍCIO 1`, 'M/d/yy'),
# MAGIC             try_to_date(`INÍCIO 1`, 'dd/MM/yyyy')
# MAGIC         ) AS inicio_1,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             try_to_date(`TÉRMINO 1`, 'M/d/yy'),
# MAGIC             try_to_date(`TÉRMINO 1`, 'dd/MM/yyyy')
# MAGIC         ) AS termino_1,
# MAGIC
# MAGIC         CAST(`INÍCIO 2` AS DATE) AS inicio_2,
# MAGIC         CAST(`TÉRMINO 2` AS DATE) AS termino_2,
# MAGIC         CAST(`INÍCIO 3` AS DATE) AS inicio_3,
# MAGIC         CAST(`TÉRMINO 3` AS DATE) AS termino_3
# MAGIC
# MAGIC     FROM workspace.bronze.ferias_anonimizado
# MAGIC ),
# MAGIC
# MAGIC ferias_validacao AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         CASE
# MAGIC             WHEN inicio_3 IS NOT NULL THEN inicio_3
# MAGIC             WHEN inicio_2 IS NOT NULL THEN inicio_2
# MAGIC             ELSE inicio_1
# MAGIC         END AS inicio_ultimo_periodo
# MAGIC
# MAGIC     FROM ferias_datas
# MAGIC ),
# MAGIC
# MAGIC resultado AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN data_aviso IS NOT NULL
# MAGIC              AND inicio_1 IS NOT NULL
# MAGIC              AND data_aviso > inicio_1
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS aviso_apos_inicio,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN inicio_1 IS NOT NULL
# MAGIC              AND termino_1 IS NOT NULL
# MAGIC              AND termino_1 < inicio_1
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS periodo_1_inconsistente,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN termino_1 IS NOT NULL
# MAGIC              AND inicio_2 IS NOT NULL
# MAGIC              AND inicio_2 <= termino_1
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS ordem_1_2_inconsistente,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN inicio_2 IS NOT NULL
# MAGIC              AND termino_2 IS NOT NULL
# MAGIC              AND termino_2 < inicio_2
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS periodo_2_inconsistente,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN termino_2 IS NOT NULL
# MAGIC              AND inicio_3 IS NOT NULL
# MAGIC              AND inicio_3 <= termino_2
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS ordem_2_3_inconsistente,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN inicio_3 IS NOT NULL
# MAGIC              AND termino_3 IS NOT NULL
# MAGIC              AND termino_3 < inicio_3
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS periodo_3_inconsistente,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN inicio_ultimo_periodo IS NOT NULL
# MAGIC              AND data_limite_inicio IS NOT NULL
# MAGIC              AND inicio_ultimo_periodo > data_limite_inicio
# MAGIC             THEN 1 ELSE 0
# MAGIC         END AS ultimo_periodo_apos_data_limite
# MAGIC
# MAGIC     FROM ferias_validacao
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `SEQUÊNCIA`,
# MAGIC     data_aviso_original,
# MAGIC     data_limite_inicio_original,
# MAGIC     inicio_1_original,
# MAGIC     termino_1_original,
# MAGIC     inicio_2_original,
# MAGIC     termino_2_original,
# MAGIC     inicio_3_original,
# MAGIC     termino_3_original,
# MAGIC     aviso_apos_inicio,
# MAGIC     periodo_1_inconsistente,
# MAGIC     ordem_1_2_inconsistente,
# MAGIC     periodo_2_inconsistente,
# MAGIC     ordem_2_3_inconsistente,
# MAGIC     periodo_3_inconsistente,
# MAGIC     ultimo_periodo_apos_data_limite
# MAGIC
# MAGIC FROM resultado
# MAGIC
# MAGIC WHERE aviso_apos_inicio = 1
# MAGIC    OR periodo_1_inconsistente = 1
# MAGIC    OR ordem_1_2_inconsistente = 1
# MAGIC    OR periodo_2_inconsistente = 1
# MAGIC    OR ordem_2_3_inconsistente = 1
# MAGIC    OR periodo_3_inconsistente = 1
# MAGIC    OR ultimo_periodo_apos_data_limite = 1
# MAGIC
# MAGIC ORDER BY
# MAGIC     DRT,
# MAGIC     `SEQUÊNCIA`;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.10 Resultado da verificação da consistência cronológica dos períodos de férias**
# MAGIC
# MAGIC A análise consolidada da consistência cronológica identificou **29 registros** que atenderam a pelo menos uma das condições verificadas. Como um mesmo registro pode atender a mais de uma condição, as quantidades de ocorrências por regra não devem ser somadas.
# MAGIC
# MAGIC Não foram identificados casos em que a data de término fosse anterior à respectiva data de início nos períodos 1, 2 ou 3. Também não foram encontradas inconsistências na sequência cronológica entre os períodos 2 e 3.
# MAGIC
# MAGIC Foi identificada **1 ocorrência de inconsistência entre os períodos 1 e 2**, referente ao DRT `280`, sequência 4, na qual o mesmo intervalo de férias foi registrado nos dois períodos. Considerando o processo manual utilizado na manutenção da planilha de origem, essa ocorrência é compatível com a prática de copiar um registro anterior para iniciar um novo lançamento sem que todos os campos fossem posteriormente alterados. O registro será preservado, sem correção por inferência.
# MAGIC
# MAGIC Foram identificados **5 registros em que a `DATA DO AVISO` é posterior à data de início do primeiro período de férias**. Entre essas ocorrências, o DRT `273`, sequência 1, corresponde a um erro conhecido de preenchimento do DRT: o registro pertence a outro profissional, diferente daquele associado ao registro seguinte. Como os dados disponíveis não permitem determinar com segurança qual seria o DRT correto, nenhuma correção será realizada por inferência. As demais ocorrências também serão preservadas conforme registradas na fonte, pois não existem informações suficientes para determinar com segurança qual informação deveria ser corrigida.
# MAGIC
# MAGIC Na comparação com a `DATA LIMITE PARA INÍCIO`, foram identificados **25 registros em que o início do último período registrado ocorre após essa data**. Esse resultado não será interpretado automaticamente como erro. Nos casos de férias fracionadas, a avaliação correta depende também da quantidade de dias já gozados nos períodos anteriores e das regras aplicáveis ao fracionamento, lógica que não será reproduzida no escopo deste MVP.
# MAGIC
# MAGIC Assim, a comparação com a `DATA LIMITE PARA INÍCIO` constitui uma **verificação simplificada de consistência**. Nos casos sem fracionamento, o início do único período após a data limite representa um indício de ultrapassagem do prazo conforme as informações disponíveis na fonte; nos casos fracionados, a condição isoladamente não é suficiente para caracterizar uma inconsistência.
# MAGIC
# MAGIC De forma geral, os dados apresentam **consistência cronológica satisfatória para os objetivos do MVP**. As exceções identificadas serão preservadas, e nenhuma data ou DRT será reconstruído ou corrigido por inferência. Na camada Silver serão realizados os tratamentos de padronização, conversão de tipos e organização dos atributos, mantendo-se as informações efetivamente disponíveis na fonte.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 Dependentes
# MAGIC
# MAGIC Nesta seção serão analisados os dados de **dependentes dos empregados**, com o objetivo de compreender a estrutura disponível na camada Bronze e identificar os atributos necessários para as análises previstas no MVP.
# MAGIC
# MAGIC Os dependentes estão associados aos vínculos empregatícios e possuem relevância principalmente para a análise dos custos relacionados ao plano de saúde, uma vez que esses custos podem variar de acordo com características como a idade do dependente.
# MAGIC
# MAGIC Inicialmente será analisada a estrutura da tabela disponível na camada Bronze. Em seguida, serão definidos os atributos relevantes para a camada Silver e realizadas as verificações de qualidade necessárias antes das transformações.
# MAGIC
# MAGIC ### 1.2.1 Identificação das colunas e tipos de dados de DEPENDENTES
# MAGIC
# MAGIC O primeiro passo consiste em identificar todas as colunas existentes em `workspace.bronze.dependentes_anonimizados` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações ou exclusões de atributos. O objetivo é documentar a estrutura atual da fonte antes de definir o mapeamento dos atributos e os tratamentos necessários para a camada Silver.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.dependentes_anonimizados;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.2 Mapeamento dos atributos de DEPENDENTES
# MAGIC
# MAGIC Após a identificação da estrutura da tabela `workspace.bronze.dependentes_anonimizados`, foram definidos os atributos relevantes para a camada Silver.
# MAGIC
# MAGIC Para o escopo do MVP serão mantidas as informações necessárias para identificar o vínculo ao qual o dependente está associado, identificar o dependente e caracterizar seu parentesco e nascimento. Esses atributos permitirão posteriormente relacionar os dependentes aos empregados e apoiar as análises relacionadas ao plano de saúde.
# MAGIC
# MAGIC As demais colunas possuem finalidade administrativa ou não são necessárias para as análises previstas no projeto e, portanto, não serão incorporadas à tabela Silver de dependentes.
# MAGIC
# MAGIC | Coluna Bronze | Destino | Nome na Silver | Tipo previsto | Observação |
# MAGIC |---|---|---|---|---|
# MAGIC | `UNIDADE` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `DRT` | DEPENDENTE | `drt` | STRING | Identifica o vínculo empregatício ao qual o dependente está associado |
# MAGIC | `MATRÍCULA IBRATI` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `NOME REDUZIDO` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `SEQUÊNCIA` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `GÊNERO` | DEPENDENTE | `genero` | STRING | Gênero do dependente |
# MAGIC | `NOME` | DEPENDENTE | `nome` | STRING | Nome anonimizado do dependente |
# MAGIC | `PARENTESCO` | DEPENDENTE | `parentesco` | STRING | Relação de parentesco do dependente com o empregado |
# MAGIC | `NASCIMENTO` | DEPENDENTE | `data_nascimento` | DATE | Data de nascimento do dependente |
# MAGIC | `CONSIDERA EM IR?` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `CONSIDERA EM SF?` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `PENSÃO?` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `CONTROLE` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `MATRÍCULA` | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `ÚLTIMA ATUALIZAÇÃO` | Não utilizada | — | — | Campo administrativo da fonte |
# MAGIC | `POR` | Não utilizada | — | — | Campo administrativo da fonte |

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.3 Diagnóstico dos registros de Dependentes
# MAGIC
# MAGIC Após a definição dos atributos que serão utilizados na camada Silver, será realizada uma análise inicial dos registros existentes na tabela de dependentes.
# MAGIC
# MAGIC Nesta etapa será verificada a quantidade total de registros, a presença de `DRT` e a quantidade de vínculos empregatícios distintos associados aos dependentes.
# MAGIC
# MAGIC Como o `DRT` representa o vínculo empregatício ao qual o dependente está associado, sua presença é necessária para permitir posteriormente o relacionamento dos dependentes com os empregados.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DRT) AS registros_com_drt,
# MAGIC     SUM(CASE WHEN DRT IS NULL THEN 1 ELSE 0 END) AS registros_sem_drt,
# MAGIC     COUNT(DISTINCT DRT) AS drts_distintos
# MAGIC FROM workspace.bronze.dependentes_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.3 Resultado da análise do diagnóstico dos registros de Dependentes**
# MAGIC
# MAGIC A tabela `workspace.bronze.dependentes_anonimizados` possui **218 registros**, todos com `DRT` preenchido, não sendo identificados registros sem vínculo empregatício associado.
# MAGIC
# MAGIC Foram encontrados **130 DRTs distintos**. Como a quantidade de registros é superior à quantidade de vínculos, um mesmo DRT pode possuir mais de um dependente associado.
# MAGIC
# MAGIC Não foram identificados, nesta etapa, problemas relacionados à ausência de `DRT`.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.4 Verificação de valores nulos nos atributos selecionados
# MAGIC
# MAGIC Após a análise inicial dos registros, será verificada a presença de valores nulos nos atributos de dependentes selecionados para a camada Silver: `DRT`, `GÊNERO`, `NOME`, `PARENTESCO` e `NASCIMENTO`.
# MAGIC
# MAGIC O objetivo é identificar eventuais ausências de informação nos campos que serão efetivamente utilizados no MVP antes da realização das transformações para a camada Silver.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(CASE WHEN DRT IS NULL THEN 1 ELSE 0 END) AS nulos_drt,
# MAGIC     SUM(CASE WHEN `GÊNERO` IS NULL THEN 1 ELSE 0 END) AS nulos_genero,
# MAGIC     SUM(CASE WHEN `NOME` IS NULL THEN 1 ELSE 0 END) AS nulos_nome,
# MAGIC     SUM(CASE WHEN `PARENTESCO` IS NULL THEN 1 ELSE 0 END) AS nulos_parentesco,
# MAGIC     SUM(CASE WHEN `NASCIMENTO` IS NULL THEN 1 ELSE 0 END) AS nulos_nascimento
# MAGIC
# MAGIC FROM workspace.bronze.dependentes_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.4 Resultado da verificação de valores nulos nos atributos selecionados**
# MAGIC
# MAGIC Não foram identificados valores nulos nos atributos selecionados para a camada Silver.
# MAGIC
# MAGIC Os **218 registros** possuem `DRT`, `GÊNERO`, `NOME`, `PARENTESCO` e `NASCIMENTO` preenchidos.
# MAGIC
# MAGIC Dessa forma, não será necessário tratamento de valores nulos nesses atributos durante a construção da camada Silver.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.5 Verificação de possíveis registros duplicados de dependentes
# MAGIC
# MAGIC Após a análise de completude dos atributos selecionados, será verificada a existência de possíveis registros duplicados de dependentes.
# MAGIC
# MAGIC A repetição de um mesmo nome na base não caracteriza, isoladamente, uma duplicidade, pois pessoas diferentes podem possuir nomes iguais. Por esse motivo, a análise considerará inicialmente a combinação entre `DRT` e `NOME`, verificando se um mesmo nome de dependente aparece mais de uma vez associado ao mesmo vínculo empregatício.
# MAGIC
# MAGIC Caso sejam encontradas repetições, os demais atributos selecionados — `GÊNERO`, `PARENTESCO` e `NASCIMENTO` — serão utilizados para avaliar se os registros representam efetivamente o mesmo dependente.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `NOME`,
# MAGIC     COUNT(*) AS qtd_registros
# MAGIC FROM workspace.bronze.dependentes_anonimizados
# MAGIC GROUP BY
# MAGIC     DRT,
# MAGIC     `NOME`
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY
# MAGIC     qtd_registros DESC,
# MAGIC     DRT,
# MAGIC     `NOME`;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.5 Resultado da verificação de possíveis registros duplicados de dependentese**
# MAGIC
# MAGIC Não foram identificadas repetições da combinação `DRT` + `NOME` na tabela de dependentes.
# MAGIC
# MAGIC Dessa forma, nenhum dependente aparece mais de uma vez com o mesmo nome associado ao mesmo vínculo empregatício.
# MAGIC
# MAGIC Como não foram encontradas ocorrências nessa verificação, não foi necessário utilizar `GÊNERO`, `PARENTESCO` e `NASCIMENTO` para aprofundar a análise de possíveis duplicidades.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.6 Verificação de dependentes com a mesma data de nascimento
# MAGIC
# MAGIC Após a verificação de possíveis repetições de dependentes por `DRT` e `NOME`, será analisada a existência de dependentes associados ao mesmo vínculo empregatício que possuam a mesma data de nascimento.
# MAGIC
# MAGIC A ocorrência de uma mesma data de nascimento para mais de um dependente do mesmo DRT não caracteriza necessariamente uma duplicidade, pois pode representar, por exemplo, dependentes nascidos na mesma data. Caso sejam encontradas ocorrências, os respectivos registros serão analisados individualmente antes de qualquer conclusão.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT,
# MAGIC     `NASCIMENTO`,
# MAGIC     COUNT(*) AS qtd_dependentes
# MAGIC FROM workspace.bronze.dependentes_anonimizados
# MAGIC GROUP BY
# MAGIC     DRT,
# MAGIC     `NASCIMENTO`
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY
# MAGIC     qtd_dependentes DESC,
# MAGIC     DRT,
# MAGIC     `NASCIMENTO`;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.6 Resultado da verificação de dependentes com a mesma data de nascimento**
# MAGIC
# MAGIC Foi identificada apenas **1 ocorrência de dependentes associados ao mesmo DRT com a mesma data de nascimento**.
# MAGIC
# MAGIC O DRT `426` possui dois dependentes distintos, ambos registrados como `FILHO(A)`, com nomes diferentes e a mesma data de nascimento (`10/9/14`). Os registros são compatíveis com a possibilidade de irmãos gêmeos e não apresentam evidência de duplicidade.
# MAGIC
# MAGIC Dessa forma, os dois registros serão preservados, não sendo necessário qualquer tratamento de duplicidade com base na data de nascimento.
# MAGIC