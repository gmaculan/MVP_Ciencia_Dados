# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição do grão e dos componentes da Fato_Custo_Pessoal
# MAGIC
# MAGIC A `Fato_Custo_Pessoal` terá como objetivo consolidar os custos diretamente associados a cada vínculo empregatício ao longo do tempo, permitindo analisar a evolução do custo dos profissionais e sua posterior associação às respectivas alocações.
# MAGIC
# MAGIC ## Grão da fato
# MAGIC
# MAGIC O grão da `Fato_Custo_Pessoal` será:
# MAGIC
# MAGIC **uma linha por DRT por ano.**
# MAGIC
# MAGIC O DRT identifica um vínculo empregatício específico, enquanto o CPF identifica a pessoa. Dessa forma, uma mesma pessoa poderá possuir diferentes DRTs quando houver desligamento seguido de posterior recontratação.
# MAGIC
# MAGIC Cada vínculo será tratado de forma independente. O primeiro DRT representará os custos correspondentes ao primeiro vínculo até seu desligamento, enquanto uma eventual recontratação será representada por um novo DRT a partir da respectiva data de admissão.
# MAGIC
# MAGIC Somente serão gerados registros para os anos compreendidos no período de existência de cada vínculo.
# MAGIC
# MAGIC ## Componentes do custo
# MAGIC
# MAGIC Os custos diretamente associados ao empregado serão organizados em três grupos analíticos:
# MAGIC
# MAGIC ### Remuneração
# MAGIC
# MAGIC - `salario`: remuneração do empregado aplicável ao período considerado.
# MAGIC
# MAGIC ### Benefícios
# MAGIC
# MAGIC - `tr`: ticket refeição;
# MAGIC - `ta`: ticket alimentação;
# MAGIC - `plano_saude`: custo do plano de saúde do titular;
# MAGIC - `total_beneficios`: soma dos benefícios considerados para apenas o titular.
# MAGIC
# MAGIC O total de benefícios será calculado como:
# MAGIC
# MAGIC **Total Benefícios = TR + TA + Plano Saúde Titular**
# MAGIC
# MAGIC Os custos dos dependentes, quando houver, não serão incluídos na `Fato_Custo_Pessoal`.
# MAGIC
# MAGIC ### Encargos
# MAGIC
# MAGIC - `ferias`: provisão mensal do custo de férias;
# MAGIC - `decimo_terceiro`: provisão mensal do 13º salário;
# MAGIC - `fgts`: custo mensal de FGTS;
# MAGIC - `total_encargos`: soma dos encargos considerados no MVP.
# MAGIC
# MAGIC Para fins do MVP, serão adotadas as seguintes simplificações:
# MAGIC
# MAGIC **Férias = (Salário + 1/3 do Salário) / 12**
# MAGIC
# MAGIC **13º salário = Salário / 12**
# MAGIC
# MAGIC O FGTS será calculado utilizando a alíquota aplicável sobre as verbas consideradas na sua base de cálculo.
# MAGIC
# MAGIC O projeto utilizará essas provisões para representar uma fotografia mensal do custo do empregado em cada ano, evitando registrar em um único mês todo o custo anual de férias ou de 13º salário.
# MAGIC
# MAGIC ### Custo total do empregado
# MAGIC
# MAGIC O custo total diretamente associado ao titular será calculado como:
# MAGIC
# MAGIC **Custo Total Empregado = Salário + Total Benefícios + Total Encargos**
# MAGIC
# MAGIC Dessa forma, a fato permitirá analisar separadamente remuneração, benefícios e encargos, além do custo total do vínculo.
# MAGIC
# MAGIC ## Tratamento temporal
# MAGIC
# MAGIC A utilização do ano no grão é necessária porque os componentes do custo podem variar ao longo do vínculo.
# MAGIC
# MAGIC No contexto do MVP, devem ser consideradas especialmente:
# MAGIC
# MAGIC - alterações de salário e benefícios;
# MAGIC - alterações dos valores dos planos de saúde;
# MAGIC - mudança de faixa etária do titular;
# MAGIC - admissão e desligamento do empregado.
# MAGIC
# MAGIC As datas de vigência disponíveis nas fontes serão utilizadas para determinar os valores aplicáveis a cada período. Quando houver alterações dentro do mesmo ano, o cálculo deverá respeitar os diferentes valores vigentes ao longo desse ano para produzir a representação de custo correspondente.
# MAGIC
# MAGIC As limitações históricas das fontes serão preservadas. Valores inexistentes não serão criados ou inferidos artificialmente.
# MAGIC
# MAGIC ## Dependentes
# MAGIC
# MAGIC Os custos dos dependentes serão tratados separadamente em uma futura `Fato_Dependentes`.
# MAGIC
# MAGIC A `Fato_Custo_Pessoal` conterá exclusivamente os custos diretamente associados ao titular do vínculo. Portanto, os custos de plano de saúde dos dependentes não integrarão `total_beneficios`, `total_encargos` ou `custo_total_empregado`.
# MAGIC
# MAGIC Na análise conjunta das duas fatos será possível calcular posteriormente o custo global associado ao profissional:
# MAGIC
# MAGIC **Custo Global = Custo Total Empregado + Custo dos Dependentes**
# MAGIC
# MAGIC Essa separação evita duplicação de custos e preserva o grão específico de cada fato.
# MAGIC
# MAGIC ## Estrutura conceitual
# MAGIC
# MAGIC A estrutura inicialmente prevista para a `Fato_Custo_Pessoal` é:
# MAGIC
# MAGIC `DRT | Nome | Ano | Salário | TR | TA | Plano Saúde | Total Benefícios | Férias | 13º | FGTS | Total Encargos | Custo Total Empregado`
# MAGIC
# MAGIC A construção da `Fato_Custo_Pessoal` utilizará as informações já tratadas e validadas na camada Silver, combinando os históricos e valores disponíveis de empregados, salários, benefícios e demais referências necessárias ao cálculo dos custos. As regras temporais e as limitações identificadas durante a construção da Silver serão preservadas na modelagem Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Definição do cálculo do custo mensal médio anual
# MAGIC
# MAGIC A `Fato_Custo_Pessoal` terá uma linha para cada combinação de **DRT e ano**, e suas medidas representarão o **custo mensal médio do vínculo naquele ano**.
# MAGIC
# MAGIC Essa abordagem permite representar, em uma única linha anual, alterações de valores ocorridas durante o próprio ano, sem perder seus efeitos sobre o custo médio do empregado.
# MAGIC
# MAGIC Para cada componente de custo que possuir variação temporal, serão considerados os valores vigentes durante o período correspondente. O valor registrado na fato será obtido pela média dos valores mensais aplicáveis ao vínculo naquele ano.
# MAGIC
# MAGIC Por exemplo, caso determinado salário permaneça vigente durante oito meses e seja alterado nos quatro meses seguintes, o salário registrado para aquele DRT e ano corresponderá à média mensal ponderada pelos respectivos períodos de vigência.
# MAGIC
# MAGIC O mesmo princípio será aplicado aos demais componentes sempre que houver informação temporal suficiente para determinar suas vigências.
# MAGIC
# MAGIC Nos anos de admissão e desligamento, serão considerados apenas os meses pertencentes ao período efetivo do vínculo. Dessa forma, um empregado que tenha permanecido seis meses na empresa durante determinado ano terá seu custo mensal médio calculado sobre esses seis meses, e não sobre os doze meses do ano.
# MAGIC
# MAGIC A partir dos valores mensais médios serão calculados os seguintes grupos:
# MAGIC
# MAGIC ### Benefícios
# MAGIC
# MAGIC **Total Benefícios = TR + TA + Plano Saúde Titular**
# MAGIC
# MAGIC Os custos dos dependentes permanecerão fora desta fato e serão tratados posteriormente na `Fato_Dependentes`.
# MAGIC
# MAGIC ### Encargos
# MAGIC
# MAGIC Para fins do MVP, serão utilizadas as seguintes provisões mensais:
# MAGIC
# MAGIC **Férias = (Salário + 1/3 do Salário) / 12**
# MAGIC
# MAGIC **13º salário = Salário / 12**
# MAGIC
# MAGIC O FGTS será calculado à alíquota de **8%**, considerando as verbas definidas como integrantes de sua base de cálculo.
# MAGIC
# MAGIC **Total Encargos = Férias + 13º + FGTS**
# MAGIC
# MAGIC ### Custo total
# MAGIC
# MAGIC O custo mensal médio do empregado será calculado como:
# MAGIC
# MAGIC **Custo Total Empregado = Salário + Total Benefícios + Total Encargos**
# MAGIC
# MAGIC Dessa forma, cada registro da `Fato_Custo_Pessoal` representará uma fotografia do **custo mensal médio do respectivo vínculo em determinado ano**, preservando separadamente remuneração, benefícios e encargos.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(COALESCE(e.data_desligamento, MAKE_DATE(l.ultimo_ano_disponivel, 12, 31))),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 ano_inicial,
# MAGIC                 ano_final
# MAGIC             )
# MAGIC         ) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano,
# MAGIC     data_admissao,
# MAGIC     data_desligamento,
# MAGIC
# MAGIC     GREATEST(
# MAGIC         data_admissao,
# MAGIC         MAKE_DATE(ano, 1, 1)
# MAGIC     ) AS inicio_periodo_ano,
# MAGIC
# MAGIC     LEAST(
# MAGIC         COALESCE(data_desligamento, MAKE_DATE(ano, 12, 31)),
# MAGIC         MAKE_DATE(ano, 12, 31)
# MAGIC     ) AS fim_periodo_ano
# MAGIC
# MAGIC FROM drt_ano
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Definição do cálculo do custo mensal médio anual
# MAGIC
# MAGIC A base temporal da `Fato_Custo_Pessoal` foi estruturada no grão definido para o projeto: **uma linha por DRT por ano**.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **1.158 registros DRT × ano**;
# MAGIC - **347 DRTs distintos**;
# MAGIC - **1.158 combinações distintas de DRT e ano**, confirmando ausência de duplicidade no grão;
# MAGIC - período compreendido entre **2000 e 2024**.
# MAGIC
# MAGIC Para cada combinação de DRT e ano foram determinadas as datas `inicio_periodo_ano` e `fim_periodo_ano`.
# MAGIC
# MAGIC Nos anos intermediários de um vínculo, o período corresponde ao ano completo. Nos anos de admissão ou desligamento, o período foi limitado pelas respectivas datas, permitindo posteriormente calcular os custos considerando somente a parcela do ano em que o vínculo efetivamente existiu.
# MAGIC
# MAGIC Para os vínculos sem data de desligamento, a geração dos anos foi limitada ao último ano disponível no histórico salarial, evitando a criação de períodos posteriores à cobertura temporal dos dados utilizados no MVP.
# MAGIC
# MAGIC A estrutura obtida constitui a base temporal sobre a qual serão incorporados os componentes do custo do empregado.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Cálculo do salário mensal médio por DRT e ano
# MAGIC
# MAGIC O primeiro componente incorporado à base da `Fato_Custo_Pessoal` será o salário.
# MAGIC
# MAGIC A tabela Silver de salários contém o histórico das alterações salariais de cada DRT. Portanto, um mesmo vínculo pode possuir diferentes valores de salário dentro de determinado ano.
# MAGIC
# MAGIC Para manter o grão **DRT × ano**, será calculado o salário mensal médio aplicável ao vínculo naquele ano.
# MAGIC
# MAGIC O cálculo considerará, para cada mês pertencente ao período efetivo do vínculo, o último salário cuja `data_alteracao` seja anterior ou igual ao respectivo mês. Dessa forma, uma alteração salarial ocorrida durante o vínculo passa a produzir efeito a partir de sua vigência, enquanto o valor anterior permanece associado aos meses anteriores.
# MAGIC
# MAGIC Nos anos de admissão ou desligamento serão considerados somente os meses compreendidos no período efetivo do vínculo.
# MAGIC
# MAGIC Após a determinação dos valores mensais aplicáveis, será calculada a média desses valores para cada combinação de DRT e ano.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     -- Estagiários possuem DRT com mais de 3 dígitos
# MAGIC     -- e não fazem parte do escopo da Fato_Custo_Pessoal
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 ano_inicial,
# MAGIC                 ano_final
# MAGIC             )
# MAGIC         ) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano,
# MAGIC     MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC     MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC     COUNT(*) AS meses_vinculo,
# MAGIC     ROUND(AVG(salario_mes), 2) AS salario_medio_mensal
# MAGIC
# MAGIC FROM salario_mensal
# MAGIC
# MAGIC GROUP BY
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão do Cálculo do salário mensal médio por DRT e ano
# MAGIC
# MAGIC O salário mensal médio foi calculado para cada combinação de DRT e ano, respeitando o período efetivo de cada vínculo e as alterações salariais registradas na camada Silver.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma duplicidade de DRT e ano;
# MAGIC - nenhum salário mensal médio nulo;
# MAGIC - nenhum período anual inconsistente.
# MAGIC
# MAGIC Os vínculos identificados como estagiários foram excluídos do escopo da `Fato_Custo_Pessoal`. Para o MVP, foi adotado como regra de identificação o DRT com mais de três dígitos. Após a aplicação desse critério, todos os DRTs mantidos possuem até três dígitos.
# MAGIC
# MAGIC Para cada mês do período efetivo do vínculo foi considerado o último salário disponível até aquele mês. Em seguida, os valores mensais foram utilizados para determinar o salário mensal médio correspondente ao DRT no respectivo ano.
# MAGIC
# MAGIC Nos anos de admissão e desligamento, foram considerados somente os meses pertencentes ao período efetivo do vínculo.
# MAGIC
# MAGIC Dessa forma, `salario_medio_mensal` passa a representar a remuneração mensal média do vínculo em cada ano e constitui o primeiro componente de custo da `Fato_Custo_Pessoal`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Incorporação dos benefícios TR e TA
# MAGIC
# MAGIC Nesta etapa serão incorporados à base da `Fato_Custo_Pessoal` os benefícios de ticket refeição (`TR`) e ticket alimentação (`TA`).
# MAGIC
# MAGIC Os valores históricos desses benefícios estão disponíveis na tabela de referência `workspace.bronze.valor_ticket_2010_2025`, organizada por períodos de Convenção Coletiva de Trabalho (CCT).
# MAGIC
# MAGIC Como as vigências das CCTs não coincidem integralmente com o ano civil, os valores de TR e TA serão determinados inicialmente para cada mês do vínculo. Para o MVP, será considerada a mudança de referência em **setembro**, de forma que cada período de CCT seja aplicado de setembro do ano inicial até agosto do ano seguinte.
# MAGIC
# MAGIC Assim, um mesmo DRT poderá possuir dois valores diferentes de TR e TA dentro de determinado ano. Após a determinação do valor aplicável a cada mês, será calculada a média mensal correspondente a cada combinação de **DRT e ano**, mantendo o mesmo critério temporal utilizado para o salário.
# MAGIC
# MAGIC Nos anos de admissão ou desligamento serão considerados somente os meses pertencentes ao período efetivo do vínculo.
# MAGIC
# MAGIC Como a referência histórica disponível para os tickets tem início em **2010**, não serão criados valores para períodos anteriores à cobertura da fonte. Nesses casos, TR e TA permanecerão sem valor.
# MAGIC
# MAGIC A tabela Silver de benefícios não será utilizada para reconstruir o histórico de TR e TA, pois seus valores representam o último conjunto de benefícios disponível para cada vínculo e não as alterações históricas desses benefícios.
# MAGIC
# MAGIC Nesta etapa não serão incorporados o plano de saúde do titular nem os custos dos dependentes. O plano de saúde será tratado separadamente, utilizando as regras de vigência, plano e faixa etária disponíveis na `dim_saude`.
# MAGIC
# MAGIC Ao final desta etapa, a base anual passará a conter:
# MAGIC
# MAGIC - `salario_medio_mensal`;
# MAGIC - `tr_medio_mensal`;
# MAGIC - `ta_medio_mensal`.
# MAGIC
# MAGIC Os valores de TR e TA representarão, portanto, o **custo mensal médio de cada benefício para o respectivo DRT no ano analisado**.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(data_desligamento, MAKE_DATE(ano, 12, 31)),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_mensais AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano,
# MAGIC     MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC     MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC     COUNT(*) AS meses_vinculo,
# MAGIC
# MAGIC     ROUND(AVG(salario_mes), 2) AS salario_medio_mensal,
# MAGIC     ROUND(AVG(tr), 2) AS tr_medio_mensal,
# MAGIC     ROUND(AVG(ta), 2) AS ta_medio_mensal
# MAGIC
# MAGIC FROM custos_mensais
# MAGIC
# MAGIC GROUP BY
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Incorporação dos benefícios TR e TA
# MAGIC
# MAGIC Os valores de ticket refeição (`TR`) e ticket alimentação (`TA`) foram incorporados à base da `Fato_Custo_Pessoal` considerando o histórico disponível das Convenções Coletivas de Trabalho (CCT).
# MAGIC
# MAGIC Foram mantidos:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma duplicidade de DRT e ano;
# MAGIC - nenhum salário mensal médio nulo.
# MAGIC
# MAGIC Os valores de TR e TA foram determinados mensalmente conforme a referência de CCT aplicável a cada período e, posteriormente, utilizados para calcular o custo mensal médio de cada benefício por DRT e ano.
# MAGIC
# MAGIC Nos anos em que ocorre mudança de CCT, a média anual reflete os diferentes valores aplicáveis aos meses do vínculo. Nos anos de admissão ou desligamento, são considerados somente os meses pertencentes ao período efetivo do vínculo.
# MAGIC
# MAGIC Foram identificados **31 registros com TR e TA sem valor**, todos pertencentes a períodos anteriores a 2010. Esses valores foram preservados como `NULL`, pois a fonte histórica disponível para os tickets começa em 2010 e não serão criados valores não existentes na origem.
# MAGIC
# MAGIC Dessa forma, `tr_medio_mensal` e `ta_medio_mensal` passam a representar o custo mensal médio histórico desses benefícios para cada DRT no respectivo ano.
# MAGIC
# MAGIC O plano de saúde do titular permanece fora desta etapa e será incorporado separadamente, utilizando as referências de vigência, plano e faixa etária disponíveis na `dim_saude`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Incorporação do plano de saúde do titular
# MAGIC
# MAGIC Nesta etapa será incorporado à `Fato_Custo_Pessoal` o custo do plano de saúde do empregado titular.
# MAGIC
# MAGIC A tabela Silver de benefícios não registra diretamente a identificação do plano de saúde do empregado como `ESPECIAL` ou `EXECUTIVO`. O campo `plano_saude` contém o último valor monetário disponível do plano associado ao DRT.
# MAGIC
# MAGIC Por esse motivo, antes do cálculo histórico será necessário relacionar os valores registrados para os titulares às referências disponíveis na `dim_saude`, de forma a identificar como esses valores correspondem aos planos e às respectivas faixas etárias.
# MAGIC
# MAGIC Após essa identificação, o custo histórico do plano de saúde será determinado mensalmente considerando:
# MAGIC
# MAGIC - o plano associado ao empregado;
# MAGIC - a idade do empregado em cada mês, calculada a partir de sua data de nascimento;
# MAGIC - a faixa etária correspondente;
# MAGIC - a referência de valores vigente no período;
# MAGIC - o IOF aplicável à respectiva referência.
# MAGIC
# MAGIC Dessa forma, alterações de faixa etária e mudanças nos valores dos planos poderão produzir diferentes custos dentro de um mesmo ano.
# MAGIC
# MAGIC Após a determinação do custo aplicável em cada mês do vínculo, será calculado o custo mensal médio do plano de saúde do titular para cada combinação de **DRT e ano**, mantendo o mesmo critério temporal utilizado para salário, TR e TA.
# MAGIC
# MAGIC Os custos dos planos de saúde dos dependentes não serão incorporados nesta fato. Eles serão tratados posteriormente na `Fato_Dependentes`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     mes_ref,
# MAGIC     `24-10-22`
# MAGIC
# MAGIC FROM workspace.gold.dim_saude
# MAGIC
# MAGIC ORDER BY ordem_historico;

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Incorporação do plano de saúde do titular
# MAGIC
# MAGIC Nesta etapa será incorporado à `Fato_Custo_Pessoal` o custo do plano de saúde do empregado titular.
# MAGIC
# MAGIC Para o MVP, todos os empregados e seus dependentes estão associados ao plano `ESPECIAL`. Portanto, não será necessário inferir o tipo de plano a partir do valor registrado na tabela Silver de benefícios.
# MAGIC
# MAGIC Embora a `dim_saude` preserve também as referências do plano `EXECUTIVO`, esses valores não serão utilizados no cálculo dos custos de saúde dos empregados e dependentes considerados no projeto.
# MAGIC
# MAGIC O custo do plano de saúde do titular será determinado mensalmente considerando:
# MAGIC
# MAGIC - a data de nascimento do empregado;
# MAGIC - sua idade no mês analisado;
# MAGIC - a faixa etária correspondente;
# MAGIC - o plano `ESPECIAL`;
# MAGIC - a referência de valores vigente naquele mês;
# MAGIC - o IOF aplicável à respectiva referência.
# MAGIC
# MAGIC Dessa forma, alterações de faixa etária e mudanças nos valores do plano poderão produzir diferentes custos dentro de um mesmo ano.
# MAGIC
# MAGIC Após a determinação do custo aplicável em cada mês do vínculo, será calculado o custo mensal médio do plano de saúde do titular para cada combinação de **DRT e ano**, mantendo o mesmo critério temporal utilizado para salário, TR e TA.
# MAGIC
# MAGIC Os custos dos planos de saúde dos dependentes não serão incorporados nesta fato. Eles serão tratados posteriormente na `Fato_Dependentes`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_com_tickets AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC ),
# MAGIC
# MAGIC saude_long AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         mes_ref,
# MAGIC         ordem_historico,
# MAGIC         referencia,
# MAGIC         valor
# MAGIC
# MAGIC     FROM workspace.gold.dim_saude
# MAGIC
# MAGIC     UNPIVOT (
# MAGIC         valor FOR referencia IN (
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
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC
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
# MAGIC
# MAGIC         CAST(TRIM(mes_ref) AS INT) AS idade_inicial,
# MAGIC
# MAGIC         TRY_CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     REPLACE(TRIM(valor), 'R$', ''),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             )
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC
# MAGIC     FROM saude_long
# MAGIC
# MAGIC     WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC       AND TRIM(mes_ref) IN (
# MAGIC           '0', '19', '24', '29', '34',
# MAGIC           '39', '44', '49', '54', '59'
# MAGIC       )
# MAGIC ),
# MAGIC
# MAGIC saude_com_faixa AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC         data_vigencia,
# MAGIC         idade_inicial,
# MAGIC
# MAGIC         LEAD(idade_inicial, 1, 999)
# MAGIC             OVER (
# MAGIC                 PARTITION BY referencia
# MAGIC                 ORDER BY idade_inicial
# MAGIC             ) - 1 AS idade_final,
# MAGIC
# MAGIC         valor_base
# MAGIC
# MAGIC     FROM vigencias_saude
# MAGIC ),
# MAGIC
# MAGIC custos_com_saude AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         c.*,
# MAGIC
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(
# MAGIC                 LAST_DAY(c.mes_referencia),
# MAGIC                 c.data_nascimento
# MAGIC             ) / 12
# MAGIC         ) AS idade_mes,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(
# MAGIC                 s.valor_base * 1.0238,
# MAGIC                 s.data_vigencia
# MAGIC             )
# MAGIC
# MAGIC             FROM saude_com_faixa s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.data_vigencia <= LAST_DAY(c.mes_referencia)
# MAGIC
# MAGIC                 AND FLOOR(
# MAGIC                     MONTHS_BETWEEN(
# MAGIC                         LAST_DAY(c.mes_referencia),
# MAGIC                         c.data_nascimento
# MAGIC                     ) / 12
# MAGIC                 ) BETWEEN s.idade_inicial AND s.idade_final
# MAGIC         ) AS plano_saude_mes
# MAGIC
# MAGIC     FROM custos_com_tickets c
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano,
# MAGIC     MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC     MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC     COUNT(*) AS meses_vinculo,
# MAGIC
# MAGIC     ROUND(AVG(salario_mes), 2) AS salario_medio_mensal,
# MAGIC     ROUND(AVG(tr), 2) AS tr_medio_mensal,
# MAGIC     ROUND(AVG(ta), 2) AS ta_medio_mensal,
# MAGIC     ROUND(AVG(plano_saude_mes), 2) AS plano_saude_medio_mensal
# MAGIC
# MAGIC FROM custos_com_saude
# MAGIC
# MAGIC GROUP BY
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     ano
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 5. Conclusão da Incorporação do plano de saúde do titular
# MAGIC
# MAGIC O custo do plano de saúde do titular foi incorporado à base da `Fato_Custo_Pessoal`, mantendo o grão de **uma linha por DRT por ano**.
# MAGIC
# MAGIC Foram mantidos:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma alteração no grão anteriormente definido;
# MAGIC - nenhum salário mensal médio nulo.
# MAGIC
# MAGIC Para o MVP, foi aplicada a regra de negócio de que todos os empregados e seus dependentes utilizam o plano `ESPECIAL`. As referências do plano `EXECUTIVO` permanecem preservadas na `dim_saude`, mas não são utilizadas no cálculo dos custos dos empregados considerados no projeto.
# MAGIC
# MAGIC O custo do plano de saúde foi determinado mensalmente considerando a data de nascimento do empregado, sua idade no período, a faixa etária correspondente e a última referência de valores disponível na `dim_saude` até o respectivo mês.
# MAGIC
# MAGIC Dessa forma, o cálculo contempla tanto alterações dos valores do plano ao longo do tempo quanto mudanças de faixa etária do titular.
# MAGIC
# MAGIC Após a determinação dos valores mensais aplicáveis, foi calculado `plano_saude_medio_mensal`, representando o custo mensal médio do plano de saúde do titular para cada DRT no respectivo ano.
# MAGIC
# MAGIC Foram identificados **25 registros sem valor de plano de saúde**, todos pertencentes a períodos anteriores ao início da referência histórica disponível na `dim_saude`, em outubro de 2009. Esses registros foram preservados como `NULL`, sem criação de valores inexistentes na fonte.
# MAGIC
# MAGIC Os custos de saúde dos dependentes permanecem fora da `Fato_Custo_Pessoal` e serão tratados posteriormente na `Fato_Dependentes`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Cálculo do total de benefícios do titular
# MAGIC
# MAGIC Nesta etapa será calculado o custo mensal médio total dos benefícios diretamente associados ao empregado titular.
# MAGIC
# MAGIC Para a `Fato_Custo_Pessoal`, serão considerados:
# MAGIC
# MAGIC - ticket refeição (`TR`);
# MAGIC - ticket alimentação (`TA`);
# MAGIC - plano de saúde do titular.
# MAGIC
# MAGIC O cálculo será realizado por meio da soma:
# MAGIC
# MAGIC **Total Benefícios = TR + TA + Plano Saúde Titular**
# MAGIC
# MAGIC O custo do plano de saúde do titular considera o valor-base histórico correspondente à faixa etária e à referência vigente, acrescido do **IOF de 2,38%**, conforme registrado nas referências históricas da `Dim_Saude`.
# MAGIC
# MAGIC Dessa forma:
# MAGIC
# MAGIC **Plano Saúde Titular = Valor-base × 1,0238**
# MAGIC
# MAGIC Esse critério mantém o mesmo tratamento adotado posteriormente para o custo do plano de saúde dos dependentes.
# MAGIC
# MAGIC Como existem períodos históricos anteriores à cobertura das fontes de referência de TR, TA e plano de saúde, a ausência de informação não será interpretada como custo zero.
# MAGIC
# MAGIC Assim, quando algum dos componentes necessários ao cálculo não estiver disponível para determinado DRT e ano, `total_beneficios` permanecerá `NULL`, preservando a distinção entre ausência de custo e ausência de informação.
# MAGIC
# MAGIC Os custos dos dependentes não fazem parte de `total_beneficios` e são tratados separadamente na `Fato_Dependentes`.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_com_tickets AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC ),
# MAGIC
# MAGIC saude_long AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         mes_ref,
# MAGIC         ordem_historico,
# MAGIC         referencia,
# MAGIC         valor
# MAGIC
# MAGIC     FROM workspace.gold.dim_saude
# MAGIC
# MAGIC     UNPIVOT (
# MAGIC         valor FOR referencia IN (
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
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC
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
# MAGIC
# MAGIC         CAST(TRIM(mes_ref) AS INT) AS idade_inicial,
# MAGIC
# MAGIC         TRY_CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     REPLACE(TRIM(valor), 'R$', ''),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             )
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC
# MAGIC     FROM saude_long
# MAGIC
# MAGIC     WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC       AND TRIM(mes_ref) IN (
# MAGIC           '0', '19', '24', '29', '34',
# MAGIC           '39', '44', '49', '54', '59'
# MAGIC       )
# MAGIC ),
# MAGIC
# MAGIC saude_com_faixa AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC         data_vigencia,
# MAGIC         idade_inicial,
# MAGIC
# MAGIC         LEAD(idade_inicial, 1, 999)
# MAGIC             OVER (
# MAGIC                 PARTITION BY referencia
# MAGIC                 ORDER BY idade_inicial
# MAGIC             ) - 1 AS idade_final,
# MAGIC
# MAGIC         valor_base
# MAGIC
# MAGIC     FROM vigencias_saude
# MAGIC ),
# MAGIC
# MAGIC custos_com_saude AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         c.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(
# MAGIC                 s.valor_base * 1.0238,
# MAGIC                 s.data_vigencia
# MAGIC             )
# MAGIC
# MAGIC             FROM saude_com_faixa s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.data_vigencia <= LAST_DAY(c.mes_referencia)
# MAGIC
# MAGIC                 AND FLOOR(
# MAGIC                     MONTHS_BETWEEN(
# MAGIC                         LAST_DAY(c.mes_referencia),
# MAGIC                         c.data_nascimento
# MAGIC                     ) / 12
# MAGIC                 ) BETWEEN s.idade_inicial AND s.idade_final
# MAGIC         ) AS plano_saude_mes
# MAGIC
# MAGIC     FROM custos_com_tickets c
# MAGIC ),
# MAGIC
# MAGIC base_anual AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC         MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC         MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC         COUNT(*) AS meses_vinculo,
# MAGIC
# MAGIC         ROUND(AVG(salario_mes), 2) AS salario_medio_mensal,
# MAGIC         ROUND(AVG(tr), 2) AS tr_medio_mensal,
# MAGIC         ROUND(AVG(ta), 2) AS ta_medio_mensal,
# MAGIC         ROUND(AVG(plano_saude_mes), 2) AS plano_saude_medio_mensal
# MAGIC
# MAGIC     FROM custos_com_saude
# MAGIC
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     *,
# MAGIC
# MAGIC     ROUND(
# MAGIC         tr_medio_mensal
# MAGIC         + ta_medio_mensal
# MAGIC         + plano_saude_medio_mensal,
# MAGIC         2
# MAGIC     ) AS total_beneficios
# MAGIC
# MAGIC FROM base_anual
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 6. Conclusão do Cálculo do total de benefícios do titular
# MAGIC
# MAGIC O custo mensal médio total dos benefícios do titular foi calculado para cada combinação de DRT e ano.
# MAGIC
# MAGIC O cálculo considera:
# MAGIC
# MAGIC **Total Benefícios = TR + TA + Plano Saúde Titular**
# MAGIC
# MAGIC Foram mantidos:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma duplicidade de DRT e ano;
# MAGIC - **1.116 registros com todos os componentes necessários disponíveis e total de benefícios calculado**;
# MAGIC - **31 registros com `total_beneficios` sem valor**.
# MAGIC
# MAGIC Nos 1.116 registros com informação completa, o `total_beneficios` corresponde à soma de `tr_medio_mensal`, `ta_medio_mensal` e `plano_saude_medio_mensal`.
# MAGIC
# MAGIC Os 31 registros sem valor de `total_beneficios` pertencem ao período entre 2000 e 2009 e decorrem da ausência de cobertura histórica de pelo menos um dos componentes utilizados no cálculo.
# MAGIC
# MAGIC Essas ausências foram preservadas como `NULL`, evitando interpretar falta de informação histórica como custo igual a zero.
# MAGIC
# MAGIC Os custos dos dependentes permanecem fora do cálculo de `total_beneficios` e serão tratados posteriormente na `Fato_Dependentes`.
# MAGIC
# MAGIC Com essa etapa, estão consolidados os componentes de benefícios do titular necessários para a composição do custo mensal médio do empregado.

# COMMAND ----------

# MAGIC %md
# MAGIC # 7. Cálculo dos encargos do empregado
# MAGIC
# MAGIC Nesta etapa serão calculados os encargos considerados na `Fato_Custo_Pessoal`.
# MAGIC
# MAGIC Para o MVP, serão considerados:
# MAGIC
# MAGIC - provisão mensal de férias;
# MAGIC - provisão mensal de 13º salário;
# MAGIC - FGTS;
# MAGIC - total de encargos.
# MAGIC
# MAGIC O custo de férias será tratado como uma provisão mensal correspondente ao salário acrescido de um terço constitucional, distribuído ao longo de 12 meses:
# MAGIC
# MAGIC **Férias = (Salário + 1/3 do Salário) / 12**
# MAGIC
# MAGIC O 13º salário será tratado como uma provisão mensal:
# MAGIC
# MAGIC **13º = Salário / 12**
# MAGIC
# MAGIC O FGTS será calculado utilizando a alíquota de **8%**, aplicada sobre o salário e sobre as provisões consideradas de férias e 13º salário:
# MAGIC
# MAGIC **FGTS = 8% × (Salário + Férias + 13º)**
# MAGIC
# MAGIC Por fim:
# MAGIC
# MAGIC **Total Encargos = Férias + 13º + FGTS**
# MAGIC
# MAGIC Como a `Fato_Custo_Pessoal` possui grão **DRT × ano** e representa custos mensais médios, os cálculos serão realizados a partir do `salario_medio_mensal` correspondente a cada vínculo no respectivo ano.
# MAGIC
# MAGIC Esses cálculos constituem simplificações adotadas para o MVP e não têm como objetivo reproduzir integralmente todas as regras trabalhistas e contábeis aplicáveis a uma folha de pagamento real.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_com_tickets AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC ),
# MAGIC
# MAGIC saude_long AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         mes_ref,
# MAGIC         ordem_historico,
# MAGIC         referencia,
# MAGIC         valor
# MAGIC
# MAGIC     FROM workspace.gold.dim_saude
# MAGIC
# MAGIC     UNPIVOT (
# MAGIC         valor FOR referencia IN (
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
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC
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
# MAGIC
# MAGIC         CAST(TRIM(mes_ref) AS INT) AS idade_inicial,
# MAGIC
# MAGIC         TRY_CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     REPLACE(TRIM(valor), 'R$', ''),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             )
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC
# MAGIC     FROM saude_long
# MAGIC
# MAGIC     WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC       AND TRIM(mes_ref) IN (
# MAGIC           '0', '19', '24', '29', '34',
# MAGIC           '39', '44', '49', '54', '59'
# MAGIC       )
# MAGIC ),
# MAGIC
# MAGIC saude_com_faixa AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC         data_vigencia,
# MAGIC         idade_inicial,
# MAGIC
# MAGIC         LEAD(idade_inicial, 1, 999)
# MAGIC             OVER (
# MAGIC                 PARTITION BY referencia
# MAGIC                 ORDER BY idade_inicial
# MAGIC             ) - 1 AS idade_final,
# MAGIC
# MAGIC         valor_base
# MAGIC
# MAGIC     FROM vigencias_saude
# MAGIC ),
# MAGIC
# MAGIC custos_com_saude AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         c.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(
# MAGIC                 s.valor_base * 1.0238,
# MAGIC                 s.data_vigencia
# MAGIC             )
# MAGIC
# MAGIC             FROM saude_com_faixa s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.data_vigencia <= LAST_DAY(c.mes_referencia)
# MAGIC
# MAGIC                 AND FLOOR(
# MAGIC                     MONTHS_BETWEEN(
# MAGIC                         LAST_DAY(c.mes_referencia),
# MAGIC                         c.data_nascimento
# MAGIC                     ) / 12
# MAGIC                 ) BETWEEN s.idade_inicial AND s.idade_final
# MAGIC         ) AS plano_saude_mes
# MAGIC
# MAGIC     FROM custos_com_tickets c
# MAGIC ),
# MAGIC
# MAGIC base_anual AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC         MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC         MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC         COUNT(*) AS meses_vinculo,
# MAGIC
# MAGIC         ROUND(AVG(salario_mes), 2) AS salario_medio_mensal,
# MAGIC         ROUND(AVG(tr), 2) AS tr_medio_mensal,
# MAGIC         ROUND(AVG(ta), 2) AS ta_medio_mensal,
# MAGIC         ROUND(AVG(plano_saude_mes), 2) AS plano_saude_medio_mensal
# MAGIC
# MAGIC     FROM custos_com_saude
# MAGIC
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano
# MAGIC ),
# MAGIC
# MAGIC beneficios AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             tr_medio_mensal
# MAGIC             + ta_medio_mensal
# MAGIC             + plano_saude_medio_mensal,
# MAGIC             2
# MAGIC         ) AS total_beneficios
# MAGIC
# MAGIC     FROM base_anual
# MAGIC ),
# MAGIC
# MAGIC encargos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             (salario_medio_mensal * (4.0 / 3.0)) / 12,
# MAGIC             2
# MAGIC         ) AS ferias,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_medio_mensal / 12,
# MAGIC             2
# MAGIC         ) AS decimo_terceiro
# MAGIC
# MAGIC     FROM beneficios
# MAGIC ),
# MAGIC
# MAGIC encargos_com_fgts AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             0.08 * (
# MAGIC                 salario_medio_mensal
# MAGIC                 + ferias
# MAGIC                 + decimo_terceiro
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS fgts
# MAGIC
# MAGIC     FROM encargos
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     *,
# MAGIC
# MAGIC     ROUND(
# MAGIC         ferias
# MAGIC         + decimo_terceiro
# MAGIC         + fgts,
# MAGIC         2
# MAGIC     ) AS total_encargos
# MAGIC
# MAGIC FROM encargos_com_fgts
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 7. Conclusão do Cálculo dos encargos do empregado
# MAGIC
# MAGIC Os encargos considerados na `Fato_Custo_Pessoal` foram calculados para cada combinação de DRT e ano a partir do salário mensal médio do respectivo vínculo.
# MAGIC
# MAGIC Foram mantidos:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma duplicidade de DRT e ano;
# MAGIC - nenhum valor nulo nos componentes de encargos calculados.
# MAGIC
# MAGIC Para o MVP, foram consideradas as seguintes premissas:
# MAGIC
# MAGIC - férias: provisão mensal correspondente ao salário acrescido de um terço, distribuído ao longo de 12 meses;
# MAGIC - 13º salário: provisão mensal correspondente ao salário dividido por 12;
# MAGIC - FGTS: 8% sobre o salário acrescido das provisões de férias e 13º;
# MAGIC - total de encargos: soma das provisões de férias, 13º e FGTS.
# MAGIC
# MAGIC Os cálculos foram realizados a partir do `salario_medio_mensal`, mantendo a mesma lógica de custo mensal médio adotada para os demais componentes da fato.
# MAGIC
# MAGIC As regras utilizadas constituem simplificações para fins analíticos do MVP e não pretendem reproduzir integralmente todas as regras trabalhistas e contábeis de uma folha de pagamento real.
# MAGIC
# MAGIC Com essa etapa, estão disponíveis os componentes necessários para calcular o custo mensal médio total do empregado.

# COMMAND ----------

# MAGIC %md
# MAGIC # 8. Cálculo do custo total do empregado
# MAGIC
# MAGIC Nesta etapa será calculado o custo mensal médio total do empregado para cada combinação de DRT e ano.
# MAGIC
# MAGIC O cálculo será realizado a partir dos três componentes consolidados nas etapas anteriores:
# MAGIC
# MAGIC - salário mensal médio;
# MAGIC - total de benefícios do titular;
# MAGIC - total de encargos.
# MAGIC
# MAGIC Assim:
# MAGIC
# MAGIC **Custo Total Empregado = Salário + Total Benefícios + Total Encargos**
# MAGIC
# MAGIC Os custos dos dependentes não serão incorporados nesta fato, pois serão tratados posteriormente na `Fato_Dependentes`.
# MAGIC
# MAGIC Para os períodos em que `total_beneficios` permanece `NULL` por ausência de informação histórica nas fontes de benefícios, `custo_total_empregado` também permanecerá `NULL`.
# MAGIC
# MAGIC Essa regra evita interpretar ausência de informação como custo igual a zero e mantém explícita a limitação histórica dos dados disponíveis.
# MAGIC
# MAGIC O resultado continuará representando o **custo mensal médio do vínculo em cada ano**, respeitando o grão definido para a `Fato_Custo_Pessoal` de uma linha por DRT e ano.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_com_tickets AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC ),
# MAGIC
# MAGIC saude_long AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         mes_ref,
# MAGIC         ordem_historico,
# MAGIC         referencia,
# MAGIC         valor
# MAGIC
# MAGIC     FROM workspace.gold.dim_saude
# MAGIC
# MAGIC     UNPIVOT (
# MAGIC         valor FOR referencia IN (
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
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC
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
# MAGIC
# MAGIC         CAST(TRIM(mes_ref) AS INT) AS idade_inicial,
# MAGIC
# MAGIC         TRY_CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     REPLACE(TRIM(valor), 'R$', ''),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             )
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC
# MAGIC     FROM saude_long
# MAGIC
# MAGIC     WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC       AND TRIM(mes_ref) IN (
# MAGIC           '0', '19', '24', '29', '34',
# MAGIC           '39', '44', '49', '54', '59'
# MAGIC       )
# MAGIC ),
# MAGIC
# MAGIC saude_com_faixa AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC         data_vigencia,
# MAGIC         idade_inicial,
# MAGIC
# MAGIC         LEAD(idade_inicial, 1, 999)
# MAGIC             OVER (
# MAGIC                 PARTITION BY referencia
# MAGIC                 ORDER BY idade_inicial
# MAGIC             ) - 1 AS idade_final,
# MAGIC
# MAGIC         valor_base
# MAGIC
# MAGIC     FROM vigencias_saude
# MAGIC ),
# MAGIC
# MAGIC custos_com_saude AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         c.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(
# MAGIC                 s.valor_base * 1.0238,
# MAGIC                 s.data_vigencia
# MAGIC             )
# MAGIC
# MAGIC             FROM saude_com_faixa s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.data_vigencia <= LAST_DAY(c.mes_referencia)
# MAGIC
# MAGIC                 AND FLOOR(
# MAGIC                     MONTHS_BETWEEN(
# MAGIC                         LAST_DAY(c.mes_referencia),
# MAGIC                         c.data_nascimento
# MAGIC                     ) / 12
# MAGIC                 ) BETWEEN s.idade_inicial AND s.idade_final
# MAGIC         ) AS plano_saude_mes
# MAGIC
# MAGIC     FROM custos_com_tickets c
# MAGIC ),
# MAGIC
# MAGIC base_anual AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC         MIN(inicio_periodo_ano) AS inicio_periodo_ano,
# MAGIC         MAX(fim_periodo_ano) AS fim_periodo_ano,
# MAGIC         COUNT(*) AS meses_vinculo,
# MAGIC
# MAGIC         ROUND(AVG(salario_mes), 2) AS salario_medio_mensal,
# MAGIC         ROUND(AVG(tr), 2) AS tr_medio_mensal,
# MAGIC         ROUND(AVG(ta), 2) AS ta_medio_mensal,
# MAGIC         ROUND(AVG(plano_saude_mes), 2) AS plano_saude_medio_mensal
# MAGIC
# MAGIC     FROM custos_com_saude
# MAGIC
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano
# MAGIC ),
# MAGIC
# MAGIC beneficios AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             tr_medio_mensal
# MAGIC             + ta_medio_mensal
# MAGIC             + plano_saude_medio_mensal,
# MAGIC             2
# MAGIC         ) AS total_beneficios
# MAGIC
# MAGIC     FROM base_anual
# MAGIC ),
# MAGIC
# MAGIC encargos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             (salario_medio_mensal * (4.0 / 3.0)) / 12,
# MAGIC             2
# MAGIC         ) AS ferias,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_medio_mensal / 12,
# MAGIC             2
# MAGIC         ) AS decimo_terceiro
# MAGIC
# MAGIC     FROM beneficios
# MAGIC ),
# MAGIC
# MAGIC encargos_com_fgts AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             0.08 * (
# MAGIC                 salario_medio_mensal
# MAGIC                 + ferias
# MAGIC                 + decimo_terceiro
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS fgts
# MAGIC
# MAGIC     FROM encargos
# MAGIC ),
# MAGIC
# MAGIC custos_com_encargos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             ferias
# MAGIC             + decimo_terceiro
# MAGIC             + fgts,
# MAGIC             2
# MAGIC         ) AS total_encargos
# MAGIC
# MAGIC     FROM encargos_com_fgts
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     *,
# MAGIC
# MAGIC     ROUND(
# MAGIC         salario_medio_mensal
# MAGIC         + total_beneficios
# MAGIC         + total_encargos,
# MAGIC         2
# MAGIC     ) AS custo_total_empregado
# MAGIC
# MAGIC FROM custos_com_encargos
# MAGIC
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     ano;

# COMMAND ----------

# MAGIC %md
# MAGIC # 8. Conclusão do Cálculo do custo total do empregado
# MAGIC
# MAGIC O custo mensal médio total do empregado foi calculado para cada combinação de DRT e ano a partir dos componentes consolidados nas etapas anteriores:
# MAGIC
# MAGIC **Custo Total Empregado = Salário + Total Benefícios + Total Encargos**
# MAGIC
# MAGIC A validação apresentou:
# MAGIC
# MAGIC - **1.147 registros DRT × ano**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - nenhuma duplicidade de DRT e ano;
# MAGIC - **1.116 registros com `custo_total_empregado` calculado**;
# MAGIC - **31 registros com `custo_total_empregado` nulo**;
# MAGIC - nenhuma divergência entre o custo total calculado e a soma de seus componentes nos registros com informação completa.
# MAGIC
# MAGIC Os 31 registros sem custo total calculado pertencem ao período entre **2000 e 2009** e correspondem aos mesmos registros em que `total_beneficios` permanece sem valor devido à ausência de cobertura histórica das respectivas fontes.
# MAGIC
# MAGIC Essas ausências foram preservadas como `NULL`, mantendo a distinção entre ausência de informação e custo igual a zero.
# MAGIC
# MAGIC Os custos dos dependentes permanecem fora da `Fato_Custo_Pessoal` e serão tratados posteriormente na `Fato_Dependentes`.
# MAGIC
# MAGIC Com essa etapa, a composição das medidas da `Fato_Custo_Pessoal` está concluída e validada, permitindo avançar para a definição de sua estrutura final e persistência na camada Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 9. Persistência da Fato_Custo_Pessoal
# MAGIC
# MAGIC Nesta etapa será persistida na camada Gold a estrutura final da `Fato_Custo_Pessoal`.
# MAGIC
# MAGIC O grão da fato é:
# MAGIC
# MAGIC **uma linha por DRT por ano.**
# MAGIC
# MAGIC O DRT identifica o vínculo empregatício, enquanto o CPF permite identificar a mesma pessoa em diferentes vínculos. A coluna `ano` preserva a dimensão histórica dos custos.
# MAGIC
# MAGIC A estrutura final será composta por:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `nome`;
# MAGIC - `cpf`;
# MAGIC - `ano`;
# MAGIC - `salario`;
# MAGIC - `tr`;
# MAGIC - `ta`;
# MAGIC - `plano_saude_titular`;
# MAGIC - `total_beneficios`;
# MAGIC - `ferias`;
# MAGIC - `decimo_terceiro`;
# MAGIC - `fgts`;
# MAGIC - `total_encargos`;
# MAGIC - `custo_total_empregado`.
# MAGIC
# MAGIC As medidas representam custos mensais médios do respectivo vínculo no ano analisado.
# MAGIC
# MAGIC O `plano_saude_titular` considera o valor-base histórico correspondente à faixa etária e à referência vigente, acrescido do **IOF de 2,38%**. Consequentemente, esse valor também está incorporado ao `total_beneficios` e ao `custo_total_empregado`.
# MAGIC
# MAGIC Os campos auxiliares utilizados durante a construção e validação dos cálculos, como datas de início e fim do período anual e quantidade de meses do vínculo, não integrarão a estrutura final da fato.
# MAGIC
# MAGIC Os períodos sem cobertura histórica suficiente para o cálculo dos benefícios continuarão preservados como `NULL`, sem substituição por valores artificiais.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.fato_custo_pessoal
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH limite_temporal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         YEAR(MAX(data_alteracao)) AS ultimo_ano_disponivel
# MAGIC     FROM workspace.silver.salario_anonimizado
# MAGIC ),
# MAGIC
# MAGIC vinculos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_nascimento,
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC         YEAR(e.data_admissao) AS ano_inicial,
# MAGIC
# MAGIC         LEAST(
# MAGIC             YEAR(
# MAGIC                 COALESCE(
# MAGIC                     e.data_desligamento,
# MAGIC                     MAKE_DATE(l.ultimo_ano_disponivel, 12, 31)
# MAGIC                 )
# MAGIC             ),
# MAGIC             l.ultimo_ano_disponivel
# MAGIC         ) AS ano_final
# MAGIC
# MAGIC     FROM workspace.silver.empregados_anonimizados e
# MAGIC     CROSS JOIN limite_temporal l
# MAGIC
# MAGIC     WHERE LENGTH(TRIM(CAST(e.drt AS STRING))) <= 3
# MAGIC ),
# MAGIC
# MAGIC drt_ano AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC
# MAGIC     FROM vinculos
# MAGIC
# MAGIC     WHERE ano_inicial <= ano_final
# MAGIC ),
# MAGIC
# MAGIC periodos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC         ano,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             data_admissao,
# MAGIC             MAKE_DATE(ano, 1, 1)
# MAGIC         ) AS inicio_periodo_ano,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(
# MAGIC                 data_desligamento,
# MAGIC                 MAKE_DATE(ano, 12, 31)
# MAGIC             ),
# MAGIC             MAKE_DATE(ano, 12, 31)
# MAGIC         ) AS fim_periodo_ano
# MAGIC
# MAGIC     FROM drt_ano
# MAGIC ),
# MAGIC
# MAGIC meses AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         p.*,
# MAGIC
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(
# MAGIC                 DATE_TRUNC('MONTH', inicio_periodo_ano),
# MAGIC                 DATE_TRUNC('MONTH', fim_periodo_ano),
# MAGIC                 INTERVAL 1 MONTH
# MAGIC             )
# MAGIC         ) AS mes_referencia
# MAGIC
# MAGIC     FROM periodos p
# MAGIC ),
# MAGIC
# MAGIC salario_mensal AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         m.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(s.salario, s.data_alteracao)
# MAGIC             FROM workspace.silver.salario_anonimizado s
# MAGIC             WHERE
# MAGIC                 s.drt = m.drt
# MAGIC                 AND s.data_alteracao <= LAST_DAY(m.mes_referencia)
# MAGIC         ) AS salario_mes
# MAGIC
# MAGIC     FROM meses m
# MAGIC ),
# MAGIC
# MAGIC tickets_referencia AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(`Período (CCT)`, '([0-9]{4})', 1)
# MAGIC             AS INT
# MAGIC         ) AS ano_inicio,
# MAGIC
# MAGIC         CAST(
# MAGIC             REGEXP_EXTRACT(
# MAGIC                 `Período (CCT)`,
# MAGIC                 '([0-9]{4})[^0-9]+([0-9]{4})',
# MAGIC                 2
# MAGIC             )
# MAGIC             AS INT
# MAGIC         ) AS ano_fim,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Direto: VR/VA Total (21 dias fixos)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS tr,
# MAGIC
# MAGIC         CAST(
# MAGIC             `Benefício Indireto (Valor Mínimo Mensal)`
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS ta
# MAGIC
# MAGIC     FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC
# MAGIC     WHERE `Período (CCT)` IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC custos_com_tickets AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         s.*,
# MAGIC         t.tr,
# MAGIC         t.ta
# MAGIC
# MAGIC     FROM salario_mensal s
# MAGIC
# MAGIC     LEFT JOIN tickets_referencia t
# MAGIC         ON (
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_inicio
# MAGIC                 AND MONTH(s.mes_referencia) >= 9
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) > t.ano_inicio
# MAGIC                 AND YEAR(s.mes_referencia) < t.ano_fim
# MAGIC             )
# MAGIC             OR
# MAGIC             (
# MAGIC                 YEAR(s.mes_referencia) = t.ano_fim
# MAGIC                 AND MONTH(s.mes_referencia) <= 8
# MAGIC             )
# MAGIC         )
# MAGIC ),
# MAGIC
# MAGIC saude_long AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         mes_ref,
# MAGIC         ordem_historico,
# MAGIC         referencia,
# MAGIC         valor
# MAGIC
# MAGIC     FROM workspace.gold.dim_saude
# MAGIC
# MAGIC     UNPIVOT (
# MAGIC         valor FOR referencia IN (
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
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC
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
# MAGIC
# MAGIC         CAST(TRIM(mes_ref) AS INT) AS idade_inicial,
# MAGIC
# MAGIC         TRY_CAST(
# MAGIC             REPLACE(
# MAGIC                 REPLACE(
# MAGIC                     REPLACE(TRIM(valor), 'R$', ''),
# MAGIC                     '.',
# MAGIC                     ''
# MAGIC                 ),
# MAGIC                 ',',
# MAGIC                 '.'
# MAGIC             )
# MAGIC             AS DECIMAL(15,2)
# MAGIC         ) AS valor_base
# MAGIC
# MAGIC     FROM saude_long
# MAGIC
# MAGIC     WHERE ordem_historico BETWEEN 6 AND 15
# MAGIC       AND TRIM(mes_ref) IN (
# MAGIC           '0', '19', '24', '29', '34',
# MAGIC           '39', '44', '49', '54', '59'
# MAGIC       )
# MAGIC ),
# MAGIC
# MAGIC saude_com_faixa AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         referencia,
# MAGIC         data_vigencia,
# MAGIC         idade_inicial,
# MAGIC
# MAGIC         LEAD(idade_inicial, 1, 999)
# MAGIC             OVER (
# MAGIC                 PARTITION BY referencia
# MAGIC                 ORDER BY idade_inicial
# MAGIC             ) - 1 AS idade_final,
# MAGIC
# MAGIC         valor_base
# MAGIC
# MAGIC     FROM vigencias_saude
# MAGIC ),
# MAGIC
# MAGIC custos_com_saude AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         c.*,
# MAGIC
# MAGIC         (
# MAGIC             SELECT MAX_BY(
# MAGIC                 s.valor_base * 1.0238,
# MAGIC                 s.data_vigencia
# MAGIC             )
# MAGIC
# MAGIC             FROM saude_com_faixa s
# MAGIC
# MAGIC             WHERE
# MAGIC                 s.data_vigencia <= LAST_DAY(c.mes_referencia)
# MAGIC
# MAGIC                 AND FLOOR(
# MAGIC                     MONTHS_BETWEEN(
# MAGIC                         LAST_DAY(c.mes_referencia),
# MAGIC                         c.data_nascimento
# MAGIC                     ) / 12
# MAGIC                 ) BETWEEN s.idade_inicial AND s.idade_final
# MAGIC         ) AS plano_saude_mes
# MAGIC
# MAGIC     FROM custos_com_tickets c
# MAGIC ),
# MAGIC
# MAGIC base_anual AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano,
# MAGIC
# MAGIC         ROUND(AVG(salario_mes), 2) AS salario,
# MAGIC         ROUND(AVG(tr), 2) AS tr,
# MAGIC         ROUND(AVG(ta), 2) AS ta,
# MAGIC         ROUND(AVG(plano_saude_mes), 2) AS plano_saude_titular
# MAGIC
# MAGIC     FROM custos_com_saude
# MAGIC
# MAGIC     GROUP BY
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         ano
# MAGIC ),
# MAGIC
# MAGIC beneficios AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             tr
# MAGIC             + ta
# MAGIC             + plano_saude_titular,
# MAGIC             2
# MAGIC         ) AS total_beneficios
# MAGIC
# MAGIC     FROM base_anual
# MAGIC ),
# MAGIC
# MAGIC encargos AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             (salario * (4.0 / 3.0)) / 12,
# MAGIC             2
# MAGIC         ) AS ferias,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario / 12,
# MAGIC             2
# MAGIC         ) AS decimo_terceiro
# MAGIC
# MAGIC     FROM beneficios
# MAGIC ),
# MAGIC
# MAGIC encargos_com_fgts AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             0.08 * (
# MAGIC                 salario
# MAGIC                 + ferias
# MAGIC                 + decimo_terceiro
# MAGIC             ),
# MAGIC             2
# MAGIC         ) AS fgts
# MAGIC
# MAGIC     FROM encargos
# MAGIC ),
# MAGIC
# MAGIC custos_finais AS (
# MAGIC
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             ferias
# MAGIC             + decimo_terceiro
# MAGIC             + fgts,
# MAGIC             2
# MAGIC         ) AS total_encargos
# MAGIC
# MAGIC     FROM encargos_com_fgts
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     c.drt,
# MAGIC     c.nome,
# MAGIC     e.cpf,
# MAGIC     c.ano,
# MAGIC     c.salario,
# MAGIC     c.tr,
# MAGIC     c.ta,
# MAGIC     c.plano_saude_titular,
# MAGIC     c.total_beneficios,
# MAGIC     c.ferias,
# MAGIC     c.decimo_terceiro,
# MAGIC     c.fgts,
# MAGIC     c.total_encargos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         c.salario
# MAGIC         + c.total_beneficios
# MAGIC         + c.total_encargos,
# MAGIC         2
# MAGIC     ) AS custo_total_empregado
# MAGIC
# MAGIC FROM custos_finais c
# MAGIC
# MAGIC LEFT JOIN workspace.gold.dim_empregado e
# MAGIC     ON c.drt = e.drt;

# COMMAND ----------

# MAGIC %md
# MAGIC # 10. Validação da Fato_Custo_Pessoal persistida
# MAGIC
# MAGIC Após a persistência da `Fato_Custo_Pessoal` na camada Gold, será realizada a validação final da tabela.
# MAGIC
# MAGIC A validação verificará:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de DRTs distintos;
# MAGIC - unicidade da combinação DRT × ano;
# MAGIC - presença de CPF;
# MAGIC - período histórico armazenado;
# MAGIC - presença de valores nulos nas principais medidas;
# MAGIC - consistência do `total_beneficios`;
# MAGIC - consistência do `total_encargos`;
# MAGIC - consistência do `custo_total_empregado`.
# MAGIC
# MAGIC São esperados **1.147 registros** e **341 DRTs distintos**, conforme os resultados já validados antes da persistência.
# MAGIC
# MAGIC Os valores nulos historicamente justificados nos benefícios e, consequentemente, no custo total do empregado devem permanecer preservados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT drt) AS total_drts,
# MAGIC     COUNT(DISTINCT CONCAT(CAST(drt AS STRING), '|', CAST(ano AS STRING))) AS total_drt_ano,
# MAGIC
# MAGIC     SUM(CASE WHEN cpf IS NULL THEN 1 ELSE 0 END) AS cpf_null,
# MAGIC
# MAGIC     MIN(ano) AS primeiro_ano,
# MAGIC     MAX(ano) AS ultimo_ano,
# MAGIC
# MAGIC     SUM(CASE WHEN salario IS NULL THEN 1 ELSE 0 END) AS salario_null,
# MAGIC     SUM(CASE WHEN tr IS NULL THEN 1 ELSE 0 END) AS tr_null,
# MAGIC     SUM(CASE WHEN ta IS NULL THEN 1 ELSE 0 END) AS ta_null,
# MAGIC     SUM(CASE WHEN plano_saude_titular IS NULL THEN 1 ELSE 0 END) AS plano_saude_null,
# MAGIC     SUM(CASE WHEN total_beneficios IS NULL THEN 1 ELSE 0 END) AS total_beneficios_null,
# MAGIC
# MAGIC     SUM(CASE WHEN ferias IS NULL THEN 1 ELSE 0 END) AS ferias_null,
# MAGIC     SUM(CASE WHEN decimo_terceiro IS NULL THEN 1 ELSE 0 END) AS decimo_terceiro_null,
# MAGIC     SUM(CASE WHEN fgts IS NULL THEN 1 ELSE 0 END) AS fgts_null,
# MAGIC     SUM(CASE WHEN total_encargos IS NULL THEN 1 ELSE 0 END) AS total_encargos_null,
# MAGIC
# MAGIC     SUM(CASE WHEN custo_total_empregado IS NULL THEN 1 ELSE 0 END) AS custo_total_null,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN total_beneficios IS NOT NULL
# MAGIC              AND ABS(
# MAGIC                  total_beneficios
# MAGIC                  - ROUND(tr + ta + plano_saude_titular, 2)
# MAGIC              ) > 0.01
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS divergencia_total_beneficios,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN ABS(
# MAGIC                 total_encargos
# MAGIC                 - ROUND(ferias + decimo_terceiro + fgts, 2)
# MAGIC             ) > 0.01
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS divergencia_total_encargos,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN custo_total_empregado IS NOT NULL
# MAGIC              AND ABS(
# MAGIC                  custo_total_empregado
# MAGIC                  - ROUND(salario + total_beneficios + total_encargos, 2)
# MAGIC              ) > 0.01
# MAGIC             THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS divergencia_custo_total
# MAGIC
# MAGIC FROM workspace.gold.fato_custo_pessoal;

# COMMAND ----------

# MAGIC %md
# MAGIC # 10. Conclusão da Validação da Fato_Custo_Pessoal persistida
# MAGIC
# MAGIC A `Fato_Custo_Pessoal` foi persistida e validada na camada Gold como `workspace.gold.fato_custo_pessoal`.
# MAGIC
# MAGIC A validação final apresentou:
# MAGIC
# MAGIC - **1.147 registros**;
# MAGIC - **341 DRTs distintos**;
# MAGIC - **1.147 combinações distintas de DRT × ano**, confirmando a unicidade do grão definido;
# MAGIC - período histórico entre **2000 e 2024**;
# MAGIC - nenhum CPF nulo;
# MAGIC - nenhum salário nulo;
# MAGIC - nenhum valor nulo em férias, 13º, FGTS ou total de encargos;
# MAGIC - nenhuma divergência no cálculo de `total_beneficios`;
# MAGIC - nenhuma divergência no cálculo de `total_encargos`;
# MAGIC - nenhuma divergência no cálculo de `custo_total_empregado`.
# MAGIC
# MAGIC Foram preservados:
# MAGIC
# MAGIC - **31 registros com TR nulo**;
# MAGIC - **31 registros com TA nulo**;
# MAGIC - **25 registros com plano de saúde do titular nulo**;
# MAGIC - **31 registros com total de benefícios nulo**;
# MAGIC - **31 registros com custo total do empregado nulo**.
# MAGIC
# MAGIC Esses valores nulos decorrem da ausência de cobertura histórica das respectivas fontes e foram mantidos como `NULL`, evitando a criação de custos não existentes nos dados de origem.
# MAGIC
# MAGIC O custo do plano de saúde do titular considera o valor-base histórico correspondente à faixa etária e à referência vigente, acrescido do **IOF de 2,38%**. Esse tratamento é aplicado antes da consolidação anual e, consequentemente, está refletido em `plano_saude_titular`, `total_beneficios` e `custo_total_empregado`.
# MAGIC
# MAGIC A estrutura final da fato contém:
# MAGIC
# MAGIC - `drt`;
# MAGIC - `nome`;
# MAGIC - `cpf`;
# MAGIC - `ano`;
# MAGIC - `salario`;
# MAGIC - `tr`;
# MAGIC - `ta`;
# MAGIC - `plano_saude_titular`;
# MAGIC - `total_beneficios`;
# MAGIC - `ferias`;
# MAGIC - `decimo_terceiro`;
# MAGIC - `fgts`;
# MAGIC - `total_encargos`;
# MAGIC - `custo_total_empregado`.
# MAGIC
# MAGIC Cada registro representa o **custo mensal médio de um vínculo empregatício em determinado ano**.
# MAGIC
# MAGIC O DRT identifica o vínculo empregatício, o CPF permite reconhecer uma mesma pessoa em diferentes vínculos e o ano representa o período histórico associado às medidas de custo.
# MAGIC
# MAGIC Os custos dos dependentes não estão incluídos nesta fato e são tratados separadamente na `Fato_Dependentes`.
# MAGIC
# MAGIC Com a persistência e a validação concluídas, a `Fato_Custo_Pessoal` está finalizada na camada Gold.