# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição da cobertura da dimensão de tempo
# MAGIC
# MAGIC A `dim_tempo` será a dimensão calendário compartilhada pelas estruturas analíticas da camada Gold.
# MAGIC
# MAGIC Sua cobertura temporal deverá contemplar todas as datas necessárias para representar integralmente as informações disponíveis e permitir as consultas previstas no MVP. Portanto, o intervalo da dimensão não será limitado ao período operacional da empresa.
# MAGIC
# MAGIC Também serão consideradas datas anteriores a esse período quando possuírem relevância analítica. Esse é o caso, por exemplo, das datas de nascimento de empregados e dependentes, necessárias para análises relacionadas à idade e à determinação de custos associados às faixas etárias dos planos de saúde.
# MAGIC
# MAGIC Para estabelecer os limites da `dim_tempo`, serão consideradas as datas analiticamente relevantes existentes nas tabelas Silver:
# MAGIC
# MAGIC - nascimento, admissão e desligamento dos empregados;
# MAGIC - nascimento dos dependentes;
# MAGIC - alterações salariais;
# MAGIC - início das alocações;
# MAGIC - datas relacionadas aos períodos aquisitivos, avisos, limites e períodos de gozo das férias;
# MAGIC - emissão, competência e vencimento do faturamento;
# MAGIC - competência das despesas com fornecedores.
# MAGIC
# MAGIC As datas de admissão e desligamento dos empregados, além de participarem da definição da cobertura temporal, são utilizadas pela `dim_empregado` por meio das chaves `id_tempo_admissao` e `id_tempo_desligamento`. Dessa forma, a mesma `dim_tempo` desempenha diferentes papéis temporais e permite apoiar análises de admissões, desligamentos, tempo de empresa e turnover.
# MAGIC
# MAGIC Para vínculos ativos, cuja data de desligamento é inexistente, `id_tempo_desligamento` permanece nulo na `dim_empregado`, representando corretamente a ausência de encerramento do vínculo.
# MAGIC
# MAGIC A tabela de benefícios não possui histórico próprio de alterações. Os valores disponíveis representam o último valor conhecido dos benefícios do titular. Sua referência temporal é determinada pelo vínculo do empregado, cujas datas de admissão e desligamento já são consideradas na definição da cobertura da `dim_tempo`.
# MAGIC
# MAGIC Os custos relacionados aos dependentes são tratados separadamente dos benefícios do titular. Para essas análises, além do período correspondente ao vínculo do empregado, a data de nascimento do dependente é necessária para determinar sua idade e a respectiva faixa etária utilizada no cálculo do custo do plano de saúde.
# MAGIC
# MAGIC Dessa forma, benefícios e custos relacionados aos dependentes não exigem a criação de novas datas artificiais: suas necessidades temporais são atendidas pelas datas já existentes nas entidades de empregados e dependentes.
# MAGIC
# MAGIC Nesta etapa serão identificadas a menor e a maior data existentes no conjunto dessas referências temporais. Esses limites serão utilizados posteriormente para gerar o calendário completo da `dim_tempo`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH datas_relevantes AS (
# MAGIC
# MAGIC     -- Empregados
# MAGIC     SELECT data_nascimento AS data
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_admissao
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_desligamento
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     -- Dependentes
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_nascimento
# MAGIC     FROM workspace.silver.dependentes_anonimizados
# MAGIC
# MAGIC     -- Salários
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_alteracao
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC
# MAGIC     -- Alocações
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio
# MAGIC     FROM workspace.silver.alocacao_anonimizado
# MAGIC
# MAGIC     -- Férias
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_periodo_aquisitivo
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_periodo_aquisitivo
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_limite_aviso
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_limite_inicio
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_aviso
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_1
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_1
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_2
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_2
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_3
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_3
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     -- Faturamento
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_emissao
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_competencia
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_vencimento
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     -- Fornecedores
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT competencia
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     MIN(data) AS menor_data,
# MAGIC     MAX(data) AS maior_data,
# MAGIC     COUNT(*) AS total_ocorrencias_datas,
# MAGIC     COUNT(DISTINCT data) AS datas_distintas
# MAGIC FROM datas_relevantes
# MAGIC WHERE data IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC # 1. Conclusão da Definição da cobertura da dimensão de tempo
# MAGIC
# MAGIC O levantamento das referências temporais disponíveis nas tabelas Silver identificou como limites atuais dos dados:
# MAGIC
# MAGIC - **menor data:** 05/11/1932;
# MAGIC - **maior data:** 02/03/2026.
# MAGIC
# MAGIC Esses limites refletem o conjunto de dados atualmente disponível no MVP. Em um ambiente corporativo com maior volume e diversidade de registros, seria esperada uma quantidade maior de ocorrências distribuídas ao longo desse intervalo e a dimensão poderia ser estendida sempre que novos dados ultrapassassem seus limites.
# MAGIC
# MAGIC A `dim_tempo` não será composta somente pelas datas efetivamente encontradas nas fontes. Será gerado um calendário contínuo contendo **todos os dias entre 05/11/1932 e 02/03/2026**, garantindo que qualquer evento compreendido nesse intervalo possa ser relacionado à dimensão.
# MAGIC
# MAGIC A granularidade definida será de **uma linha por dia**.
# MAGIC
# MAGIC A dimensão será composta pelos seguintes atributos:
# MAGIC
# MAGIC - `id_tempo`: chave substituta da dimensão;
# MAGIC - `data`: data completa representada pela linha;
# MAGIC - `dia`: dia do mês;
# MAGIC - `mes`: mês;
# MAGIC - `ano`: ano.
# MAGIC
# MAGIC Essa estrutura permitirá que as diferentes referências temporais existentes no modelo utilizem uma dimensão comum e possibilitará análises em diferentes níveis de agregação, especialmente por dia, mês e ano.
# MAGIC
# MAGIC A granularidade diária também será relevante para análises financeiras, particularmente para o fluxo financeiro previsto, permitindo utilizar as datas disponíveis nas estruturas financeiras e posteriormente consolidar os valores segundo diferentes períodos.
# MAGIC
# MAGIC Com isso, ficam definidos a cobertura, a granularidade e os atributos da `dim_tempo`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Construção da dimensão de tempo
# MAGIC
# MAGIC Com base nos limites e na granularidade definidos na etapa anterior, será criada a tabela `workspace.gold.dim_tempo`.
# MAGIC
# MAGIC A dimensão será gerada como um calendário contínuo entre **05/11/1932 e 02/03/2026**, contendo uma linha para cada dia do intervalo.
# MAGIC
# MAGIC Para cada data serão derivados o dia, o mês e o ano. Também será criada a chave substituta `id_tempo`, que permitirá às demais estruturas da camada Gold referenciar uma mesma data em diferentes contextos analíticos.
# MAGIC
# MAGIC Nesta etapa será realizada apenas a criação da dimensão. Sua integridade e cobertura temporal serão verificadas posteriormente.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.dim_tempo AS
# MAGIC
# MAGIC WITH datas_relevantes AS (
# MAGIC
# MAGIC     -- Empregados
# MAGIC     SELECT data_nascimento AS data
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_admissao
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_desligamento
# MAGIC     FROM workspace.silver.empregados_anonimizados
# MAGIC
# MAGIC     -- Dependentes
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_nascimento
# MAGIC     FROM workspace.silver.dependentes_anonimizados
# MAGIC
# MAGIC     -- Salários
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_alteracao
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC
# MAGIC     -- Alocações
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio
# MAGIC     FROM workspace.silver.alocacao_anonimizado
# MAGIC
# MAGIC     -- Férias
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_periodo_aquisitivo
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_periodo_aquisitivo
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_limite_aviso
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_limite_inicio
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_aviso
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_1
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_1
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_2
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_2
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_inicio_3
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_termino_3
# MAGIC     FROM workspace.silver.ferias_anonimizado
# MAGIC
# MAGIC     -- Faturamento
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_emissao
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_competencia
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT data_vencimento
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC
# MAGIC     -- Fornecedores
# MAGIC     UNION ALL
# MAGIC
# MAGIC     SELECT competencia
# MAGIC     FROM workspace.silver.fornecedor_anonimizado
# MAGIC ),
# MAGIC
# MAGIC limites AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         MIN(data) AS menor_data,
# MAGIC         MAX(data) AS maior_data
# MAGIC     FROM datas_relevantes
# MAGIC     WHERE data IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC calendario AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 menor_data,
# MAGIC                 maior_data,
# MAGIC                 INTERVAL 1 DAY
# MAGIC             )
# MAGIC         ) AS data
# MAGIC     FROM limites
# MAGIC ),
# MAGIC
# MAGIC tempo_identificado AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         ROW_NUMBER() OVER (ORDER BY data) AS id_tempo,
# MAGIC         data,
# MAGIC         DAY(data) AS dia,
# MAGIC         MONTH(data) AS mes,
# MAGIC         YEAR(data) AS ano
# MAGIC     FROM calendario
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     id_tempo,
# MAGIC     data,
# MAGIC     dia,
# MAGIC     mes,
# MAGIC     ano
# MAGIC FROM tempo_identificado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Validação da dimensão de tempo
# MAGIC
# MAGIC Após a construção da tabela `workspace.gold.dim_tempo`, será realizada a validação de sua estrutura e de sua cobertura temporal.
# MAGIC
# MAGIC A verificação tem como objetivos confirmar:
# MAGIC
# MAGIC - a existência de um identificador único para cada data;
# MAGIC - a inexistência de datas duplicadas;
# MAGIC - a inexistência de valores nulos nos atributos da dimensão;
# MAGIC - a correspondência entre a menor e a maior data da dimensão e os limites identificados automaticamente nas fontes Silver;
# MAGIC - a continuidade diária do calendário, garantindo que não existam datas ausentes entre os limites da dimensão;
# MAGIC - a consistência dos atributos `dia`, `mes` e `ano` em relação à coluna `data`.
# MAGIC
# MAGIC Como a granularidade definida para a `dim_tempo` é de uma linha por dia, o número de registros deverá corresponder exatamente à quantidade de dias compreendidos entre a menor e a maior data, incluindo ambas.
# MAGIC
# MAGIC Essa validação permitirá confirmar que a dimensão pode ser utilizada como referência temporal comum pelas demais estruturas da camada Gold.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH validacao AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_registros,
# MAGIC         COUNT(DISTINCT id_tempo) AS ids_distintos,
# MAGIC         COUNT(DISTINCT data) AS datas_distintas,
# MAGIC
# MAGIC         SUM(
# MAGIC             CASE
# MAGIC                 WHEN id_tempo IS NULL
# MAGIC                   OR data IS NULL
# MAGIC                   OR dia IS NULL
# MAGIC                   OR mes IS NULL
# MAGIC                   OR ano IS NULL
# MAGIC                 THEN 1 ELSE 0
# MAGIC             END
# MAGIC         ) AS registros_com_nulos,
# MAGIC
# MAGIC         SUM(
# MAGIC             CASE
# MAGIC                 WHEN dia <> DAY(data)
# MAGIC                   OR mes <> MONTH(data)
# MAGIC                   OR ano <> YEAR(data)
# MAGIC                 THEN 1 ELSE 0
# MAGIC             END
# MAGIC         ) AS atributos_data_inconsistentes,
# MAGIC
# MAGIC         MIN(data) AS menor_data,
# MAGIC         MAX(data) AS maior_data
# MAGIC
# MAGIC     FROM workspace.gold.dim_tempo
# MAGIC ),
# MAGIC
# MAGIC resultado AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         DATEDIFF(maior_data, menor_data) + 1 AS dias_esperados
# MAGIC     FROM validacao
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     total_registros,
# MAGIC     ids_distintos,
# MAGIC     datas_distintas,
# MAGIC     dias_esperados,
# MAGIC     registros_com_nulos,
# MAGIC     atributos_data_inconsistentes,
# MAGIC     menor_data,
# MAGIC     maior_data,
# MAGIC     CASE
# MAGIC         WHEN total_registros = dias_esperados
# MAGIC          AND datas_distintas = dias_esperados
# MAGIC         THEN 0
# MAGIC         ELSE 1
# MAGIC     END AS falha_continuidade
# MAGIC
# MAGIC FROM resultado;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Validação da dimensão de tempo
# MAGIC
# MAGIC A validação da tabela `workspace.gold.dim_tempo` confirmou a integridade da dimensão e sua cobertura contínua ao longo de todo o intervalo definido a partir das referências temporais existentes nas tabelas Silver.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **34.086 registros**;
# MAGIC - **34.086 identificadores distintos** em `id_tempo`;
# MAGIC - **34.086 datas distintas**;
# MAGIC - **34.086 dias esperados** entre a menor e a maior data;
# MAGIC - **0 registros com valores nulos**;
# MAGIC - **0 inconsistências** entre os atributos `data`, `dia`, `mes` e `ano`;
# MAGIC - **0 falhas de continuidade** no calendário.
# MAGIC
# MAGIC A menor data registrada na dimensão é **05/11/1932** e a maior é **02/03/2026**, correspondendo aos limites identificados a partir dos dados atualmente disponíveis nas tabelas Silver.
# MAGIC
# MAGIC A igualdade entre o número de registros, o número de datas distintas e a quantidade de dias esperados confirma que a granularidade definida de **uma linha por dia** foi atendida e que não existem lacunas no calendário.
# MAGIC
# MAGIC Os limites da dimensão são determinados dinamicamente a partir das datas disponíveis nas fontes Silver. Dessa forma, caso novos dados ampliem a cobertura temporal e o processo seja novamente executado, a `dim_tempo` será reconstruída considerando automaticamente os novos limites, sem necessidade de alteração manual das datas no código.
# MAGIC
# MAGIC A dimensão fornece, assim, uma referência temporal comum para as diferentes estruturas analíticas da camada Gold, permitindo análises por dia, mês e ano e possibilitando que diferentes eventos do modelo sejam relacionados ao mesmo calendário.
# MAGIC
# MAGIC Dessa forma, a construção e a validação da `dim_tempo` são consideradas concluídas.