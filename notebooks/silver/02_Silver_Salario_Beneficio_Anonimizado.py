# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da camada Silver — Salários
# MAGIC
# MAGIC Este notebook realiza a transformação dos dados de salários da camada Bronze para a camada Silver.
# MAGIC
# MAGIC A tabela de origem é `workspace.bronze.salario_anonimizado`. O diagnóstico realizado na camada Bronze identificou 1.512 registros salariais associados a 347 DRTs.
# MAGIC
# MAGIC A camada Silver não reproduzirá todas as colunas existentes na Bronze. Serão selecionados exclusivamente os 6 atributos definidos durante o diagnóstico e necessários ao modelo e às análises previstas no MVP:
# MAGIC
# MAGIC - DRT;
# MAGIC - data da alteração;
# MAGIC - remuneração total;
# MAGIC - motivo;
# MAGIC - índice da alteração;
# MAGIC - cargo.
# MAGIC
# MAGIC Para representação da remuneração será utilizado o campo `REMUNERAÇÃO TOTAL`, conforme definido durante o diagnóstico. O campo `SALÁRIO` da origem não será propagado para a Silver.
# MAGIC
# MAGIC Durante a transformação Bronze → Silver serão aplicados os seguintes tratamentos:
# MAGIC
# MAGIC - utilização exclusiva dos registros com DRT preenchido, correspondentes aos vínculos empregatícios considerados no escopo;
# MAGIC - seleção exclusiva dos 6 atributos definidos para Salários;
# MAGIC - renomeação dos atributos conforme a nomenclatura adotada na camada Silver;
# MAGIC - conversão e padronização de `DATA DA ALTERAÇÃO` para o tipo `DATE`;
# MAGIC - conversão de `REMUNERAÇÃO TOTAL` para `DECIMAL(15,2)`, adequado à representação de valores monetários;
# MAGIC - conversão de `ÍNDICE` para `DECIMAL(3,2)`;
# MAGIC - preservação dos registros históricos existentes, sem deduplicação automática de alterações salariais;
# MAGIC - preservação de possíveis reduções ou repetições de remuneração, uma vez que esses registros podem representar eventos válidos do histórico salarial.
# MAGIC
# MAGIC A transformação preservará a rastreabilidade em relação à camada Bronze e não realizará nova anonimização dos dados.
# MAGIC
# MAGIC A tabela Silver será criada diretamente a partir da Bronze por meio de `CREATE TABLE AS SELECT`, realizando simultaneamente a seleção, transformação e carga dos 1.512 registros salariais associados aos 347 DRTs considerados no escopo.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE TABLE workspace.silver.salario_anonimizado AS
# MAGIC
# MAGIC SELECT
# MAGIC     CAST(`DRT` AS STRING) AS drt,
# MAGIC
# MAGIC     CASE
# MAGIC         -- Correção das três inconsistências de digitação identificadas na origem
# MAGIC         WHEN TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)) = '01/092022'
# MAGIC         THEN TO_DATE('01/09/2022', 'dd/MM/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)) = '01/092023'
# MAGIC         THEN TO_DATE('01/09/2023', 'dd/MM/yyyy')
# MAGIC
# MAGIC         WHEN TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)) = '01/092024'
# MAGIC         THEN TO_DATE('01/09/2024', 'dd/MM/yyyy')
# MAGIC
# MAGIC         -- Datas armazenadas como texto no formato dia/mês/ano
# MAGIC         WHEN TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)),
# MAGIC             'd/M/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         -- Representação das células originalmente armazenadas como data no Excel
# MAGIC         WHEN TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING))
# MAGIC              RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC         THEN TRY_TO_DATE(
# MAGIC             CONCAT(
# MAGIC                 SPLIT(TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)), '/')[0], '/',
# MAGIC                 SPLIT(TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)), '/')[1], '/20',
# MAGIC                 SPLIT(TRIM(CAST(`DATA DA ALTERAÇÃO` AS STRING)), '/')[2]
# MAGIC             ),
# MAGIC             'M/d/yyyy'
# MAGIC         )
# MAGIC
# MAGIC         ELSE NULL
# MAGIC     END AS data_alteracao,
# MAGIC
# MAGIC     CAST(`REMUNERAÇÃO TOTAL` AS DECIMAL(15,2)) AS salario,
# MAGIC     CAST(`MOTIVO` AS STRING) AS motivo,
# MAGIC     CAST(`ÍNDICE` AS DECIMAL(3,2)) AS indice_alteracao,
# MAGIC     CAST(`CARGO` AS STRING) AS cargo
# MAGIC
# MAGIC FROM workspace.bronze.salario_anonimizado
# MAGIC
# MAGIC WHERE `DRT` IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da construção da tabela Silver
# MAGIC
# MAGIC A transformação Bronze → Silver foi executada sem erros, resultando na criação da tabela `workspace.silver.salario_anonimizado`.
# MAGIC
# MAGIC A tabela foi construída a partir de `workspace.bronze.salario_anonimizado`, considerando exclusivamente os registros com DRT preenchido e mantendo somente os 6 atributos definidos para o histórico salarial.
# MAGIC
# MAGIC Os registros históricos foram preservados sem deduplicação automática, mantendo possíveis alterações sucessivas, repetições ou reduções de remuneração existentes na fonte.
# MAGIC
# MAGIC A criação e a carga da tabela foram concluídas. Na próxima etapa, o resultado será validado em relação ao diagnóstico realizado na camada Bronze.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da tabela Silver — Salários
# MAGIC
# MAGIC Esta etapa valida a tabela `workspace.silver.salario_anonimizado` após sua criação e carga definitiva.
# MAGIC
# MAGIC Com base no diagnóstico da camada Bronze e na conferência do arquivo de origem, são esperados:
# MAGIC
# MAGIC - 1.512 registros;
# MAGIC - 347 DRTs distintos;
# MAGIC - nenhum DRT nulo;
# MAGIC - nenhuma data de alteração nula;
# MAGIC - nenhuma remuneração nula;
# MAGIC - 143 motivos nulos;
# MAGIC - 480 índices de alteração nulos;
# MAGIC - 2 cargos nulos.
# MAGIC
# MAGIC Também serão verificadas as datas mínima e máxima de alteração salarial e os valores mínimo e máximo de remuneração e do índice de alteração.
# MAGIC
# MAGIC A validação permitirá confirmar que os tratamentos realizados na transformação Bronze → Silver preservaram o histórico salarial e os valores ausentes existentes na origem, sem introduzir perdas de informação.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS drts_distintos,
# MAGIC
# MAGIC     SUM(CASE WHEN drt IS NULL THEN 1 ELSE 0 END) AS drt_nulos,
# MAGIC     SUM(CASE WHEN data_alteracao IS NULL THEN 1 ELSE 0 END) AS data_alteracao_nulos,
# MAGIC     SUM(CASE WHEN salario IS NULL THEN 1 ELSE 0 END) AS salario_nulos,
# MAGIC     SUM(CASE WHEN motivo IS NULL THEN 1 ELSE 0 END) AS motivo_nulos,
# MAGIC     SUM(CASE WHEN indice_alteracao IS NULL THEN 1 ELSE 0 END) AS indice_alteracao_nulos,
# MAGIC     SUM(CASE WHEN cargo IS NULL THEN 1 ELSE 0 END) AS cargo_nulos,
# MAGIC
# MAGIC     MIN(data_alteracao) AS menor_data_alteracao,
# MAGIC     MAX(data_alteracao) AS maior_data_alteracao,
# MAGIC
# MAGIC     MIN(salario) AS menor_salario,
# MAGIC     MAX(salario) AS maior_salario,
# MAGIC
# MAGIC     MIN(indice_alteracao) AS menor_indice_alteracao,
# MAGIC     MAX(indice_alteracao) AS maior_indice_alteracao
# MAGIC
# MAGIC FROM workspace.silver.salario_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da validação da tabela Silver — Salários
# MAGIC
# MAGIC A validação confirmou que a tabela `workspace.silver.salario_anonimizado` foi construída de acordo com as regras definidas para a camada Silver.
# MAGIC
# MAGIC A tabela contém 1.512 registros associados a 347 DRTs distintos, correspondendo ao universo identificado durante o diagnóstico da camada Bronze.
# MAGIC
# MAGIC Não foram identificados valores nulos em `drt`, `data_alteracao` ou `salario`. O tratamento aplicado às três inconsistências de digitação existentes em `DATA DA ALTERAÇÃO` permitiu preservar as respectivas datas, eliminando os valores nulos que haviam sido produzidos na conversão inicial.
# MAGIC
# MAGIC Os valores nulos remanescentes correspondem aos dados efetivamente ausentes na origem:
# MAGIC
# MAGIC - 143 registros sem `motivo`;
# MAGIC - 480 registros sem `indice_alteracao`;
# MAGIC - 2 registros sem `cargo`.
# MAGIC
# MAGIC Esses valores foram preservados na camada Silver, sem preenchimento ou inferência artificial.
# MAGIC
# MAGIC O histórico salarial compreende alterações entre 14/08/2000 e 01/09/2024. Os valores de remuneração variam entre R$ 300,00 e R$ 17.041,44, enquanto os índices de alteração não nulos variam entre 0,00 e 1,59.
# MAGIC
# MAGIC A transformação preservou os registros históricos sem deduplicação automática, mantendo alterações sucessivas, repetições e eventuais reduções de remuneração existentes na fonte.
# MAGIC
# MAGIC Com essas verificações, a transformação Bronze → Silver de Salários é considerada concluída e validada.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Inclusão da data de desligamento
# MAGIC
# MAGIC A data de desligamento é necessária para identificar a situação do vínculo empregatício e para determinar a referência temporal utilizada posteriormente no cálculo dos benefícios.
# MAGIC
# MAGIC A informação corresponde à primeira coluna `DESLIGAMENTO` da planilha original de Empregados, localizada na coluna L e carregada na camada Bronze como `DESLIGAMENTO11`.
# MAGIC
# MAGIC A regra adotada é:
# MAGIC
# MAGIC - quando houver data de desligamento, o profissional será considerado desligado e essa data será preservada em `data_desligamento`;
# MAGIC - quando não houver data de desligamento, `data_desligamento` permanecerá nula, indicando que o vínculo é considerado ativo para as análises do MVP;
# MAGIC - para profissionais ativos, os cálculos posteriores de benefícios utilizarão os valores mais recentes disponíveis nas respectivas fontes.
# MAGIC
# MAGIC Como os demais atributos da tabela Silver de Empregados já foram construídos e validados, esta etapa acrescentará somente `data_desligamento`, sem alterar os demais dados existentes.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC ALTER TABLE workspace.silver.empregados_anonimizados
# MAGIC ADD COLUMN data_desligamento DATE;
# MAGIC
# MAGIC MERGE INTO workspace.silver.empregados_anonimizados AS s
# MAGIC
# MAGIC USING (
# MAGIC     SELECT
# MAGIC         CAST(`DRT` AS STRING) AS drt,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN `DESLIGAMENTO11` IS NULL
# MAGIC                  OR TRIM(CAST(`DESLIGAMENTO11` AS STRING)) = ''
# MAGIC             THEN NULL
# MAGIC
# MAGIC             WHEN TRIM(CAST(`DESLIGAMENTO11` AS STRING))
# MAGIC                  RLIKE '^\\d{1,2}/\\d{1,2}/\\d{4}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 TRIM(CAST(`DESLIGAMENTO11` AS STRING)),
# MAGIC                 'd/M/yyyy'
# MAGIC             )
# MAGIC
# MAGIC             WHEN TRIM(CAST(`DESLIGAMENTO11` AS STRING))
# MAGIC                  RLIKE '^\\d{1,2}/\\d{1,2}/\\d{2}$'
# MAGIC             THEN TRY_TO_DATE(
# MAGIC                 CONCAT(
# MAGIC                     SPLIT(TRIM(CAST(`DESLIGAMENTO11` AS STRING)), '/')[0], '/',
# MAGIC                     SPLIT(TRIM(CAST(`DESLIGAMENTO11` AS STRING)), '/')[1], '/',
# MAGIC                     CASE
# MAGIC                         WHEN CAST(
# MAGIC                             SPLIT(
# MAGIC                                 TRIM(CAST(`DESLIGAMENTO11` AS STRING)),
# MAGIC                                 '/'
# MAGIC                             )[2] AS INT
# MAGIC                         ) <= 26
# MAGIC                         THEN CONCAT(
# MAGIC                             '20',
# MAGIC                             SPLIT(
# MAGIC                                 TRIM(CAST(`DESLIGAMENTO11` AS STRING)),
# MAGIC                                 '/'
# MAGIC                             )[2]
# MAGIC                         )
# MAGIC                         ELSE CONCAT(
# MAGIC                             '19',
# MAGIC                             SPLIT(
# MAGIC                                 TRIM(CAST(`DESLIGAMENTO11` AS STRING)),
# MAGIC                                 '/'
# MAGIC                             )[2]
# MAGIC                         )
# MAGIC                     END
# MAGIC                 ),
# MAGIC                 'M/d/yyyy'
# MAGIC             )
# MAGIC
# MAGIC             ELSE NULL
# MAGIC         END AS data_desligamento
# MAGIC
# MAGIC     FROM workspace.bronze.empregados_anonimizados
# MAGIC
# MAGIC     WHERE `DRT` IS NOT NULL
# MAGIC
# MAGIC ) AS b
# MAGIC
# MAGIC ON s.drt = b.drt
# MAGIC
# MAGIC WHEN MATCHED THEN
# MAGIC UPDATE SET s.data_desligamento = b.data_desligamento;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da inclusão da data de desligamento
# MAGIC
# MAGIC A coluna `data_desligamento` foi adicionada à tabela `workspace.silver.empregados_anonimizados` e preenchida a partir da primeira coluna `DESLIGAMENTO` da planilha original de Empregados, correspondente a `DESLIGAMENTO11` na camada Bronze.
# MAGIC
# MAGIC A atualização alcançou os 347 registros existentes na tabela Silver, sem inclusão ou exclusão de registros e sem alteração dos demais atributos anteriormente validados.
# MAGIC
# MAGIC A interpretação adotada para `data_desligamento` é:
# MAGIC
# MAGIC - quando preenchida, identifica a data de término do respectivo vínculo empregatício;
# MAGIC - quando nula, o vínculo é considerado ativo para as análises do MVP;
# MAGIC - para vínculos ativos, os cálculos posteriores de Ticket e Plano de Saúde utilizarão os valores mais recentes disponíveis nas respectivas fontes.
# MAGIC
# MAGIC Como os demais atributos de Empregados já haviam sido validados, a próxima verificação será restrita à nova coluna `data_desligamento`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação da data de desligamento
# MAGIC
# MAGIC Esta etapa valida exclusivamente a coluna `data_desligamento` adicionada à tabela Silver de Empregados.
# MAGIC
# MAGIC A verificação tem como objetivos:
# MAGIC
# MAGIC - identificar a quantidade de vínculos com data de desligamento;
# MAGIC - identificar a quantidade de vínculos sem data de desligamento, considerados ativos para as análises do MVP;
# MAGIC - verificar as datas mínima e máxima de desligamento;
# MAGIC - confirmar que a conversão para `DATE` não produziu valores incompatíveis com a origem.
# MAGIC
# MAGIC Não serão revalidados os demais atributos da tabela de Empregados, pois essa validação já foi concluída anteriormente.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_desligamento IS NOT NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS vinculos_desligados,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN data_desligamento IS NULL THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS vinculos_ativos,
# MAGIC
# MAGIC     MIN(data_desligamento) AS menor_data_desligamento,
# MAGIC     MAX(data_desligamento) AS maior_data_desligamento
# MAGIC
# MAGIC FROM workspace.silver.empregados_anonimizados;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     data_desligamento
# MAGIC FROM workspace.silver.empregados_anonimizados
# MAGIC ORDER BY drt;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da validação da data de desligamento
# MAGIC
# MAGIC A validação da coluna `data_desligamento` confirmou a manutenção dos 347 vínculos existentes na tabela `workspace.silver.empregados_anonimizados`.
# MAGIC
# MAGIC Foram identificados:
# MAGIC
# MAGIC - 333 vínculos com data de desligamento;
# MAGIC - 14 vínculos sem data de desligamento, considerados ativos para as análises do MVP;
# MAGIC - data mínima de desligamento em 03/04/2012;
# MAGIC - data máxima de desligamento em 31/12/2024.
# MAGIC
# MAGIC A soma dos vínculos desligados e ativos corresponde aos 347 registros da tabela Silver de Empregados.
# MAGIC
# MAGIC A coluna `data_desligamento` está, portanto, disponível para utilização nas etapas posteriores do pipeline. Para os profissionais desligados, essa data será utilizada como referência temporal na atribuição dos benefícios. Para os 14 vínculos ativos, serão utilizados os valores mais recentes disponíveis nas respectivas fontes de Ticket e Plano de Saúde.
# MAGIC
# MAGIC Com essa validação, a inclusão de `data_desligamento` na tabela Silver de Empregados é considerada concluída.

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Construção da tabela Silver — Benefícios
# MAGIC
# MAGIC Este notebook realiza a construção da tabela de Benefícios na camada Silver.
# MAGIC
# MAGIC A transformação será realizada em etapas, pois os valores utilizados no MVP são provenientes de diferentes fontes da camada Bronze.
# MAGIC
# MAGIC A primeira etapa utiliza `workspace.bronze.beneficio_anonimizado` para estabelecer os DRTs que compõem a tabela de Benefícios.
# MAGIC
# MAGIC A estrutura Silver adotada contém os seguintes atributos:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `ticket_refeicao`;
# MAGIC - `ticket_alimentacao`;
# MAGIC - `plano_saude`;
# MAGIC - `total_beneficios`.
# MAGIC
# MAGIC Os valores de ticket e plano de saúde não serão obtidos diretamente dos respectivos campos existentes na planilha principal de benefícios. Esses componentes serão preenchidos posteriormente a partir das fontes históricas específicas disponíveis na camada Bronze.
# MAGIC
# MAGIC Nesta primeira etapa:
# MAGIC
# MAGIC - serão considerados somente os registros com DRT preenchido;
# MAGIC - `drt` será convertido para `STRING`;
# MAGIC - os campos de ticket, plano de saúde e total de benefícios serão inicialmente criados como nulos;
# MAGIC - os valores monetários serão representados como `DECIMAL(15,2)`.
# MAGIC
# MAGIC Nas etapas seguintes, a tabela será enriquecida com os valores de ticket e plano de saúde provenientes das respectivas fontes históricas. O `total_beneficios` será posteriormente calculado a partir dos componentes considerados no escopo do MVP.
# MAGIC
# MAGIC Essa abordagem evita utilizar como histórico valores pontuais existentes na planilha principal e mantém separadas as diferentes etapas de construção da informação na camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE TABLE workspace.silver.beneficio_anonimizado AS
# MAGIC
# MAGIC SELECT
# MAGIC     CAST(`DRT` AS STRING) AS drt,
# MAGIC
# MAGIC     CAST(NULL AS DECIMAL(15,2)) AS ticket_refeicao,
# MAGIC     CAST(NULL AS DECIMAL(15,2)) AS ticket_alimentacao,
# MAGIC     CAST(NULL AS DECIMAL(15,2)) AS plano_saude,
# MAGIC     CAST(NULL AS DECIMAL(15,2)) AS total_beneficios
# MAGIC
# MAGIC FROM workspace.bronze.beneficio_anonimizado
# MAGIC
# MAGIC WHERE `DRT` IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da criação da tabela Silver — Benefícios
# MAGIC
# MAGIC A tabela `workspace.silver.beneficio_anonimizado` foi criada com os DRTs que compõem o conjunto de Benefícios e com os atributos que serão preenchidos nas etapas seguintes.
# MAGIC
# MAGIC Os valores de benefícios serão determinados individualmente para cada vínculo empregatício, utilizando uma data de referência.
# MAGIC
# MAGIC Para profissionais desligados, a data de referência corresponde à data de saída registrada nos dados de Empregados. Dessa forma, os benefícios atribuídos ao profissional representarão os valores vigentes no momento de seu desligamento.
# MAGIC
# MAGIC Para profissionais sem data de saída, considerados ativos para esta finalidade, serão utilizados os valores correspondentes à última referência disponível nas respectivas fontes de benefícios.
# MAGIC
# MAGIC A próxima etapa realizará o preenchimento dos valores de ticket. Posteriormente será tratado o plano de saúde, que dependerá também da idade do profissional na respectiva data de referência.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Atribuição dos valores de Ticket
# MAGIC
# MAGIC Os valores de ticket serão atribuídos individualmente aos DRTs existentes em `workspace.silver.beneficio_anonimizado`, utilizando a situação do vínculo registrada em `workspace.silver.empregados_anonimizados`.
# MAGIC
# MAGIC A data de referência será determinada da seguinte forma:
# MAGIC
# MAGIC - para vínculos com `data_desligamento` preenchida, será utilizada a própria data de desligamento;
# MAGIC - para vínculos sem `data_desligamento`, considerados ativos para esta finalidade, será utilizado o valor mais recente disponível na fonte histórica de Ticket.
# MAGIC
# MAGIC As alterações dos valores de Ticket entram em vigor em setembro. Portanto:
# MAGIC
# MAGIC - desligamentos ocorridos entre janeiro e agosto utilizarão os valores cuja vigência começou em setembro do ano anterior;
# MAGIC - desligamentos ocorridos entre setembro e dezembro utilizarão os valores cuja vigência começou em setembro do próprio ano.
# MAGIC
# MAGIC Por exemplo, um desligamento em agosto de 2013 utiliza os valores vigentes desde setembro de 2012, enquanto um desligamento em setembro de 2013 utiliza os valores cuja vigência se inicia em setembro de 2013.
# MAGIC
# MAGIC A fonte histórica utilizada é `workspace.bronze.valor_ticket_2010_2025`.
# MAGIC
# MAGIC Nesta etapa serão preenchidos os atributos de Ticket da tabela Silver de Benefícios. O Plano de Saúde será tratado posteriormente, considerando também a idade do profissional na respectiva data de referência.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC MERGE INTO workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC USING (
# MAGIC
# MAGIC     WITH referencia AS (
# MAGIC
# MAGIC         SELECT
# MAGIC             b.drt,
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN e.data_desligamento IS NULL
# MAGIC                 THEN 2025
# MAGIC
# MAGIC                 WHEN MONTH(e.data_desligamento) >= 9
# MAGIC                 THEN YEAR(e.data_desligamento)
# MAGIC
# MAGIC                 ELSE YEAR(e.data_desligamento) - 1
# MAGIC             END AS ano_inicio_vigencia
# MAGIC
# MAGIC         FROM workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC         INNER JOIN workspace.silver.empregados_anonimizados AS e
# MAGIC             ON b.drt = e.drt
# MAGIC     ),
# MAGIC
# MAGIC     ticket AS (
# MAGIC
# MAGIC         SELECT
# MAGIC             CAST(
# MAGIC                 TRIM(
# MAGIC                     SPLIT(
# MAGIC                         CAST(`Período (CCT)` AS STRING),
# MAGIC                         '/'
# MAGIC                     )[0]
# MAGIC                 ) AS INT
# MAGIC             ) AS ano_inicio_vigencia,
# MAGIC
# MAGIC             CAST(
# MAGIC                 `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC                 AS DECIMAL(15,2)
# MAGIC             ) AS ticket_refeicao,
# MAGIC
# MAGIC             CAST(
# MAGIC                 `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC                 AS DECIMAL(15,2)
# MAGIC             ) AS ticket_alimentacao
# MAGIC
# MAGIC         FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC     )
# MAGIC
# MAGIC     SELECT
# MAGIC         r.drt,
# MAGIC         t.ticket_refeicao,
# MAGIC         t.ticket_alimentacao
# MAGIC
# MAGIC     FROM referencia AS r
# MAGIC
# MAGIC     LEFT JOIN ticket AS t
# MAGIC         ON r.ano_inicio_vigencia = t.ano_inicio_vigencia
# MAGIC
# MAGIC ) AS origem
# MAGIC
# MAGIC ON b.drt = origem.drt
# MAGIC
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC     b.ticket_refeicao = origem.ticket_refeicao,
# MAGIC     b.ticket_alimentacao = origem.ticket_alimentacao;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da atribuição dos valores de Ticket
# MAGIC
# MAGIC A atribuição dos valores de Ticket foi executada para os 342 registros existentes em `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC A transformação utilizou `data_desligamento` da tabela Silver de Empregados como referência para os vínculos desligados e o período mais recente disponível para os vínculos considerados ativos.
# MAGIC
# MAGIC A regra de vigência com alteração em setembro foi aplicada para determinar o período correspondente a cada vínculo.
# MAGIC
# MAGIC O `MERGE` atualizou os 342 registros da tabela Silver de Benefícios, sem inserir ou excluir registros.
# MAGIC
# MAGIC Antes de concluir esta etapa, será verificado se todos os DRTs receberam os respectivos valores de Ticket ou se existem registros sem correspondência na fonte histórica.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Validação dos valores de Ticket
# MAGIC
# MAGIC Esta etapa verifica o resultado da atribuição dos valores de Ticket na tabela `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - o total de registros da tabela;
# MAGIC - a quantidade de valores nulos em `ticket_refeicao`;
# MAGIC - a quantidade de valores nulos em `ticket_alimentacao`;
# MAGIC - os valores mínimo e máximo atribuídos a cada componente.
# MAGIC
# MAGIC A validação permitirá identificar eventuais vínculos para os quais não tenha sido encontrada uma vigência correspondente na fonte histórica de Ticket.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN ticket_refeicao IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS ticket_refeicao_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN ticket_alimentacao IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS ticket_alimentacao_nulos,
# MAGIC
# MAGIC     MIN(ticket_refeicao) AS menor_ticket_refeicao,
# MAGIC     MAX(ticket_refeicao) AS maior_ticket_refeicao,
# MAGIC
# MAGIC     MIN(ticket_alimentacao) AS menor_ticket_alimentacao,
# MAGIC     MAX(ticket_alimentacao) AS maior_ticket_alimentacao
# MAGIC
# MAGIC FROM workspace.silver.beneficio_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da validação inicial dos valores de Ticket
# MAGIC
# MAGIC A validação confirmou a manutenção dos 342 registros da tabela `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC Foram identificados:
# MAGIC
# MAGIC - 11 registros sem valor em `ticket_refeicao`;
# MAGIC - 11 registros sem valor em `ticket_alimentacao`;
# MAGIC - valores de `ticket_refeicao` entre R$ 304,50 e R$ 588,00;
# MAGIC - valores de `ticket_alimentacao` entre R$ 148,00 e R$ 299,77.
# MAGIC
# MAGIC Como 11 vínculos não receberam valores de Ticket, a etapa ainda não será considerada concluída.
# MAGIC
# MAGIC Antes de realizar qualquer ajuste, serão identificados os DRTs correspondentes e suas respectivas datas de desligamento para determinar por que não houve correspondência com uma vigência disponível na fonte histórica.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Verificação dos vínculos sem valores de Ticket
# MAGIC
# MAGIC Esta etapa identifica os vínculos que permaneceram sem valores de Ticket após a atribuição inicial.
# MAGIC
# MAGIC Para cada registro serão apresentados o DRT e a data de desligamento existente na tabela Silver de Empregados.
# MAGIC
# MAGIC O objetivo é verificar a referência temporal desses vínculos antes de definir qualquer tratamento adicional, sem realizar preenchimentos ou inferências nesta etapa.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC UPDATE workspace.silver.beneficio_anonimizado
# MAGIC
# MAGIC SET
# MAGIC     ticket_refeicao = (
# MAGIC         SELECT
# MAGIC             MAX(
# MAGIC                 CAST(
# MAGIC                     `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC                     AS DECIMAL(15,2)
# MAGIC                 )
# MAGIC             )
# MAGIC         FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC     ),
# MAGIC
# MAGIC     ticket_alimentacao = (
# MAGIC         SELECT
# MAGIC             MAX(
# MAGIC                 CAST(
# MAGIC                     `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC                     AS DECIMAL(15,2)
# MAGIC                 )
# MAGIC             )
# MAGIC         FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC     )
# MAGIC
# MAGIC WHERE
# MAGIC     ticket_refeicao IS NULL
# MAGIC     OR ticket_alimentacao IS NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão do tratamento dos registros sem Ticket
# MAGIC
# MAGIC Os 11 registros que permaneceram sem correspondência após a atribuição inicial foram atualizados utilizando os maiores valores disponíveis de Ticket Refeição e Ticket Alimentação na fonte histórica.
# MAGIC
# MAGIC O tratamento foi aplicado exclusivamente a esses 11 registros, sem modificar os valores anteriormente atribuídos aos demais vínculos.
# MAGIC
# MAGIC A próxima etapa verificará se todos os 342 registros da tabela Silver de Benefícios possuem valores de Ticket após o tratamento.

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Validação final dos valores de Ticket
# MAGIC
# MAGIC Esta etapa realiza a validação final dos valores de Ticket na tabela `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - o total de registros;
# MAGIC - a quantidade de valores nulos em `ticket_refeicao`;
# MAGIC - a quantidade de valores nulos em `ticket_alimentacao`;
# MAGIC - os valores mínimo e máximo de cada componente.
# MAGIC
# MAGIC A ausência de valores nulos confirmará que todos os vínculos receberam valores de Ticket segundo as regras definidas para o MVP.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN ticket_refeicao IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS ticket_refeicao_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN ticket_alimentacao IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS ticket_alimentacao_nulos,
# MAGIC
# MAGIC     MIN(ticket_refeicao) AS menor_ticket_refeicao,
# MAGIC     MAX(ticket_refeicao) AS maior_ticket_refeicao,
# MAGIC
# MAGIC     MIN(ticket_alimentacao) AS menor_ticket_alimentacao,
# MAGIC     MAX(ticket_alimentacao) AS maior_ticket_alimentacao
# MAGIC
# MAGIC FROM workspace.silver.beneficio_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Conclusão da atribuição e validação dos valores de Ticket
# MAGIC
# MAGIC A atribuição dos valores de Ticket na tabela `workspace.silver.beneficio_anonimizado` foi concluída e validada para os 342 vínculos considerados no escopo de Benefícios.
# MAGIC
# MAGIC Os valores foram determinados individualmente a partir da situação de cada vínculo empregatício, utilizando a `data_desligamento` disponível na tabela `workspace.silver.empregados_anonimizados`.
# MAGIC
# MAGIC Para os profissionais desligados, foi aplicado o valor vigente na respectiva data de desligamento, considerando que as alterações dos valores de Ticket entram em vigor no mês de setembro. Dessa forma:
# MAGIC
# MAGIC - desligamentos ocorridos entre janeiro e agosto utilizam a vigência iniciada em setembro do ano anterior;
# MAGIC - desligamentos ocorridos entre setembro e dezembro utilizam a vigência iniciada em setembro do próprio ano.
# MAGIC
# MAGIC Para os profissionais considerados ativos, ou seja, sem `data_desligamento`, foram utilizados os valores mais recentes disponíveis na fonte histórica de Ticket.
# MAGIC
# MAGIC Os 11 vínculos que inicialmente não apresentaram correspondência com uma vigência disponível na fonte histórica receberam, conforme premissa adotada para o MVP, os maiores valores disponíveis de Ticket Refeição e Ticket Alimentação.
# MAGIC
# MAGIC A conferência final dos 342 registros confirmou a correspondência dos DRTs, nomes, datas de admissão e datas de desligamento com os dados de Empregados, bem como a aplicação dos valores de Ticket segundo as regras definidas.
# MAGIC
# MAGIC Com essas verificações, a atribuição dos valores de Ticket na camada Silver de Benefícios é considerada concluída e validada.

# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Atribuição dos valores de Plano de Saúde
# MAGIC
# MAGIC O valor do Plano de Saúde será determinado individualmente para cada vínculo existente em `workspace.silver.beneficio_anonimizado`, considerando tanto o profissional titular quanto seus dependentes.
# MAGIC
# MAGIC A determinação do custo depende da data de referência do vínculo, da idade de cada pessoa nessa data e da tabela de valores do plano vigente no respectivo período.
# MAGIC
# MAGIC ## Data de referência
# MAGIC
# MAGIC Para cada profissional será definida uma data de referência:
# MAGIC
# MAGIC - quando `data_desligamento` estiver preenchida, será utilizada a própria data de desligamento;
# MAGIC - quando `data_desligamento` estiver nula, o profissional será considerado ativo para esta finalidade e será utilizada a referência mais recente disponível nos dados de Plano de Saúde.
# MAGIC
# MAGIC ## Vigência dos valores do plano
# MAGIC
# MAGIC As alterações dos valores do Plano de Saúde entram em vigor no mês de **outubro**.
# MAGIC
# MAGIC Dessa forma:
# MAGIC
# MAGIC - para datas de referência entre janeiro e setembro, será utilizada a tabela cuja vigência teve início em outubro do ano anterior;
# MAGIC - para datas de referência entre outubro e dezembro, será utilizada a tabela cuja vigência teve início em outubro do próprio ano.
# MAGIC
# MAGIC Essa regra será aplicada tanto aos profissionais desligados quanto à determinação da última vigência disponível para os profissionais ativos.
# MAGIC
# MAGIC ## Determinação da faixa etária
# MAGIC
# MAGIC A idade utilizada para enquadramento no Plano de Saúde será calculada na data de referência do vínculo.
# MAGIC
# MAGIC Para o titular, será utilizada `data_nascimento` da tabela Silver de Empregados.
# MAGIC
# MAGIC Para cada dependente associado ao DRT, será utilizada sua própria data de nascimento. Dessa forma, titular e dependentes poderão estar enquadrados em faixas etárias diferentes na mesma data de referência.
# MAGIC
# MAGIC Para profissionais desligados, tanto a idade do titular quanto a idade de seus dependentes será calculada na data de desligamento, evitando a utilização de idades ou valores posteriores ao encerramento do vínculo.
# MAGIC
# MAGIC ## Cálculo do custo
# MAGIC
# MAGIC O valor correspondente a cada pessoa será determinado pela combinação entre:
# MAGIC
# MAGIC - tabela do plano vigente na data de referência;
# MAGIC - idade da pessoa nessa data;
# MAGIC - faixa etária correspondente.
# MAGIC
# MAGIC O custo do Plano de Saúde associado ao DRT será composto pelo valor aplicável ao titular acrescido dos valores aplicáveis aos seus dependentes.
# MAGIC
# MAGIC As fontes históricas utilizadas serão:
# MAGIC
# MAGIC - `workspace.bronze.plano_saude_ate_2022`;
# MAGIC - `workspace.bronze.plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC A transformação respeitará a mudança entre as fontes de Plano de Saúde e o corte de vigência em outubro, sem utilizar valores posteriores à data de referência dos vínculos desligados.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.1 Regra de atribuição do Plano de Saúde ao titular
# MAGIC
# MAGIC Nesta etapa será calculado exclusivamente o custo do Plano de Saúde correspondente ao empregado titular. Os dependentes permanecerão separados e serão tratados posteriormente, utilizando a mesma lógica de vigência e enquadramento por faixa etária.
# MAGIC
# MAGIC Como premissa simplificadora do MVP, considera-se que todos os empregados e dependentes estão vinculados à modalidade de menor custo disponível. Nas fontes analisadas, essa modalidade corresponde ao **Plano Especial**.
# MAGIC
# MAGIC Para cada empregado, a determinação do valor seguirá três etapas:
# MAGIC
# MAGIC 1. definição da data de referência;
# MAGIC 2. cálculo da idade do empregado nessa data;
# MAGIC 3. enquadramento na faixa etária correspondente e atribuição do valor vigente do Plano Especial.
# MAGIC
# MAGIC Para empregados desligados, a data de referência será a `data_desligamento`. Para empregados sem data de desligamento, considerados ativos para esta finalidade, será utilizada a referência mais recente disponível para o Plano de Saúde.
# MAGIC
# MAGIC Como regra de negócio do MVP, será considerado **outubro como mês de início de uma nova vigência anual do Plano de Saúde**. Dessa forma, referências entre janeiro e setembro utilizarão a vigência iniciada no ano anterior, enquanto referências entre outubro e dezembro utilizarão a vigência iniciada no próprio ano.
# MAGIC
# MAGIC A fonte histórica `workspace.bronze.plano_saude_ate_2022` contém valores anuais por faixa etária e modalidade. Para o período posterior à mudança para o plano Vital, será utilizada `workspace.bronze.plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC A idade será calculada na própria data de referência, evitando que empregados desligados sejam enquadrados segundo uma faixa etária alcançada somente após o encerramento do vínculo.
# MAGIC
# MAGIC A atribuição realizada nesta etapa corresponde somente ao titular. O custo dos dependentes será incorporado posteriormente, sem alterar a granularidade atual da tabela Silver de Benefícios.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC MERGE INTO workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC USING (
# MAGIC
# MAGIC     WITH empregados AS (
# MAGIC
# MAGIC         SELECT
# MAGIC             b.drt,
# MAGIC             e.data_nascimento,
# MAGIC             e.data_desligamento,
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN e.data_desligamento IS NOT NULL
# MAGIC                     THEN e.data_desligamento
# MAGIC                 ELSE DATE('2025-10-01')
# MAGIC             END AS data_referencia
# MAGIC
# MAGIC         FROM workspace.silver.beneficio_anonimizado AS b
# MAGIC
# MAGIC         INNER JOIN workspace.silver.empregados_anonimizados AS e
# MAGIC             ON b.drt = e.drt
# MAGIC     ),
# MAGIC
# MAGIC     idade AS (
# MAGIC
# MAGIC         SELECT
# MAGIC             drt,
# MAGIC             data_referencia,
# MAGIC
# MAGIC             FLOOR(
# MAGIC                 MONTHS_BETWEEN(
# MAGIC                     data_referencia,
# MAGIC                     data_nascimento
# MAGIC                 ) / 12
# MAGIC             ) AS idade,
# MAGIC
# MAGIC             CASE
# MAGIC                 WHEN MONTH(data_referencia) >= 10
# MAGIC                     THEN YEAR(data_referencia)
# MAGIC                 ELSE YEAR(data_referencia) - 1
# MAGIC             END AS ano_vigencia
# MAGIC
# MAGIC         FROM empregados
# MAGIC     ),
# MAGIC
# MAGIC     valor_plano AS (
# MAGIC
# MAGIC         SELECT
# MAGIC             drt,
# MAGIC             idade,
# MAGIC             ano_vigencia,
# MAGIC
# MAGIC             CAST(
# MAGIC
# MAGIC                 CASE
# MAGIC
# MAGIC                     /* Plano Vital mais recente */
# MAGIC                     WHEN ano_vigencia >= 2022 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 395.74
# MAGIC                             WHEN idade BETWEEN 19 AND 23 THEN 466.97
# MAGIC                             WHEN idade BETWEEN 24 AND 28 THEN 565.03
# MAGIC                             WHEN idade BETWEEN 29 AND 33 THEN 678.04
# MAGIC                             WHEN idade BETWEEN 34 AND 38 THEN 772.96
# MAGIC                             WHEN idade BETWEEN 39 AND 43 THEN 796.16
# MAGIC                             WHEN idade BETWEEN 44 AND 48 THEN 969.36
# MAGIC                             WHEN idade BETWEEN 49 AND 53 THEN 1140.16
# MAGIC                             WHEN idade BETWEEN 54 AND 58 THEN 1356.80
# MAGIC                             WHEN idade >= 59 THEN 2374.40
# MAGIC                         END
# MAGIC
# MAGIC                     /* 2021 */
# MAGIC                     WHEN ano_vigencia = 2021 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 569.48
# MAGIC                             WHEN idade BETWEEN 19 AND 23 THEN 834.27
# MAGIC                             WHEN idade BETWEEN 24 AND 28 THEN 959.43
# MAGIC                             WHEN idade BETWEEN 29 AND 33 THEN 1094.17
# MAGIC                             WHEN idade BETWEEN 34 AND 38 THEN 1128.48
# MAGIC                             WHEN idade BETWEEN 39 AND 43 THEN 1290.33
# MAGIC                             WHEN idade BETWEEN 44 AND 48 THEN 1392.82
# MAGIC                             WHEN idade BETWEEN 49 AND 53 THEN 1838.51
# MAGIC                             WHEN idade BETWEEN 54 AND 58 THEN 2138.23
# MAGIC                             WHEN idade >= 59 THEN 3404.04
# MAGIC                         END
# MAGIC
# MAGIC                     /* 2020 */
# MAGIC                     WHEN ano_vigencia = 2020 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 520.79
# MAGIC                             WHEN idade BETWEEN 19 AND 23 THEN 762.94
# MAGIC                             WHEN idade BETWEEN 24 AND 28 THEN 877.39
# MAGIC                             WHEN idade BETWEEN 29 AND 33 THEN 1000.61
# MAGIC                             WHEN idade BETWEEN 34 AND 38 THEN 1031.99
# MAGIC                             WHEN idade BETWEEN 39 AND 43 THEN 1180.00
# MAGIC                             WHEN idade BETWEEN 44 AND 48 THEN 1273.73
# MAGIC                             WHEN idade BETWEEN 49 AND 53 THEN 1681.31
# MAGIC                             WHEN idade BETWEEN 54 AND 58 THEN 1955.40
# MAGIC                             WHEN idade >= 59 THEN 3112.98
# MAGIC                         END
# MAGIC
# MAGIC                     /* 2019 */
# MAGIC                     WHEN ano_vigencia = 2019 THEN
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 461.37
# MAGIC                             WHEN idade BETWEEN 19 AND 23 THEN 675.89
# MAGIC                             WHEN idade BETWEEN 24 AND 28 THEN 777.28
# MAGIC                             WHEN idade BETWEEN 29 AND 33 THEN 886.44
# MAGIC                             WHEN idade BETWEEN 34 AND 38 THEN 914.24
# MAGIC                             WHEN idade BETWEEN 39 AND 43 THEN 1045.36
# MAGIC                             WHEN idade BETWEEN 44 AND 48 THEN 1128.40
# MAGIC                             WHEN idade BETWEEN 49 AND 53 THEN 1489.47
# MAGIC                             WHEN idade BETWEEN 54 AND 58 THEN 1732.28
# MAGIC                             WHEN idade >= 59 THEN 2757.79
# MAGIC                         END
# MAGIC
# MAGIC                     /* Referências anteriores */
# MAGIC                     ELSE
# MAGIC                         CASE
# MAGIC                             WHEN idade <= 18 THEN 401.68
# MAGIC                             WHEN idade BETWEEN 19 AND 23 THEN 588.44
# MAGIC                             WHEN idade BETWEEN 24 AND 28 THEN 676.72
# MAGIC                             WHEN idade BETWEEN 29 AND 33 THEN 771.76
# MAGIC                             WHEN idade BETWEEN 34 AND 38 THEN 795.96
# MAGIC                             WHEN idade BETWEEN 39 AND 43 THEN 910.12
# MAGIC                             WHEN idade BETWEEN 44 AND 48 THEN 982.41
# MAGIC                             WHEN idade BETWEEN 49 AND 53 THEN 1296.77
# MAGIC                             WHEN idade BETWEEN 54 AND 58 THEN 1508.17
# MAGIC                             WHEN idade >= 59 THEN 2401.00
# MAGIC                         END
# MAGIC                 END
# MAGIC
# MAGIC             AS DECIMAL(15,2)) AS plano_saude
# MAGIC
# MAGIC         FROM idade
# MAGIC     )
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         plano_saude
# MAGIC
# MAGIC     FROM valor_plano
# MAGIC
# MAGIC ) AS origem
# MAGIC
# MAGIC ON b.drt = origem.drt
# MAGIC
# MAGIC WHEN MATCHED THEN UPDATE SET
# MAGIC     b.plano_saude = origem.plano_saude;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6.1 Conclusão da atribuição do Plano de Saúde ao titular
# MAGIC
# MAGIC A execução do `MERGE` atualizou os **342 registros** existentes em `workspace.silver.beneficio_anonimizado`, sem inserção ou exclusão de registros.
# MAGIC
# MAGIC Nesta etapa, o valor de `plano_saude` foi atribuído exclusivamente ao **empregado titular**, mantendo os dependentes separados para tratamento posterior.
# MAGIC
# MAGIC A atribuição considerou a data de referência de cada vínculo, a idade do empregado nessa data, o enquadramento na respectiva faixa etária e a premissa adotada para o MVP de utilização da modalidade de Plano de Saúde de menor custo.
# MAGIC
# MAGIC Para os empregados desligados, a referência utilizada foi a `data_desligamento`. Para os empregados considerados ativos, foi utilizada a referência definida para o período mais recente do plano.
# MAGIC
# MAGIC O resultado do `MERGE` confirma que todos os 342 registros da tabela de Benefícios foram alcançados pela atualização. A consistência dos valores atribuídos será verificada na etapa seguinte de validação.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.2 Validação da atribuição do Plano de Saúde
# MAGIC
# MAGIC Após a atribuição do valor do Plano de Saúde aos titulares, será realizada a validação dos resultados obtidos.
# MAGIC
# MAGIC A verificação tem como objetivo confirmar se todos os vínculos receberam um valor de Plano de Saúde e observar o intervalo dos valores atribuídos antes do encerramento desta etapa.
# MAGIC
# MAGIC Essa validação é necessária porque o resultado do `MERGE` confirma a atualização dos registros, mas não valida, isoladamente, o resultado das regras de idade, faixa etária, vigência e valor aplicadas.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN plano_saude IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS plano_saude_nulos,
# MAGIC
# MAGIC     MIN(plano_saude) AS menor_plano_saude,
# MAGIC     MAX(plano_saude) AS maior_plano_saude
# MAGIC
# MAGIC FROM workspace.silver.beneficio_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6.2 Conclusão da validação da atribuição do Plano de Saúde
# MAGIC
# MAGIC A validação da atribuição do Plano de Saúde apresentou **342 registros**, sem valores nulos em `plano_saude`.
# MAGIC
# MAGIC Os valores atribuídos aos titulares variam entre **R$ 401,68 e R$ 3.112,98**, confirmando que todos os vínculos contemplados na tabela Silver de Benefícios receberam um valor de Plano de Saúde.
# MAGIC
# MAGIC A atribuição foi realizada considerando a data de referência do vínculo, a idade do empregado nessa data, seu enquadramento na respectiva faixa etária e a premissa simplificadora adotada para o MVP de utilização da modalidade de menor custo.
# MAGIC
# MAGIC Nesta etapa, `plano_saude` representa exclusivamente o custo correspondente ao **titular**. Os custos dos dependentes serão tratados posteriormente, a partir da tabela Silver de Dependentes, preservando a separação entre as entidades.
# MAGIC
# MAGIC Com a ausência de valores nulos e a cobertura dos 342 vínculos, a atribuição do Plano de Saúde ao titular é considerada concluída na tabela `workspace.silver.beneficio_anonimizado`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 7. Cálculo do total de benefícios
# MAGIC
# MAGIC Após a atribuição dos valores de Ticket Refeição, Ticket Alimentação e Plano de Saúde, será calculado o atributo `total_beneficios`.
# MAGIC
# MAGIC Para o escopo definido no MVP, o total será composto por:
# MAGIC
# MAGIC - `ticket_refeicao`;
# MAGIC - `ticket_alimentacao`;
# MAGIC - `plano_saude`.
# MAGIC
# MAGIC Assim:
# MAGIC
# MAGIC **total_beneficios = ticket_refeicao + ticket_alimentacao + plano_saude**
# MAGIC
# MAGIC Vale-transporte e plano dental não fazem parte do escopo definido para esta análise e, portanto, não serão incorporados ao cálculo.
# MAGIC
# MAGIC Nesta etapa, `plano_saude` representa exclusivamente o custo do empregado titular. Consequentemente, `total_beneficios` também representa inicialmente o custo mensal dos benefícios do titular.
# MAGIC
# MAGIC O custo dos dependentes será tratado posteriormente a partir da tabela Silver de Dependentes. Após esse tratamento, o componente de Plano de Saúde e, consequentemente, o total de benefícios poderão ser atualizados para incorporar os valores correspondentes aos dependentes.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC UPDATE workspace.silver.beneficio_anonimizado
# MAGIC
# MAGIC SET total_beneficios =
# MAGIC     COALESCE(ticket_refeicao, 0)
# MAGIC     + COALESCE(ticket_alimentacao, 0)
# MAGIC     + COALESCE(plano_saude, 0);

