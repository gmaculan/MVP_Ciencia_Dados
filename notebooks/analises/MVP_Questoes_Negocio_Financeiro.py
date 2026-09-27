# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Questões de Negócio — Módulo Financeiro
# MAGIC
# MAGIC O módulo financeiro de uma empresa utiliza informações provenientes de diferentes áreas para realizar pagamentos, acompanhar recebimentos e fornecer informações para o planejamento e controle financeiro.
# MAGIC
# MAGIC No caso dos **custos relacionados aos funcionários**, existe uma interface importante entre o RH, os gestores responsáveis e o Financeiro. Informações como salário, benefícios, admissões, desligamentos e demais eventos que possam alterar os valores devidos aos funcionários são originadas ou administradas pelas áreas responsáveis por esses processos. O Financeiro utiliza as informações recebidas para efetuar os respectivos pagamentos.
# MAGIC
# MAGIC Assim, se determinado funcionário possui um valor normalmente utilizado para pagamento, mas algum evento provoca uma alteração em uma competência específica, essa alteração precisa ser informada ao Financeiro pela área responsável. Na ausência de uma atualização, o Financeiro trabalha com as informações de pagamento que lhe foram disponibilizadas.
# MAGIC
# MAGIC O **fluxo operacional de comunicação, aprovação e encaminhamento dessas alterações entre RH, gestores e Financeiro não faz parte do escopo deste MVP**. O projeto também não pretende desenvolver um sistema transacional de folha de pagamento ou reproduzir todos os processos administrativos envolvidos na execução dos pagamentos.
# MAGIC
# MAGIC As análises relacionadas à composição dos custos dos funcionários, incluindo salário, benefícios e encargos disponíveis na estrutura analítica, já foram tratadas no **Módulo de Recursos Humanos**. Por esse motivo, essas questões não serão repetidas no Módulo Financeiro apenas para reproduzir informações já obtidas. Para fins das análises financeiras, considera-se que os valores necessários aos pagamentos estejam disponíveis a partir dos processos responsáveis por sua geração e atualização.
# MAGIC
# MAGIC Da mesma forma, o Financeiro utiliza informações relacionadas aos **recebimentos e pagamentos da empresa** para elaborar instrumentos de gestão, como o fluxo de caixa e outros controles financeiros. A modelagem completa desses processos e artefatos não faz parte do escopo deste MVP. Entretanto, os dados disponíveis permitem demonstrar como informações de entradas e saídas podem ser consolidadas para fornecer uma visão do fluxo financeiro em determinado período.
# MAGIC
# MAGIC Além dessas atividades, a base disponível contém informações referentes a **fornecedores e prestadores de serviços PJ**. Como o MVP não possui um módulo específico destinado a fornecedores e PJs, as análises relacionadas aos seus custos serão apresentadas neste módulo, por sua relação direta com as despesas da empresa e com o acompanhamento financeiro e gerencial.
# MAGIC
# MAGIC A partir desse contexto, foram definidas as seguintes questões de negócio:
# MAGIC
# MAGIC 1. **Qual é o custo de um fornecedor por período?**  
# MAGIC    **Público:** Financeiro, gestores responsáveis e Diretoria, dependendo da natureza do fornecedor.  
# MAGIC    A análise busca permitir o acompanhamento dos valores associados a determinado fornecedor ao longo do período disponível, possibilitando avaliar a evolução dos gastos relacionados a esse fornecedor.
# MAGIC
# MAGIC 2. **Quais fornecedores representam os maiores custos para a empresa?**  
# MAGIC    **Público:** Financeiro, gestores responsáveis e Diretoria.  
# MAGIC    A análise busca identificar os fornecedores com maior participação nos custos registrados, permitindo avaliar a concentração das despesas e os fornecedores que possuem maior impacto financeiro para a empresa.
# MAGIC
# MAGIC 3. **Qual é o fluxo financeiro em determinado período?**  
# MAGIC    **Público:** Financeiro e Diretoria.  
# MAGIC    A análise busca consolidar, em uma mesma visão, as **entradas previstas por faturamento**, as **saídas previstas a partir das obrigações de pagamento disponíveis na estrutura analítica** e o **saldo previsto resultante** no período selecionado. Esses elementos serão tratados conjuntamente, pois constituem componentes da mesma questão de negócio e podem servir de apoio à elaboração e análise do fluxo de caixa.
# MAGIC
# MAGIC As análises deste módulo possuem finalidade **analítica e demonstrativa**. Elas não pretendem reproduzir todos os processos executados pelo Financeiro, nem substituir sistemas transacionais de contas a pagar, contas a receber, folha de pagamento ou tesouraria.
# MAGIC
# MAGIC As questões serão analisadas individualmente nas seções seguintes. Para cada análise será apresentada uma breve contextualização da questão, a consulta utilizada, o resultado obtido e sua interpretação, sempre considerando as premissas e limitações dos dados disponíveis no MVP.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.1 Qual é o custo de um fornecedor por período?
# MAGIC
# MAGIC O acompanhamento dos gastos com fornecedores permite ao Financeiro e aos gestores responsáveis avaliar os valores associados a determinado fornecedor ao longo do tempo, apoiando o controle das despesas e a análise de sua evolução.
# MAGIC
# MAGIC A consulta considera um **fornecedor e um intervalo de competências**, apresentando os valores registrados em cada competência e o custo total correspondente ao período selecionado.
# MAGIC
# MAGIC Em uma aplicação operacional, o fornecedor e o período poderiam ser selecionados pelo usuário por meio de uma interface. Neste MVP, esses parâmetros serão definidos diretamente na consulta SQL para demonstrar a funcionalidade.
# MAGIC
# MAGIC A base de fornecedores disponível possui caráter amostral. Portanto, os valores obtidos representam os registros disponíveis no MVP e não devem ser interpretados como a totalidade das despesas históricas da empresa com fornecedores.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH parametros AS (
# MAGIC     SELECT
# MAGIC         'CONEXÃO BRASIL TELECOM S/A' AS fornecedor_selecionado,
# MAGIC         DATE '2024-01-01' AS data_inicial,
# MAGIC         DATE '2024-12-31' AS data_final
# MAGIC ),
# MAGIC
# MAGIC gastos_fornecedor AS (
# MAGIC     SELECT
# MAGIC         f.fornecedor,
# MAGIC         f.competencia,
# MAGIC         SUM(f.valor_nf_fornecedor) AS valor_competencia
# MAGIC
# MAGIC     FROM workspace.silver.fornecedor_anonimizado f
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE f.fornecedor = p.fornecedor_selecionado
# MAGIC       AND f.competencia BETWEEN p.data_inicial AND p.data_final
# MAGIC
# MAGIC     GROUP BY
# MAGIC         f.fornecedor,
# MAGIC         f.competencia
# MAGIC ),
# MAGIC
# MAGIC total_periodo AS (
# MAGIC     SELECT
# MAGIC         SUM(valor_competencia) AS valor_total_periodo
# MAGIC     FROM gastos_fornecedor
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     p.data_inicial AS periodo_consultado_inicio,
# MAGIC     p.data_final AS periodo_consultado_fim,
# MAGIC     g.fornecedor,
# MAGIC     g.competencia,
# MAGIC     ROUND(g.valor_competencia, 2) AS valor_competencia,
# MAGIC     ROUND(t.valor_total_periodo, 2) AS valor_total_periodo
# MAGIC
# MAGIC FROM parametros p
# MAGIC
# MAGIC LEFT JOIN gastos_fornecedor g
# MAGIC     ON 1 = 1
# MAGIC
# MAGIC CROSS JOIN total_periodo t
# MAGIC
# MAGIC ORDER BY g.competencia;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.1. Conclusão da Qual é o custo de um fornecedor por período?
# MAGIC
# MAGIC Para demonstrar a consulta, foi selecionado o fornecedor **CONEXÃO BRASIL TELECOM S/A** e utilizado o período de **01/01/2024 a 31/12/2024**.
# MAGIC
# MAGIC No período analisado, foram identificados registros nas **12 competências de 2024**, totalizando **R$ 227.733,23** em gastos com esse fornecedor.
# MAGIC
# MAGIC Entre fevereiro e dezembro, os valores mensais apresentam comportamento relativamente estável, situando-se aproximadamente entre **R$ 20 mil e R$ 21 mil por competência**. Em janeiro foi registrado o valor de **R$ 529,39**, significativamente inferior aos valores observados nos demais meses.
# MAGIC
# MAGIC Os dados disponíveis não permitem determinar a causa dessa diferença em janeiro. Em uma situação operacional, uma variação dessa magnitude poderia ser utilizada pelo Financeiro ou pelo gestor responsável como ponto de partida para verificar os registros e compreender o evento que originou o valor.
# MAGIC
# MAGIC A consulta demonstra que a estrutura disponível permite selecionar um fornecedor e um período de interesse, acompanhar os valores registrados em cada competência e obter o custo total correspondente ao intervalo analisado.
# MAGIC
# MAGIC Em uma aplicação operacional, o fornecedor e o período poderiam ser selecionados pelo usuário por meio de uma interface, permitindo aplicar a mesma análise aos demais fornecedores cadastrados.
# MAGIC
# MAGIC Os resultados devem ser interpretados considerando que a base de fornecedores utilizada no MVP possui caráter amostral e, portanto, representa os registros disponíveis para a análise, não necessariamente a totalidade das despesas históricas da empresa com fornecedores.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 Quais fornecedores representam os maiores custos para a empresa?
# MAGIC
# MAGIC Identificar os fornecedores que representam os maiores custos permite ao **Financeiro**, aos **gestores responsáveis** e à **Diretoria** compreender como as despesas registradas estão distribuídas entre os diferentes fornecedores e identificar aqueles com maior participação nos gastos da empresa.
# MAGIC
# MAGIC Para permitir uma comparação consistente, os fornecedores serão analisados dentro de um **mesmo período de referência**. Nesta demonstração será utilizado o intervalo de **01/01/2024 a 31/12/2024**, evitando comparar diretamente fornecedores que possuam registros referentes a períodos históricos diferentes.
# MAGIC
# MAGIC A análise apresentará o valor total registrado para cada fornecedor no período e sua participação percentual no total das despesas com fornecedores. Dessa forma, será possível identificar tanto os maiores valores absolutos quanto o grau de concentração desses gastos.
# MAGIC
# MAGIC Em uma aplicação operacional, o período poderia ser selecionado pelo usuário por meio de uma interface. Neste MVP, o intervalo será definido diretamente na consulta SQL para demonstrar a funcionalidade.
# MAGIC
# MAGIC Os resultados devem ser interpretados considerando o caráter amostral da base de fornecedores disponível no MVP. Portanto, a análise representa a distribuição dos gastos existentes nos registros disponíveis para o período selecionado, e não necessariamente a totalidade das despesas da empresa com fornecedores.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH parametros AS (
# MAGIC     SELECT
# MAGIC         DATE '2024-01-01' AS data_inicial,
# MAGIC         DATE '2024-12-31' AS data_final
# MAGIC ),
# MAGIC
# MAGIC custos_fornecedores AS (
# MAGIC     SELECT
# MAGIC         f.fornecedor,
# MAGIC         SUM(f.valor_nf_fornecedor) AS custo_fornecedor
# MAGIC
# MAGIC     FROM workspace.silver.fornecedor_anonimizado f
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE f.competencia BETWEEN p.data_inicial AND p.data_final
# MAGIC
# MAGIC     GROUP BY
# MAGIC         f.fornecedor
# MAGIC ),
# MAGIC
# MAGIC total_periodo AS (
# MAGIC     SELECT
# MAGIC         SUM(custo_fornecedor) AS custo_total_fornecedores
# MAGIC     FROM custos_fornecedores
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     p.data_inicial AS periodo_consultado_inicio,
# MAGIC     p.data_final AS periodo_consultado_fim,
# MAGIC
# MAGIC     c.fornecedor,
# MAGIC
# MAGIC     ROUND(
# MAGIC         c.custo_fornecedor,
# MAGIC         2
# MAGIC     ) AS custo_fornecedor,
# MAGIC
# MAGIC     ROUND(
# MAGIC         c.custo_fornecedor
# MAGIC         / NULLIF(t.custo_total_fornecedores, 0)
# MAGIC         * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_custo_total,
# MAGIC
# MAGIC     ROUND(
# MAGIC         SUM(c.custo_fornecedor) OVER (
# MAGIC             ORDER BY c.custo_fornecedor DESC
# MAGIC             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
# MAGIC         )
# MAGIC         / NULLIF(t.custo_total_fornecedores, 0)
# MAGIC         * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_acumulado
# MAGIC
# MAGIC FROM custos_fornecedores c
# MAGIC
# MAGIC CROSS JOIN total_periodo t
# MAGIC CROSS JOIN parametros p
# MAGIC
# MAGIC ORDER BY
# MAGIC     c.custo_fornecedor DESC,
# MAGIC     c.fornecedor;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2. Conclusão da Quais fornecedores representam os maiores custos para a empresa?
# MAGIC
# MAGIC Para permitir uma comparação entre os fornecedores em um mesmo intervalo de referência, a análise considerou o período de **01/01/2024 a 31/12/2024**.
# MAGIC
# MAGIC Foram identificados **34 fornecedores** com registros no período, que representam conjuntamente **R$ 2.163.780,61** em gastos na base analisada.
# MAGIC
# MAGIC O fornecedor com maior custo foi **CONEXÃO BRASIL TELECOM S/A**, com **R$ 227.733,23**, correspondente a **10,52%** do total registrado. Em seguida aparecem **SOFTNOVA BRASIL SOFTWARE LTDA**, com **R$ 164.684,03 (7,61%)**, e **NUVEMAX TECNOLOGIA S/A**, com **R$ 160.947,78 (7,44%)**.
# MAGIC
# MAGIC A análise do percentual acumulado permite avaliar também a concentração dos gastos. Os **três fornecedores de maior custo representam conjuntamente 25,57%** das despesas registradas, enquanto os **cinco primeiros representam 39,22%** e os **dez primeiros concentram 67,95%** do total.
# MAGIC
# MAGIC Os resultados mostram, portanto, que existe concentração dos gastos nos fornecedores de maior custo, embora nenhum fornecedor isoladamente represente uma parcela predominante das despesas registradas no período. Essa informação pode apoiar o Financeiro, os gestores responsáveis e a Diretoria na identificação dos fornecedores com maior impacto financeiro e no direcionamento de análises mais detalhadas sobre essas despesas.
# MAGIC
# MAGIC A consulta também demonstra que a análise não precisa se limitar a uma classificação dos fornecedores pelo valor absoluto: a participação percentual e o percentual acumulado permitem avaliar quanto os principais fornecedores representam conjuntamente no total das despesas.
# MAGIC
# MAGIC Os resultados devem ser interpretados considerando o caráter amostral da base utilizada no MVP. Portanto, os valores representam os registros disponíveis para 2024 e não necessariamente a totalidade das despesas da empresa com fornecedores.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.3 Qual é o fluxo financeiro em determinado período?
# MAGIC
# MAGIC O acompanhamento do fluxo financeiro permite ao **Financeiro** e à **Diretoria** visualizar, ao longo do tempo, as entradas e saídas financeiras previstas a partir das informações disponíveis nas bases da empresa.
# MAGIC
# MAGIC Nesta análise, o fluxo será construído a partir dos movimentos financeiros que podem ser identificados ou estimados com os dados disponíveis no MVP. O objetivo não é reproduzir integralmente um extrato bancário ou um sistema financeiro transacional, mas organizar cronologicamente as entradas e obrigações de pagamento modeladas no projeto.
# MAGIC
# MAGIC Serão consideradas como **entradas** as receitas provenientes do faturamento. Para fins desta análise, a data de emissão da nota fiscal será utilizada como data do movimento financeiro da receita.
# MAGIC
# MAGIC Como **saídas**, serão considerados:
# MAGIC
# MAGIC - salários e benefícios de ticket refeição e ticket alimentação;
# MAGIC - plano de saúde dos titulares e dependentes;
# MAGIC - FGTS;
# MAGIC - férias;
# MAGIC - 13º salário;
# MAGIC - pagamentos a fornecedores.
# MAGIC
# MAGIC Para transformar os custos disponíveis nas bases em movimentos financeiros, serão adotadas as seguintes premissas:
# MAGIC
# MAGIC - salário, ticket refeição e ticket alimentação referentes à competência de determinado mês serão pagos no **5º dia útil do mês seguinte**, considerando como dias úteis apenas segunda a sexta-feira, sem tratamento de feriados;
# MAGIC - o plano de saúde dos titulares e dos respectivos dependentes será pago conjuntamente no **dia 24 da própria competência**;
# MAGIC - o FGTS será pago no **dia 21 da própria competência**;
# MAGIC - as férias serão pagas **dois dias antes do início do período de gozo**, sendo o valor calculado como **salário + 1/3 do salário**;
# MAGIC - a provisão mensal do 13º salário não será tratada como saída financeira. O pagamento será representado em duas parcelas: **30 de novembro** e **20 de dezembro**;
# MAGIC - para os fornecedores, como a fonte não possui data de vencimento, será utilizada uma regra demonstrativa baseada no custo total do fornecedor em cada competência:
# MAGIC   - até R$ 2.000,00: dia 8;
# MAGIC   - de R$ 2.000,01 a R$ 8.000,00: dia 12;
# MAGIC   - de R$ 8.000,01 a R$ 15.000,00: dia 15;
# MAGIC   - de R$ 15.000,01 a R$ 25.000,00: dia 20;
# MAGIC   - de R$ 25.000,01 a R$ 55.000,00: dia 23;
# MAGIC   - acima de R$ 55.000,00: dia 25.
# MAGIC
# MAGIC A coluna **Receber** representará as entradas, enquanto **Pagar** representará as saídas. O campo **Total** será calculado como `Receber - Pagar`, e o **Saldo** corresponderá ao acumulado cronológico desses movimentos, partindo de saldo inicial igual a zero.
# MAGIC
# MAGIC Como as bases não contêm saldo bancário inicial nem todos os compromissos financeiros da empresa, o resultado deve ser interpretado como um **fluxo financeiro demonstrativo construído com os dados disponíveis no MVP**, e não como a reprodução integral do fluxo de caixa histórico da empresa.
# MAGIC
# MAGIC Para demonstrar a análise, será utilizado o período de **01/01/2024 a 31/12/2024**.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH parametros AS (
# MAGIC     SELECT
# MAGIC         DATE '2024-01-01' AS data_inicial,
# MAGIC         DATE '2024-12-31' AS data_final
# MAGIC ),
# MAGIC
# MAGIC competencias AS (
# MAGIC     SELECT EXPLODE(
# MAGIC         SEQUENCE(
# MAGIC             ADD_MONTHS(DATE_TRUNC('MONTH', data_inicial), -1),
# MAGIC             DATE_TRUNC('MONTH', data_final),
# MAGIC             INTERVAL 1 MONTH
# MAGIC         )
# MAGIC     ) AS competencia
# MAGIC     FROM parametros
# MAGIC ),
# MAGIC
# MAGIC empregados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC     LEFT JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    BASE MENSAL DE PESSOAL
# MAGIC    ========================================================= */
# MAGIC
# MAGIC base_mensal AS (
# MAGIC     SELECT
# MAGIC         c.competencia,
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         cp.salario AS salario_mensal,
# MAGIC         cp.tr,
# MAGIC         cp.ta,
# MAGIC         cp.plano_saude_titular,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             e.data_admissao,
# MAGIC             c.competencia
# MAGIC         ) AS inicio_atividade_mes,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(e.data_desligamento, LAST_DAY(c.competencia)),
# MAGIC             LAST_DAY(c.competencia)
# MAGIC         ) AS fim_atividade_mes
# MAGIC
# MAGIC     FROM competencias c
# MAGIC
# MAGIC     INNER JOIN empregados e
# MAGIC         ON e.data_admissao <= LAST_DAY(c.competencia)
# MAGIC        AND (
# MAGIC             e.data_desligamento IS NULL
# MAGIC             OR e.data_desligamento >= c.competencia
# MAGIC        )
# MAGIC
# MAGIC     INNER JOIN workspace.gold.fato_custo_pessoal cp
# MAGIC         ON cp.drt = e.drt
# MAGIC        AND cp.ano = YEAR(c.competencia)
# MAGIC ),
# MAGIC
# MAGIC dias_mensais AS (
# MAGIC     SELECT
# MAGIC         b.*,
# MAGIC
# MAGIC         LEAST(
# MAGIC             30,
# MAGIC             DATEDIFF(
# MAGIC                 b.fim_atividade_mes,
# MAGIC                 b.inicio_atividade_mes
# MAGIC             ) + 1
# MAGIC         ) AS dias_trabalhados,
# MAGIC
# MAGIC         COUNT(
# MAGIC             CASE
# MAGIC                 WHEN DAYOFWEEK(t.data) BETWEEN 2 AND 6
# MAGIC                 THEN 1
# MAGIC             END
# MAGIC         ) AS dias_uteis_trabalhados
# MAGIC
# MAGIC     FROM base_mensal b
# MAGIC
# MAGIC     LEFT JOIN workspace.gold.dim_tempo t
# MAGIC         ON t.data BETWEEN b.inicio_atividade_mes
# MAGIC                       AND b.fim_atividade_mes
# MAGIC
# MAGIC     GROUP BY
# MAGIC         b.competencia,
# MAGIC         b.drt,
# MAGIC         b.nome,
# MAGIC         b.data_admissao,
# MAGIC         b.data_desligamento,
# MAGIC         b.salario_mensal,
# MAGIC         b.tr,
# MAGIC         b.ta,
# MAGIC         b.plano_saude_titular,
# MAGIC         b.inicio_atividade_mes,
# MAGIC         b.fim_atividade_mes
# MAGIC ),
# MAGIC
# MAGIC custos_mensais AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_mensal * dias_trabalhados / 30.0,
# MAGIC             2
# MAGIC         ) AS salario_periodo,
# MAGIC
# MAGIC         ROUND(
# MAGIC             COALESCE(tr, 0) / 21.0
# MAGIC             * LEAST(dias_uteis_trabalhados, 21),
# MAGIC             2
# MAGIC         ) AS tr_periodo,
# MAGIC
# MAGIC         ROUND(
# MAGIC             COALESCE(ta, 0) / 21.0
# MAGIC             * LEAST(dias_uteis_trabalhados, 21),
# MAGIC             2
# MAGIC         ) AS ta_periodo,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN dias_trabalhados >= 15 THEN 1
# MAGIC             ELSE 0
# MAGIC         END AS avo_13_mes
# MAGIC
# MAGIC     FROM dias_mensais
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    FGTS MENSAL — SOMENTE SOBRE SALÁRIO
# MAGIC    ========================================================= */
# MAGIC
# MAGIC custos_com_fgts AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             0.08 * salario_periodo,
# MAGIC             2
# MAGIC         ) AS fgts_competencia
# MAGIC
# MAGIC     FROM custos_mensais
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    5º DIA ÚTIL DO MÊS SEGUINTE
# MAGIC    ========================================================= */
# MAGIC
# MAGIC quinto_dia_util AS (
# MAGIC     SELECT
# MAGIC         competencia,
# MAGIC         MAX(data) AS data_pagamento
# MAGIC
# MAGIC     FROM (
# MAGIC         SELECT
# MAGIC             c.competencia,
# MAGIC             t.data,
# MAGIC
# MAGIC             ROW_NUMBER() OVER (
# MAGIC                 PARTITION BY c.competencia
# MAGIC                 ORDER BY t.data
# MAGIC             ) AS ordem_dia_util
# MAGIC
# MAGIC         FROM competencias c
# MAGIC
# MAGIC         INNER JOIN workspace.gold.dim_tempo t
# MAGIC             ON t.data BETWEEN ADD_MONTHS(c.competencia, 1)
# MAGIC                           AND LAST_DAY(ADD_MONTHS(c.competencia, 1))
# MAGIC            AND DAYOFWEEK(t.data) BETWEEN 2 AND 6
# MAGIC     ) x
# MAGIC
# MAGIC     WHERE ordem_dia_util = 5
# MAGIC
# MAGIC     GROUP BY competencia
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    RECEITA
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_receita AS (
# MAGIC     SELECT
# MAGIC         f.data_emissao AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'NF ',
# MAGIC             CAST(f.nf AS STRING)
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         f.cliente AS entidade,
# MAGIC
# MAGIC         'Faturamento' AS descricao,
# MAGIC
# MAGIC         f.data_emissao AS emissao,
# MAGIC
# MAGIC         CAST(f.valor AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS pagar
# MAGIC
# MAGIC     FROM workspace.gold.fato_faturamento f
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE f.data_emissao
# MAGIC           BETWEEN p.data_inicial AND p.data_final
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    SALÁRIO + TR + TA
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_folha AS (
# MAGIC     SELECT
# MAGIC         q.data_pagamento AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'FOLHA-',
# MAGIC             CAST(c.drt AS STRING),
# MAGIC             '-',
# MAGIC             DATE_FORMAT(c.competencia, 'yyyyMM')
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         c.nome AS entidade,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'Salário + TR + TA - competência ',
# MAGIC             DATE_FORMAT(c.competencia, 'MM/yyyy')
# MAGIC         ) AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             ROUND(
# MAGIC                 c.salario_periodo
# MAGIC                 + c.tr_periodo
# MAGIC                 + c.ta_periodo,
# MAGIC                 2
# MAGIC             )
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM custos_com_fgts c
# MAGIC
# MAGIC     INNER JOIN quinto_dia_util q
# MAGIC         ON c.competencia = q.competencia
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE q.data_pagamento
# MAGIC           BETWEEN p.data_inicial AND p.data_final
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    PLANO DE SAÚDE DOS DEPENDENTES
# MAGIC    ========================================================= */
# MAGIC
# MAGIC saude_dependentes AS (
# MAGIC     SELECT
# MAGIC         c.competencia,
# MAGIC         d.drt,
# MAGIC
# MAGIC         ROUND(
# MAGIC             SUM(d.custo_plano_saude),
# MAGIC             2
# MAGIC         ) AS custo_dependentes
# MAGIC
# MAGIC     FROM competencias c
# MAGIC
# MAGIC     INNER JOIN workspace.gold.fato_dependentes d
# MAGIC         ON d.ano = YEAR(c.competencia)
# MAGIC
# MAGIC     INNER JOIN empregados e
# MAGIC         ON e.drt = d.drt
# MAGIC        AND e.data_admissao <= LAST_DAY(c.competencia)
# MAGIC        AND (
# MAGIC             e.data_desligamento IS NULL
# MAGIC             OR e.data_desligamento >= c.competencia
# MAGIC        )
# MAGIC
# MAGIC     GROUP BY
# MAGIC         c.competencia,
# MAGIC         d.drt
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    PLANO DE SAÚDE TITULAR + DEPENDENTES — DIA 24
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_saude AS (
# MAGIC     SELECT
# MAGIC         MAKE_DATE(
# MAGIC             YEAR(c.competencia),
# MAGIC             MONTH(c.competencia),
# MAGIC             24
# MAGIC         ) AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'SAUDE-',
# MAGIC             CAST(c.drt AS STRING),
# MAGIC             '-',
# MAGIC             DATE_FORMAT(c.competencia, 'yyyyMM')
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         c.nome AS entidade,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'Plano de saúde titular + dependentes - competência ',
# MAGIC             DATE_FORMAT(c.competencia, 'MM/yyyy')
# MAGIC         ) AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             ROUND(
# MAGIC                 COALESCE(c.plano_saude_titular, 0)
# MAGIC                 + COALESCE(d.custo_dependentes, 0),
# MAGIC                 2
# MAGIC             )
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM custos_com_fgts c
# MAGIC
# MAGIC     LEFT JOIN saude_dependentes d
# MAGIC         ON d.drt = c.drt
# MAGIC        AND d.competencia = c.competencia
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE MAKE_DATE(
# MAGIC               YEAR(c.competencia),
# MAGIC               MONTH(c.competencia),
# MAGIC               24
# MAGIC           )
# MAGIC           BETWEEN p.data_inicial AND p.data_final
# MAGIC
# MAGIC       AND (
# MAGIC           COALESCE(c.plano_saude_titular, 0)
# MAGIC           + COALESCE(d.custo_dependentes, 0)
# MAGIC       ) > 0
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    FGTS MENSAL — DIA 21
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_fgts AS (
# MAGIC     SELECT
# MAGIC         MAKE_DATE(
# MAGIC             YEAR(c.competencia),
# MAGIC             MONTH(c.competencia),
# MAGIC             21
# MAGIC         ) AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'FGTS-',
# MAGIC             CAST(c.drt AS STRING),
# MAGIC             '-',
# MAGIC             DATE_FORMAT(c.competencia, 'yyyyMM')
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         c.nome AS entidade,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'FGTS sobre salário - competência ',
# MAGIC             DATE_FORMAT(c.competencia, 'MM/yyyy')
# MAGIC         ) AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             c.fgts_competencia
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM custos_com_fgts c
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE MAKE_DATE(
# MAGIC               YEAR(c.competencia),
# MAGIC               MONTH(c.competencia),
# MAGIC               21
# MAGIC           )
# MAGIC           BETWEEN p.data_inicial AND p.data_final
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    FÉRIAS
# MAGIC    ========================================================= */
# MAGIC
# MAGIC salario_ferias AS (
# MAGIC     SELECT
# MAGIC         f.drt,
# MAGIC         f.sequencial_ferias,
# MAGIC         f.data_inicio_gozo,
# MAGIC         e.nome,
# MAGIC         s.salario,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY
# MAGIC                 f.drt,
# MAGIC                 f.sequencial_ferias,
# MAGIC                 f.data_inicio_gozo
# MAGIC             ORDER BY s.data_alteracao DESC
# MAGIC         ) AS ordem_salario
# MAGIC
# MAGIC     FROM workspace.gold.fato_ferias f
# MAGIC
# MAGIC     INNER JOIN empregados e
# MAGIC         ON e.drt = f.drt
# MAGIC
# MAGIC     LEFT JOIN workspace.silver.salario_anonimizado s
# MAGIC         ON s.drt = f.drt
# MAGIC        AND s.data_alteracao <= f.data_inicio_gozo
# MAGIC
# MAGIC     WHERE f.data_inicio_gozo IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC mov_ferias AS (
# MAGIC     SELECT
# MAGIC         DATE_SUB(
# MAGIC             s.data_inicio_gozo,
# MAGIC             2
# MAGIC         ) AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'FERIAS-',
# MAGIC             CAST(s.drt AS STRING),
# MAGIC             '-',
# MAGIC             CAST(s.sequencial_ferias AS STRING)
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         s.nome AS entidade,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'Férias - início ',
# MAGIC             DATE_FORMAT(
# MAGIC                 s.data_inicio_gozo,
# MAGIC                 'dd/MM/yyyy'
# MAGIC             )
# MAGIC         ) AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             ROUND(
# MAGIC                 s.salario
# MAGIC                 + s.salario / 3.0,
# MAGIC                 2
# MAGIC             )
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM salario_ferias s
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE s.ordem_salario = 1
# MAGIC
# MAGIC       AND DATE_SUB(
# MAGIC               s.data_inicio_gozo,
# MAGIC               2
# MAGIC           )
# MAGIC           BETWEEN p.data_inicial AND p.data_final
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    13º — AVOS ADQUIRIDOS EM 2024
# MAGIC    ========================================================= */
# MAGIC
# MAGIC base_13_anual AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC
# MAGIC         SUM(avo_13_mes) AS avos_13_ano,
# MAGIC
# MAGIC         MAX_BY(
# MAGIC             salario_mensal,
# MAGIC             competencia
# MAGIC         ) AS salario_referencia
# MAGIC
# MAGIC     FROM custos_mensais
# MAGIC
# MAGIC     WHERE YEAR(competencia) = 2024
# MAGIC
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome
# MAGIC ),
# MAGIC
# MAGIC calculo_13 AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         avos_13_ano,
# MAGIC         salario_referencia,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_referencia
# MAGIC             * avos_13_ano / 12.0,
# MAGIC             2
# MAGIC         ) AS valor_13_total
# MAGIC
# MAGIC     FROM base_13_anual
# MAGIC
# MAGIC     WHERE avos_13_ano > 0
# MAGIC ),
# MAGIC
# MAGIC parcelas_13 AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC
# MAGIC         ROUND(
# MAGIC             valor_13_total / 2.0,
# MAGIC             2
# MAGIC         ) AS primeira_parcela,
# MAGIC
# MAGIC         ROUND(
# MAGIC             valor_13_total
# MAGIC             - ROUND(valor_13_total / 2.0, 2),
# MAGIC             2
# MAGIC         ) AS segunda_parcela
# MAGIC
# MAGIC     FROM calculo_13
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    PAGAMENTO DO 13º + FGTS DO 13º
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_13 AS (
# MAGIC     SELECT
# MAGIC         DATE '2024-11-30' AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             '13-1-',
# MAGIC             CAST(drt AS STRING),
# MAGIC             '-2024'
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         nome AS entidade,
# MAGIC
# MAGIC         '13º salário - 1ª parcela + FGTS' AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             ROUND(
# MAGIC                 primeira_parcela
# MAGIC                 + primeira_parcela * 0.08,
# MAGIC                 2
# MAGIC             )
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM parcelas_13
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT
# MAGIC         DATE '2024-12-20' AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             '13-2-',
# MAGIC             CAST(drt AS STRING),
# MAGIC             '-2024'
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         nome AS entidade,
# MAGIC
# MAGIC         '13º salário - 2ª parcela + FGTS' AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             ROUND(
# MAGIC                 segunda_parcela
# MAGIC                 + segunda_parcela * 0.08,
# MAGIC                 2
# MAGIC             )
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM parcelas_13
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    FORNECEDORES
# MAGIC    ========================================================= */
# MAGIC
# MAGIC mov_fornecedores AS (
# MAGIC     SELECT
# MAGIC         MAKE_DATE(
# MAGIC             YEAR(f.competencia),
# MAGIC             MONTH(f.competencia),
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN f.valor_fornecedor <= 2000 THEN 8
# MAGIC                 WHEN f.valor_fornecedor <= 8000 THEN 12
# MAGIC                 WHEN f.valor_fornecedor <= 15000 THEN 15
# MAGIC                 WHEN f.valor_fornecedor <= 25000 THEN 20
# MAGIC                 WHEN f.valor_fornecedor <= 55000 THEN 23
# MAGIC                 ELSE 25
# MAGIC             END
# MAGIC         ) AS data_vencimento,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'FORN-',
# MAGIC             CAST(f.id_entidade AS STRING),
# MAGIC             '-',
# MAGIC             DATE_FORMAT(f.competencia, 'yyyyMM')
# MAGIC         ) AS codigo,
# MAGIC
# MAGIC         e.nome_entidade AS entidade,
# MAGIC
# MAGIC         CONCAT(
# MAGIC             'Fornecedor - competência ',
# MAGIC             DATE_FORMAT(f.competencia, 'MM/yyyy')
# MAGIC         ) AS descricao,
# MAGIC
# MAGIC         CAST(NULL AS DATE) AS emissao,
# MAGIC
# MAGIC         CAST(0 AS DECIMAL(18,2)) AS receber,
# MAGIC
# MAGIC         CAST(
# MAGIC             f.valor_fornecedor
# MAGIC             AS DECIMAL(18,2)
# MAGIC         ) AS pagar
# MAGIC
# MAGIC     FROM workspace.gold.fato_fornecedor f
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_entidade e
# MAGIC         ON e.id_entidade = f.id_entidade
# MAGIC        AND e.natureza_entidade = 'D'
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE f.competencia
# MAGIC           BETWEEN DATE_TRUNC('MONTH', p.data_inicial)
# MAGIC               AND DATE_TRUNC('MONTH', p.data_final)
# MAGIC ),
# MAGIC
# MAGIC /* =========================================================
# MAGIC    CONSOLIDAÇÃO DOS MOVIMENTOS
# MAGIC    ========================================================= */
# MAGIC
# MAGIC movimentos AS (
# MAGIC
# MAGIC     SELECT * FROM mov_receita
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_folha
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_saude
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_fgts
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_ferias
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_13
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT * FROM mov_fornecedores
# MAGIC ),
# MAGIC
# MAGIC fluxo AS (
# MAGIC     SELECT
# MAGIC         data_vencimento,
# MAGIC         codigo,
# MAGIC         entidade,
# MAGIC         descricao,
# MAGIC         emissao,
# MAGIC         receber,
# MAGIC         pagar,
# MAGIC
# MAGIC         ROUND(
# MAGIC             receber - pagar,
# MAGIC             2
# MAGIC         ) AS total
# MAGIC
# MAGIC     FROM movimentos
# MAGIC ),
# MAGIC
# MAGIC resultado AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             SUM(total) OVER (
# MAGIC                 ORDER BY
# MAGIC                     data_vencimento,
# MAGIC                     codigo
# MAGIC                 ROWS BETWEEN
# MAGIC                     UNBOUNDED PRECEDING
# MAGIC                     AND CURRENT ROW
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS saldo
# MAGIC
# MAGIC     FROM fluxo
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     data_vencimento AS `DATA VENCIMENTO`,
# MAGIC     codigo AS `Título/CODIGO`,
# MAGIC     entidade AS `Cliente/Fornecedor`,
# MAGIC     descricao AS `DESCRICAO`,
# MAGIC     emissao AS `Emissão`,
# MAGIC     receber AS `Receber`,
# MAGIC     pagar AS `Pagar`,
# MAGIC     total AS `Total`,
# MAGIC     saldo AS `Saldo`
# MAGIC
# MAGIC FROM resultado
# MAGIC
# MAGIC ORDER BY
# MAGIC     data_vencimento,
# MAGIC     codigo;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3. Conclusão da Qual é o fluxo financeiro em determinado período?
# MAGIC
# MAGIC A análise do fluxo financeiro demonstrativo para o período de **01/01/2024 a 31/12/2024** apresentou **1.486 movimentos financeiros**, considerando as entradas de faturamento e as saídas relacionadas à folha de pagamento, benefícios, plano de saúde, FGTS, férias, 13º salário e fornecedores.
# MAGIC
# MAGIC No período analisado, foram identificados **R$ 10.819.635,11 em valores a receber** e **R$ 7.070.279,29 em valores a pagar**, resultando em um **saldo acumulado positivo de R$ 3.749.355,82**.
# MAGIC
# MAGIC Entre as saídas consideradas, os maiores valores corresponderam à **folha de pagamento, incluindo salário, ticket refeição e ticket alimentação**, com aproximadamente **R$ 3,34 milhões**, e aos **fornecedores**, com aproximadamente **R$ 2,16 milhões**. Também foram considerados os pagamentos de plano de saúde dos titulares e dependentes, FGTS, férias e 13º salário.
# MAGIC
# MAGIC A organização cronológica dos movimentos permite acompanhar a evolução do saldo ao longo do período e identificar as datas de maior concentração de entradas e saídas, oferecendo ao Financeiro e à Diretoria uma visão integrada das obrigações e receitas representadas no modelo.
# MAGIC
# MAGIC O saldo acumulado apresentado **não corresponde ao saldo bancário real da empresa**. O cálculo parte de saldo inicial igual a zero e considera exclusivamente os movimentos financeiros que puderam ser representados a partir dos dados disponíveis no MVP. Dessa forma, o resultado deve ser interpretado como um **fluxo financeiro demonstrativo**, adequado para apoiar a análise da relação temporal entre receitas e obrigações modeladas, e não como uma reprodução integral do fluxo de caixa histórico da empresa.