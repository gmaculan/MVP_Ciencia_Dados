# Databricks notebook source
# MAGIC %md
# MAGIC # Questões de Negócio — Faturamento
# MAGIC
# MAGIC ## 1. Contexto e objetivo
# MAGIC
# MAGIC Este módulo analisa o faturamento da empresa a partir do histórico disponível, com o objetivo de fornecer aos **Gerentes e à Diretoria** informações para o acompanhamento da receita, de sua composição e de sua evolução ao longo do tempo.
# MAGIC
# MAGIC As análises consideram diferentes perspectivas do faturamento, incluindo período e cliente, além da concentração da receita, da evolução da participação dos principais clientes e do comportamento do ticket médio das notas fiscais.
# MAGIC
# MAGIC Também será realizada uma análise de previsão de faturamento com base no histórico disponível. Essa previsão terá caráter analítico e deverá ser interpretada de acordo com as características e limitações dos dados utilizados, não representando compromisso de receita futura.
# MAGIC
# MAGIC A análise de faturamento por alocação não integra este módulo, pois os dados disponíveis de alocação não representam o histórico completo necessário para estabelecer de forma consistente essa relação ao longo de todo o período analisado.
# MAGIC
# MAGIC As questões de negócio analisadas neste módulo são:
# MAGIC
# MAGIC 1. Qual o faturamento total por mês e por ano?
# MAGIC 2. Qual o faturamento por cliente?
# MAGIC 3. Como o faturamento evoluiu ao longo do tempo?
# MAGIC 4. Qual é a concentração de faturamento nos cinco maiores clientes?
# MAGIC 5. Como a participação dos maiores clientes no faturamento total evoluiu ao longo do tempo?
# MAGIC 6. Quais clientes aumentaram ou reduziram sua participação no faturamento?
# MAGIC 7. Qual o ticket médio das notas fiscais emitidas por mês?
# MAGIC 8. Qual o ticket médio das notas fiscais por cliente?
# MAGIC
# MAGIC As análises serão desenvolvidas individualmente, com a apresentação da consulta utilizada, dos resultados obtidos e de sua interpretação sob a perspectiva do negócio.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. Qual o faturamento total por mês e por ano?
# MAGIC
# MAGIC **Objetivo:** analisar o faturamento total da empresa ao longo do histórico disponível, permitindo aos **Gerentes e à Diretoria** acompanhar os valores faturados mensal e anualmente e identificar diferenças entre os períodos.
# MAGIC
# MAGIC A análise utiliza a **data de competência** das notas fiscais como referência temporal e o valor faturado registrado em cada nota fiscal.
# MAGIC
# MAGIC Serão apresentados, para cada mês, o faturamento mensal e o faturamento acumulado no respectivo ano. Dessa forma, uma única consulta permite acompanhar simultaneamente a evolução mensal e o total anual do faturamento.
# MAGIC
# MAGIC O histórico disponível não contém anos completos em suas extremidades: os dados iniciam em **novembro de 2011** e, em **2025**, alcançam **20 de outubro**. Esses períodos devem, portanto, ser interpretados como parciais e não comparados diretamente com anos completos sem considerar essa limitação.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_mensal AS (
# MAGIC     SELECT
# MAGIC         YEAR(data_competencia) AS ano,
# MAGIC         MONTH(data_competencia) AS mes,
# MAGIC         DATE_FORMAT(data_competencia, 'MM/yyyy') AS competencia,
# MAGIC         SUM(valor) AS faturamento_mensal
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY
# MAGIC         YEAR(data_competencia),
# MAGIC         MONTH(data_competencia),
# MAGIC         DATE_FORMAT(data_competencia, 'MM/yyyy')
# MAGIC ),
# MAGIC
# MAGIC resultado AS (
# MAGIC     SELECT
# MAGIC         ano,
# MAGIC         mes,
# MAGIC         competencia,
# MAGIC         faturamento_mensal,
# MAGIC         SUM(faturamento_mensal) OVER (
# MAGIC             PARTITION BY ano
# MAGIC         ) AS faturamento_anual
# MAGIC     FROM faturamento_mensal
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano AS `Ano`,
# MAGIC     mes AS `Mês`,
# MAGIC     competencia AS `Competência`,
# MAGIC     ROUND(faturamento_mensal, 2) AS `Faturamento Mensal`,
# MAGIC     ROUND(faturamento_anual, 2) AS `Faturamento Anual`
# MAGIC FROM resultado
# MAGIC ORDER BY
# MAGIC     ano,
# MAGIC     mes;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1. Conclusão da Qual o faturamento total por mês e por ano?
# MAGIC
# MAGIC O histórico analisado compreende **168 competências mensais**, entre novembro de 2011 e outubro de 2025. Para comparações entre anos completos, deve-se considerar o intervalo de **2012 a 2024**, uma vez que 2011 e 2025 possuem cobertura parcial.
# MAGIC
# MAGIC Entre os anos completos, o maior faturamento foi registrado em **2019, com R$ 16.228.170,72**. Em **2024**, o faturamento totalizou **R$ 10.367.518,30**, representando uma redução de aproximadamente **19,62% em relação a 2023**, quando o faturamento foi de R$ 12.898.736,78.
# MAGIC
# MAGIC A visão mensal complementa a análise anual ao permitir identificar as oscilações de faturamento dentro de cada exercício, enquanto o total anual facilita a comparação da receita entre os diferentes anos do histórico.
# MAGIC
# MAGIC Os valores de **2011 (R$ 971.643,16)** e **2025 (R$ 2.231.181,42)** não devem ser comparados diretamente com os totais dos anos completos, pois correspondem, respectivamente, somente aos períodos de novembro a dezembro de 2011 e de janeiro a outubro de 2025.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2. Qual o faturamento por cliente?
# MAGIC
# MAGIC **Objetivo:** identificar quanto cada cliente representa em faturamento ao longo do histórico disponível, permitindo aos **Gerentes e à Diretoria** comparar o volume de receita gerado pelos diferentes clientes atendidos pela empresa.
# MAGIC
# MAGIC A análise consolida o valor das notas fiscais por cliente e apresenta, para cada um, o **faturamento total**, a **quantidade de notas fiscais emitidas** e sua **participação percentual no faturamento total da empresa** no período disponível.
# MAGIC
# MAGIC Os clientes são apresentados em ordem decrescente de faturamento, facilitando a identificação daqueles que possuem maior representatividade na receita histórica.
# MAGIC
# MAGIC Esta análise apresenta uma visão consolidada de todo o período disponível. A concentração do faturamento nos maiores clientes e a evolução de suas participações ao longo do tempo serão analisadas separadamente nas questões específicas deste módulo.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_cliente AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         COUNT(*) AS quantidade_notas,
# MAGIC         SUM(valor) AS faturamento_cliente
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY cliente
# MAGIC ),
# MAGIC
# MAGIC total_faturamento AS (
# MAGIC     SELECT
# MAGIC         SUM(faturamento_cliente) AS faturamento_total
# MAGIC     FROM faturamento_cliente
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     f.cliente AS `Cliente`,
# MAGIC     f.quantidade_notas AS `Quantidade de Notas`,
# MAGIC     ROUND(f.faturamento_cliente, 2) AS `Faturamento Total`,
# MAGIC     ROUND(
# MAGIC         100.0 * f.faturamento_cliente / t.faturamento_total,
# MAGIC         2
# MAGIC     ) AS `Participação no Faturamento (%)`
# MAGIC FROM faturamento_cliente f
# MAGIC CROSS JOIN total_faturamento t
# MAGIC ORDER BY
# MAGIC     f.faturamento_cliente DESC,
# MAGIC     f.cliente;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2. Conclusão da Qual o faturamento por cliente?
# MAGIC
# MAGIC No histórico disponível, foram identificados **35 clientes**, responsáveis por **3.907 notas fiscais** e por um faturamento total de **R$ 169.509.653,22**.
# MAGIC
# MAGIC O cliente **BRAVIA** apresentou o maior faturamento acumulado, com **R$ 86.321.355,10**, correspondentes a **50,92%** de todo o faturamento registrado. Em seguida aparece **LUMINA**, com **R$ 27.574.994,62** e participação de **16,27%**.
# MAGIC
# MAGIC O terceiro maior faturamento pertence ao cliente **FALCON**, com **R$ 10.714.213,73**, equivalente a **6,32%** do total. Somados, os três clientes representam aproximadamente **73,51%** do faturamento histórico.
# MAGIC
# MAGIC Os resultados mostram diferenças relevantes na contribuição dos clientes para a receita da empresa e permitem aos Gerentes e à Diretoria identificar quais relacionamentos comerciais possuem maior representatividade no faturamento acumulado.
# MAGIC
# MAGIC Esta análise apresenta a participação consolidada de cada cliente em todo o histórico disponível. A concentração nos cinco maiores clientes e a evolução dessa participação ao longo do tempo serão examinadas separadamente nas questões específicas deste módulo.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. Como o faturamento evoluiu ao longo do tempo?
# MAGIC
# MAGIC **Objetivo:** avaliar a evolução do faturamento da empresa ao longo do histórico disponível, permitindo aos **Gerentes e à Diretoria** identificar períodos de crescimento ou redução da receita e a intensidade dessas variações.
# MAGIC
# MAGIC Para garantir comparabilidade entre os períodos, a análise considera os **anos completos de 2012 a 2024**. Os anos de 2011 e 2025 não são utilizados nesta comparação anual porque possuem cobertura parcial no conjunto de dados.
# MAGIC
# MAGIC Para cada ano, serão apresentados o **faturamento total**, a **variação absoluta em relação ao ano anterior** e a **variação percentual anual**. Dessa forma, a análise permite observar não apenas o valor faturado, mas também a direção e a magnitude das mudanças ocorridas ao longo do tempo.
# MAGIC
# MAGIC O primeiro ano completo, 2012, é utilizado como base inicial da série e, por isso, não possui variação em relação a um ano anterior comparável.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_anual AS (
# MAGIC     SELECT
# MAGIC         YEAR(data_competencia) AS ano,
# MAGIC         SUM(valor) AS faturamento
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     WHERE YEAR(data_competencia) BETWEEN 2012 AND 2024
# MAGIC     GROUP BY YEAR(data_competencia)
# MAGIC ),
# MAGIC
# MAGIC comparacao AS (
# MAGIC     SELECT
# MAGIC         ano,
# MAGIC         faturamento,
# MAGIC         LAG(faturamento) OVER (
# MAGIC             ORDER BY ano
# MAGIC         ) AS faturamento_ano_anterior
# MAGIC     FROM faturamento_anual
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano AS `Ano`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento,
# MAGIC         2
# MAGIC     ) AS `Faturamento`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento - faturamento_ano_anterior,
# MAGIC         2
# MAGIC     ) AS `Variação Absoluta`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         100.0 * (
# MAGIC             faturamento - faturamento_ano_anterior
# MAGIC         ) / faturamento_ano_anterior,
# MAGIC         2
# MAGIC     ) AS `Variação Anual (%)`
# MAGIC
# MAGIC FROM comparacao
# MAGIC
# MAGIC ORDER BY ano;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. Conclusão da Como o faturamento evoluiu ao longo do tempo?
# MAGIC
# MAGIC A análise dos anos completos de **2012 a 2024** mostra que o faturamento da empresa apresentou uma trajetória marcada por períodos de crescimento e retração, sem uma tendência contínua de expansão ao longo de todo o histórico.
# MAGIC
# MAGIC Entre **2012 e 2014**, houve crescimento consecutivo do faturamento, que passou de **R$ 10.142.555,29** para **R$ 13.723.958,33**. Entre **2015 e 2017**, ocorreram três reduções anuais consecutivas, sendo a mais expressiva em 2017, com queda de **15,65%** em relação ao ano anterior.
# MAGIC
# MAGIC Após crescimento de **3,64% em 2018**, o ano de **2019 apresentou a maior expansão da série**, com aumento de **44,49%** em relação a 2018 e faturamento de **R$ 16.228.170,72**, o maior valor entre os anos completos analisados.
# MAGIC
# MAGIC A partir de 2020, o comportamento voltou a oscilar. Houve redução de **12,56% em 2020**, crescimento de **5,68% em 2021** e novas quedas em 2022, 2023 e 2024. Em **2024**, o faturamento foi de **R$ 10.367.518,30**, com redução de **19,62% em relação a 2023**, a maior retração percentual anual da série analisada.
# MAGIC
# MAGIC Os resultados evidenciam que o faturamento histórico apresentou variações relevantes ao longo do tempo, permitindo aos Gerentes e à Diretoria identificar períodos de expansão e retração da receita e utilizar esse comportamento histórico como referência para as demais análises de faturamento.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.4. Qual é a concentração de faturamento nos cinco maiores clientes?
# MAGIC
# MAGIC **Objetivo:** avaliar o grau de concentração do faturamento da empresa nos cinco clientes de maior representatividade, fornecendo aos **Gerentes e à Diretoria** uma medida da dependência da receita em relação aos principais clientes.
# MAGIC
# MAGIC A análise considera todo o histórico disponível e classifica os clientes de acordo com o faturamento acumulado no período. Para os cinco maiores clientes, serão apresentados o **faturamento total**, a **participação individual no faturamento da empresa** e a **participação acumulada**, permitindo observar quanto da receita histórica está concentrada nesse grupo.
# MAGIC
# MAGIC Também será apresentada a participação conjunta dos cinco maiores clientes no faturamento total, possibilitando dimensionar a concentração da receita sem, nesta etapa, analisar sua evolução ao longo do tempo. Essa evolução será tratada separadamente na questão seguinte.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_cliente AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         SUM(valor) AS faturamento_cliente
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY cliente
# MAGIC ),
# MAGIC
# MAGIC total_empresa AS (
# MAGIC     SELECT
# MAGIC         SUM(faturamento_cliente) AS faturamento_total
# MAGIC     FROM faturamento_cliente
# MAGIC ),
# MAGIC
# MAGIC ranking AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         faturamento_cliente,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY faturamento_cliente DESC, cliente
# MAGIC         ) AS posicao
# MAGIC     FROM faturamento_cliente
# MAGIC ),
# MAGIC
# MAGIC top_5 AS (
# MAGIC     SELECT
# MAGIC         r.posicao,
# MAGIC         r.cliente,
# MAGIC         r.faturamento_cliente,
# MAGIC         t.faturamento_total,
# MAGIC
# MAGIC         100.0
# MAGIC         * r.faturamento_cliente
# MAGIC         / t.faturamento_total AS participacao_individual
# MAGIC
# MAGIC     FROM ranking r
# MAGIC     CROSS JOIN total_empresa t
# MAGIC
# MAGIC     WHERE r.posicao <= 5
# MAGIC ),
# MAGIC
# MAGIC resultado AS (
# MAGIC     SELECT
# MAGIC         posicao,
# MAGIC         cliente,
# MAGIC         faturamento_cliente,
# MAGIC         participacao_individual,
# MAGIC
# MAGIC         SUM(participacao_individual) OVER (
# MAGIC             ORDER BY posicao
# MAGIC             ROWS BETWEEN UNBOUNDED PRECEDING
# MAGIC                      AND CURRENT ROW
# MAGIC         ) AS participacao_acumulada,
# MAGIC
# MAGIC         SUM(faturamento_cliente) OVER () AS faturamento_top_5,
# MAGIC
# MAGIC         faturamento_total
# MAGIC
# MAGIC     FROM top_5
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     posicao AS `Posição`,
# MAGIC     cliente AS `Cliente`,
# MAGIC     ROUND(faturamento_cliente, 2) AS `Faturamento`,
# MAGIC     ROUND(participacao_individual, 2) AS `Participação Individual (%)`,
# MAGIC     ROUND(participacao_acumulada, 2) AS `Participação Acumulada (%)`,
# MAGIC     ROUND(faturamento_top_5, 2) AS `Faturamento dos 5 Maiores`,
# MAGIC     ROUND(
# MAGIC         100.0 * faturamento_top_5 / faturamento_total,
# MAGIC         2
# MAGIC     ) AS `Concentração dos 5 Maiores (%)`
# MAGIC
# MAGIC FROM resultado
# MAGIC
# MAGIC ORDER BY posicao;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.4. Conclusão da Qual é a concentração de faturamento nos cinco maiores clientes?
# MAGIC
# MAGIC A análise do histórico disponível mostra que os **cinco maiores clientes concentram 82,16% do faturamento total da empresa**, correspondendo a aproximadamente **R$ 139,27 milhões**.
# MAGIC
# MAGIC O cliente **BRAVIA** apresenta a maior participação individual, respondendo por **50,92%** do faturamento histórico. Com a inclusão de **LUMINA**, a participação acumulada dos dois maiores clientes alcança **67,19%**. Os três maiores — BRAVIA, LUMINA e FALCON — representam conjuntamente **73,51%** do faturamento.
# MAGIC
# MAGIC Com a inclusão de **GALENA** e **ORION**, a participação acumulada alcança **82,16%**, evidenciando uma elevada concentração histórica do faturamento em um grupo reduzido de clientes.
# MAGIC
# MAGIC Esse resultado permite aos Gerentes e à Diretoria dimensionar a representatividade dos principais clientes na receita da empresa. Entretanto, como a análise considera todo o histórico de forma consolidada, ela não permite concluir que o mesmo nível ou composição de concentração permaneceu constante ao longo do tempo.
# MAGIC
# MAGIC A evolução dessa participação será analisada na questão seguinte, permitindo verificar como a representatividade dos maiores clientes se modificou ao longo dos anos.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.5. Como a participação dos maiores clientes no faturamento total evoluiu ao longo do tempo?
# MAGIC
# MAGIC **Objetivo:** analisar como a participação dos cinco maiores clientes no faturamento da empresa se modificou ao longo do tempo, permitindo aos **Gerentes e à Diretoria** verificar se a concentração da receita nesse grupo aumentou, diminuiu ou apresentou oscilações ao longo dos anos.
# MAGIC
# MAGIC Para manter consistência com a análise anterior, são considerados como maiores clientes os **cinco clientes com maior faturamento acumulado em todo o histórico disponível**. A participação desse mesmo grupo é então calculada para cada ano completo entre **2012 e 2024**.
# MAGIC
# MAGIC Para cada ano, serão apresentados o **faturamento total da empresa**, o **faturamento dos cinco maiores clientes** e a **participação percentual desse grupo no faturamento anual**.
# MAGIC
# MAGIC A utilização de um grupo fixo de clientes ao longo de toda a série permite acompanhar a mudança de sua representatividade no faturamento sem alterar a composição do grupo a cada ano.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_cliente_historico AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         SUM(valor) AS faturamento_historico
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY cliente
# MAGIC ),
# MAGIC
# MAGIC ranking_clientes AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             ORDER BY faturamento_historico DESC, cliente
# MAGIC         ) AS posicao
# MAGIC     FROM faturamento_cliente_historico
# MAGIC ),
# MAGIC
# MAGIC top_5 AS (
# MAGIC     SELECT
# MAGIC         cliente
# MAGIC     FROM ranking_clientes
# MAGIC     WHERE posicao <= 5
# MAGIC ),
# MAGIC
# MAGIC faturamento_anual AS (
# MAGIC     SELECT
# MAGIC         YEAR(f.data_competencia) AS ano,
# MAGIC         SUM(f.valor) AS faturamento_total,
# MAGIC         SUM(
# MAGIC             CASE
# MAGIC                 WHEN t.cliente IS NOT NULL THEN f.valor
# MAGIC                 ELSE 0
# MAGIC             END
# MAGIC         ) AS faturamento_top_5
# MAGIC     FROM workspace.gold.fato_faturamento f
# MAGIC     LEFT JOIN top_5 t
# MAGIC         ON f.cliente = t.cliente
# MAGIC     WHERE YEAR(f.data_competencia) BETWEEN 2012 AND 2024
# MAGIC     GROUP BY YEAR(f.data_competencia)
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano AS `Ano`,
# MAGIC     ROUND(faturamento_total, 2) AS `Faturamento Total`,
# MAGIC     ROUND(faturamento_top_5, 2) AS `Faturamento dos 5 Maiores`,
# MAGIC     ROUND(
# MAGIC         100.0 * faturamento_top_5 / faturamento_total,
# MAGIC         2
# MAGIC     ) AS `Participação dos 5 Maiores (%)`
# MAGIC FROM faturamento_anual
# MAGIC ORDER BY ano;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.5. Conclusão da Como a participação dos maiores clientes no faturamento total evoluiu ao longo do tempo?
# MAGIC
# MAGIC A participação dos cinco maiores clientes históricos apresentou variações relevantes entre **2012 e 2024**, demonstrando que a concentração do faturamento nesse grupo não permaneceu constante ao longo do período.
# MAGIC
# MAGIC Entre **2012 e 2022**, os cinco maiores clientes representaram uma parcela elevada do faturamento anual, geralmente superior a 80%. A maior concentração ocorreu em **2018**, quando esse grupo respondeu por **95,65% do faturamento total**.
# MAGIC
# MAGIC A principal mudança ocorreu nos anos mais recentes. A participação dos cinco maiores clientes caiu de **83,04% em 2022 para 58,50% em 2023**, chegando a **51,44% em 2024**.
# MAGIC
# MAGIC Em valores absolutos, o faturamento desse grupo passou de aproximadamente **R$ 11,06 milhões em 2022** para **R$ 7,55 milhões em 2023** e **R$ 5,33 milhões em 2024**. No mesmo período, o faturamento total da empresa também apresentou redução, indicando que a queda do faturamento dos cinco maiores clientes históricos ocorreu de forma proporcionalmente mais intensa.
# MAGIC
# MAGIC A redução da participação desse grupo não deve ser interpretada isoladamente como aumento da diversificação da carteira, pois também pode estar associada à redução ou ao encerramento do faturamento de determinados clientes. A análise da evolução individual da participação dos clientes, realizada na questão seguinte, permitirá compreender melhor essa mudança na composição do faturamento.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.6. Quais clientes aumentaram ou reduziram sua participação no faturamento?
# MAGIC
# MAGIC **Objetivo:** identificar quais clientes ganharam ou perderam participação no faturamento da empresa entre os dois anos completos mais recentes, permitindo aos **Gerentes e à Diretoria** compreender as mudanças mais recentes na composição da receita.
# MAGIC
# MAGIC A análise compara **2023 e 2024**, os dois últimos anos completos disponíveis. Para cada cliente, será calculada sua participação percentual no faturamento total de cada ano e a respectiva **variação em pontos percentuais**.
# MAGIC
# MAGIC Uma variação positiva indica aumento da participação do cliente no faturamento total, enquanto uma variação negativa indica redução. Clientes sem faturamento em um dos anos são mantidos na análise, permitindo identificar também entradas ou saídas de participação entre os períodos.
# MAGIC
# MAGIC A análise representa uma comparação da composição do faturamento entre os dois anos e não determina, isoladamente, as causas comerciais ou econômicas das mudanças observadas.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_cliente_ano AS (
# MAGIC     SELECT
# MAGIC         YEAR(data_competencia) AS ano,
# MAGIC         cliente,
# MAGIC         SUM(valor) AS faturamento_cliente
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     WHERE YEAR(data_competencia) IN (2023, 2024)
# MAGIC     GROUP BY
# MAGIC         YEAR(data_competencia),
# MAGIC         cliente
# MAGIC ),
# MAGIC
# MAGIC faturamento_total_ano AS (
# MAGIC     SELECT
# MAGIC         ano,
# MAGIC         SUM(faturamento_cliente) AS faturamento_total
# MAGIC     FROM faturamento_cliente_ano
# MAGIC     GROUP BY ano
# MAGIC ),
# MAGIC
# MAGIC participacao AS (
# MAGIC     SELECT
# MAGIC         f.ano,
# MAGIC         f.cliente,
# MAGIC         f.faturamento_cliente,
# MAGIC         100.0 * f.faturamento_cliente / t.faturamento_total
# MAGIC             AS participacao
# MAGIC     FROM faturamento_cliente_ano f
# MAGIC     INNER JOIN faturamento_total_ano t
# MAGIC         ON f.ano = t.ano
# MAGIC ),
# MAGIC
# MAGIC clientes AS (
# MAGIC     SELECT DISTINCT cliente
# MAGIC     FROM participacao
# MAGIC ),
# MAGIC
# MAGIC comparacao AS (
# MAGIC     SELECT
# MAGIC         c.cliente,
# MAGIC
# MAGIC         COALESCE(p23.faturamento_cliente, 0)
# MAGIC             AS faturamento_2023,
# MAGIC
# MAGIC         COALESCE(p24.faturamento_cliente, 0)
# MAGIC             AS faturamento_2024,
# MAGIC
# MAGIC         COALESCE(p23.participacao, 0)
# MAGIC             AS participacao_2023,
# MAGIC
# MAGIC         COALESCE(p24.participacao, 0)
# MAGIC             AS participacao_2024
# MAGIC
# MAGIC     FROM clientes c
# MAGIC
# MAGIC     LEFT JOIN participacao p23
# MAGIC         ON c.cliente = p23.cliente
# MAGIC        AND p23.ano = 2023
# MAGIC
# MAGIC     LEFT JOIN participacao p24
# MAGIC         ON c.cliente = p24.cliente
# MAGIC        AND p24.ano = 2024
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     cliente AS `Cliente`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_2023,
# MAGIC         2
# MAGIC     ) AS `Faturamento 2023`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         participacao_2023,
# MAGIC         2
# MAGIC     ) AS `Participação 2023 (%)`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_2024,
# MAGIC         2
# MAGIC     ) AS `Faturamento 2024`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         participacao_2024,
# MAGIC         2
# MAGIC     ) AS `Participação 2024 (%)`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         participacao_2024 - participacao_2023,
# MAGIC         2
# MAGIC     ) AS `Variação da Participação (p.p.)`
# MAGIC
# MAGIC FROM comparacao
# MAGIC
# MAGIC ORDER BY
# MAGIC     participacao_2024 - participacao_2023 DESC,
# MAGIC     cliente;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.6. Conclusão da Quais clientes aumentaram ou reduziram sua participação no faturamento?
# MAGIC
# MAGIC A comparação entre **2023 e 2024** evidencia mudanças relevantes na composição do faturamento da empresa.
# MAGIC
# MAGIC O maior aumento de participação ocorreu com **PRISMA**, que não apresentou faturamento em 2023 e passou a representar **19,00% do faturamento total em 2024**, com R$ 1,97 milhão. **ACCORD** também passou a apresentar faturamento em 2024, alcançando participação de **3,29%**. Entre os clientes com faturamento nos dois anos, **LUMINA** aumentou sua participação de **4,45% para 5,61%**, crescimento de 1,16 ponto percentual.
# MAGIC
# MAGIC Entre as maiores reduções, **AURORA**, que representava **7,70% do faturamento em 2023**, não apresentou faturamento em 2024. **NEXORA** reduziu sua participação de **24,98% para 18,54%**, queda de 6,44 pontos percentuais, enquanto **FALCON** passou de **6,31% para 1,46%**, redução de 4,84 pontos percentuais.
# MAGIC
# MAGIC **BRAVIA** permaneceu com participação expressiva, porém apresentou redução de **47,74% para 44,36%**, correspondente a 3,38 pontos percentuais. Seu faturamento também diminuiu, de aproximadamente R$ 6,16 milhões em 2023 para R$ 4,60 milhões em 2024.
# MAGIC
# MAGIC Os resultados mostram que a composição do faturamento sofreu alterações relevantes entre os dois anos, com entrada de novos participantes de peso e redução da representatividade de alguns clientes anteriormente importantes. A análise identifica essas mudanças, mas os dados disponíveis não permitem determinar isoladamente suas causas comerciais ou econômicas.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.7. Qual o ticket médio das notas fiscais emitidas por mês?
# MAGIC
# MAGIC **Objetivo:** analisar o valor médio das notas fiscais emitidas em cada competência mensal, permitindo aos **Gerentes e à Diretoria** acompanhar como o valor médio faturado por nota se comportou ao longo do tempo.
# MAGIC
# MAGIC O ticket médio mensal é calculado pela divisão do **faturamento total da competência pela quantidade de notas fiscais emitidas no período**.
# MAGIC
# MAGIC Além do ticket médio, serão apresentados o faturamento mensal e a quantidade de notas fiscais, permitindo avaliar se alterações no valor médio estão associadas a mudanças no volume de notas emitidas, no valor faturado ou em ambos.
# MAGIC
# MAGIC A análise considera todas as competências disponíveis no histórico. Como o indicador é calculado individualmente para cada mês, os períodos parciais de 2011 e 2025 podem ser mantidos na série, respeitando-se a cobertura efetivamente existente em cada competência.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_mensal AS (
# MAGIC     SELECT
# MAGIC         DATE_TRUNC('MONTH', data_competencia) AS competencia,
# MAGIC         COUNT(*) AS quantidade_notas,
# MAGIC         SUM(valor) AS faturamento_mensal
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY DATE_TRUNC('MONTH', data_competencia)
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     DATE_FORMAT(competencia, 'MM/yyyy') AS `Competência`,
# MAGIC
# MAGIC     quantidade_notas AS `Quantidade de Notas`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_mensal,
# MAGIC         2
# MAGIC     ) AS `Faturamento Mensal`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_mensal / quantidade_notas,
# MAGIC         2
# MAGIC     ) AS `Ticket Médio`
# MAGIC
# MAGIC FROM faturamento_mensal
# MAGIC
# MAGIC ORDER BY competencia;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.7. Conclusão da Qual o ticket médio das notas fiscais emitidas por mês?
# MAGIC
# MAGIC A análise das **168 competências mensais** disponíveis mostra variações relevantes no valor médio das notas fiscais emitidas ao longo do histórico.
# MAGIC
# MAGIC O maior ticket médio mensal foi registrado em **janeiro de 2024**, com **R$ 101.997,60 por nota fiscal**. Nesse mês foram emitidas 12 notas, correspondentes a um faturamento de aproximadamente **R$ 1,22 milhão**. O menor ticket médio ocorreu em **setembro de 2015**, com **R$ 21.241,60 por nota**, quando foram emitidas 36 notas e faturados aproximadamente R$ 764,70 mil.
# MAGIC
# MAGIC A análise conjunta do ticket médio e da quantidade de notas também evidencia mudanças na composição do faturamento ao longo do tempo. Considerando anos completos, em **2015 foram emitidas 475 notas fiscais**, enquanto em **2024 foram emitidas 129**. No mesmo comparativo, o valor médio por nota passou de aproximadamente **R$ 28,38 mil para R$ 80,37 mil**.
# MAGIC
# MAGIC Dessa forma, a evolução do faturamento não está associada somente à quantidade de notas fiscais emitidas, mas também ao valor médio dessas notas. O indicador permite aos Gerentes e à Diretoria acompanhar alterações no perfil do faturamento, devendo ser interpretado em conjunto com o volume de notas e o faturamento do período.
# MAGIC
# MAGIC Os dados disponíveis permitem identificar essas mudanças, mas não permitem atribuir isoladamente suas causas a alterações contratuais, composição de clientes, projetos ou outros fatores comerciais.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.8. Qual o ticket médio das notas fiscais por cliente?
# MAGIC
# MAGIC **Objetivo:** analisar o valor médio das notas fiscais emitidas para cada cliente, permitindo aos **Gerentes e à Diretoria** comparar o perfil de faturamento dos diferentes clientes atendidos pela empresa.
# MAGIC
# MAGIC O ticket médio por cliente é calculado pela divisão do **faturamento total do cliente pela quantidade de notas fiscais emitidas para esse cliente** ao longo do histórico disponível.
# MAGIC
# MAGIC Além do ticket médio, serão apresentados a quantidade de notas fiscais e o faturamento total de cada cliente. Esses indicadores permitem distinguir clientes que acumulam maior faturamento em função de um número elevado de notas daqueles cujo faturamento está associado a notas de maior valor médio.
# MAGIC
# MAGIC Os resultados serão apresentados em ordem decrescente de ticket médio. O indicador representa o comportamento médio das notas fiscais de cada cliente em todo o período disponível e não deve ser interpretado isoladamente como medida de importância comercial ou rentabilidade.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_cliente AS (
# MAGIC     SELECT
# MAGIC         cliente,
# MAGIC         COUNT(*) AS quantidade_notas,
# MAGIC         SUM(valor) AS faturamento_total
# MAGIC     FROM workspace.gold.fato_faturamento
# MAGIC     GROUP BY cliente
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     cliente AS `Cliente`,
# MAGIC
# MAGIC     quantidade_notas AS `Quantidade de Notas`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_total,
# MAGIC         2
# MAGIC     ) AS `Faturamento Total`,
# MAGIC
# MAGIC     ROUND(
# MAGIC         faturamento_total / quantidade_notas,
# MAGIC         2
# MAGIC     ) AS `Ticket Médio`
# MAGIC
# MAGIC FROM faturamento_cliente
# MAGIC
# MAGIC ORDER BY
# MAGIC     `Ticket Médio` DESC,
# MAGIC     cliente;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.8. Conclusão da Qual o ticket médio das notas fiscais por cliente?
# MAGIC
# MAGIC A análise dos **35 clientes** evidencia diferenças relevantes tanto no valor médio das notas fiscais quanto na quantidade de notas emitidas ao longo do histórico.
# MAGIC
# MAGIC O maior ticket médio foi registrado para **PRISMA**, com **R$ 197.000,00 por nota fiscal**, considerando 10 notas. Em seguida aparecem **NEXORA**, com ticket médio de **R$ 175.545,20** em 37 notas, e **BELVIA**, com **R$ 133.533,93** em 23 notas.
# MAGIC
# MAGIC A comparação com os clientes de maior faturamento acumulado mostra que um faturamento elevado não está necessariamente associado aos maiores tickets médios. **BRAVIA**, maior cliente em faturamento histórico, apresentou **1.140 notas fiscais** e ticket médio de **R$ 75.720,49**. **LUMINA**, segundo maior faturamento acumulado, apresentou 864 notas e ticket médio de **R$ 31.915,50**.
# MAGIC
# MAGIC Outro exemplo é **ORION**, que integra o grupo dos cinco maiores clientes em faturamento histórico, mas apresentou **606 notas fiscais** e ticket médio de **R$ 12.047,50**. Nesse caso, a quantidade de notas emitidas possui papel relevante na formação do faturamento acumulado.
# MAGIC
# MAGIC Os resultados mostram que o ticket médio deve ser analisado conjuntamente com a quantidade de notas e o faturamento total. Clientes com poucas notas podem apresentar tickets médios elevados sem necessariamente possuir grande representatividade na receita total, enquanto clientes com tickets menores podem alcançar faturamentos relevantes por meio de maior recorrência de emissão.
# MAGIC
# MAGIC Essa análise permite aos Gerentes e à Diretoria compreender melhor os diferentes perfis de faturamento dos clientes, sem utilizar isoladamente o ticket médio como medida de importância comercial.