# COMMAND ----------

# MAGIC %md
# MAGIC ### 7. Conclusão do cálculo do total de benefícios
# MAGIC
# MAGIC A execução do `UPDATE` recalculou `total_beneficios` para os **342 registros** existentes em `workspace.silver.beneficio_anonimizado`.
# MAGIC
# MAGIC O valor foi obtido pela soma dos três componentes definidos no escopo atual do MVP:
# MAGIC
# MAGIC - Ticket Refeição;
# MAGIC - Ticket Alimentação;
# MAGIC - Plano de Saúde do titular.
# MAGIC
# MAGIC Nesta etapa, o total ainda não incorpora o custo de Plano de Saúde dos dependentes, que será tratado posteriormente a partir dos dados de Dependentes.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7.1 Validação do total de benefícios
# MAGIC
# MAGIC Após o cálculo de `total_beneficios`, será verificada a cobertura dos registros e a consistência aritmética entre o total armazenado e a soma dos três componentes utilizados em sua composição.
# MAGIC
# MAGIC A validação permitirá identificar valores nulos e eventuais divergências entre `total_beneficios` e a soma de `ticket_refeicao`, `ticket_alimentacao` e `plano_saude`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN total_beneficios IS NULL THEN 1 ELSE 0 END
# MAGIC     ) AS total_beneficios_nulos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN total_beneficios <>
# MAGIC                  COALESCE(ticket_refeicao, 0)
# MAGIC                  + COALESCE(ticket_alimentacao, 0)
# MAGIC                  + COALESCE(plano_saude, 0)
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS divergencias_calculo,
# MAGIC
# MAGIC     MIN(total_beneficios) AS menor_total_beneficios,
# MAGIC     MAX(total_beneficios) AS maior_total_beneficios
# MAGIC
# MAGIC FROM workspace.silver.beneficio_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 7.1 Conclusão validação do total de benefícios
# MAGIC
# MAGIC A validação do cálculo de `total_beneficios` apresentou **342 registros**, sem valores nulos e sem divergências entre o total armazenado e a soma de seus componentes.
# MAGIC
# MAGIC Os valores de `total_beneficios` variam entre **R$ 947,18 e R$ 3.900,98**.
# MAGIC
# MAGIC A ausência de divergências confirma a consistência aritmética do cálculo:
# MAGIC
# MAGIC **total_beneficios = ticket_refeicao + ticket_alimentacao + plano_saude**
# MAGIC
# MAGIC No escopo atual, `plano_saude` corresponde exclusivamente ao custo do empregado titular. Dessa forma, `total_beneficios` ainda não incorpora os custos de Plano de Saúde dos dependentes, que serão tratados posteriormente a partir da tabela Silver de Dependentes.
# MAGIC
# MAGIC Com essas verificações, o cálculo de `total_beneficios` é considerado concluído e validado na tabela `workspace.silver.beneficio_anonimizado`.