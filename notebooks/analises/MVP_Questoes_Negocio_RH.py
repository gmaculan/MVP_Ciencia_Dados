# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Questões de Negócio — Módulo de Recursos Humanos
# MAGIC
# MAGIC A gestão de Recursos Humanos envolve diferentes dimensões ao longo da relação entre o funcionário e a empresa. Entre elas estão a atração e seleção de profissionais, integração de novos funcionários, retenção e clima organizacional, remuneração e benefícios, desenvolvimento profissional, cultura e engajamento, saúde e bem-estar e, de forma cada vez mais relevante, o uso de dados para apoiar a tomada de decisão.
# MAGIC
# MAGIC Nesse contexto, questões como rotatividade de funcionários, tempo de permanência na empresa, motivos de desligamento, planejamento de férias, custos de pessoal e adequação dos benefícios podem fornecer informações importantes para o RH e para os gestores. Esses indicadores podem auxiliar tanto nas atividades operacionais da área quanto na identificação de situações que mereçam uma investigação mais aprofundada, como desligamentos precoces, concentração de desligamentos em determinados grupos ou mudanças no comportamento do turnover ao longo do tempo.
# MAGIC
# MAGIC Naturalmente, uma análise abrangente da gestão de pessoas exigiria informações que não fazem parte da base de dados disponível neste projeto, como pesquisas de clima e engajamento, avaliações de desempenho, treinamentos realizados, absenteísmo, processos de recrutamento e seleção, entrevistas de desligamento e indicadores de saúde e bem-estar. Portanto, este MVP não pretende avaliar todas as dimensões da gestão de Recursos Humanos.
# MAGIC
# MAGIC As análises foram definidas a partir dos dados efetivamente disponíveis, buscando verificar de que forma eles podem responder a uma parte dessas necessidades e transformar os registros operacionais em informações úteis para o RH, gestores e Diretoria. Dessa forma, os resultados devem ser entendidos como instrumentos de apoio à análise e à tomada de decisão, e não como explicações isoladas das causas dos fenômenos observados.
# MAGIC
# MAGIC A partir desse contexto, foram definidas as seguintes questões de negócio:
# MAGIC
# MAGIC 1. **Quando um funcionário sairá de férias?**  
# MAGIC    **Público:** RH e gestores responsáveis pelos funcionários.
# MAGIC
# MAGIC 2. **Qual é o histórico de férias de um funcionário?**  
# MAGIC    **Público:** principalmente RH.
# MAGIC
# MAGIC 3. **Quantos funcionários estarão de férias em determinado período?**  
# MAGIC    **Público:** RH e gestores responsáveis pelas equipes.
# MAGIC
# MAGIC 4. **Qual é a folha de pagamento em determinado período?**  
# MAGIC    **Público:** RH.
# MAGIC
# MAGIC 5. **Qual é o índice de turnover da empresa por ano?**  
# MAGIC    **Público:** RH e Diretoria, como indicador para acompanhamento das políticas de retenção.
# MAGIC
# MAGIC 6. **Como o turnover evoluiu ao longo dos anos?**  
# MAGIC    **Público:** RH e Diretoria, permitindo acompanhar mudanças na rotatividade e avaliar sua evolução no contexto das políticas adotadas.
# MAGIC
# MAGIC 7. **Quais são os principais motivos de desligamento?**  
# MAGIC    **Público:** RH. A análise pode indicar situações que mereçam investigação nos processos de recrutamento, seleção, integração e retenção. Por exemplo, a recorrência de determinado motivo relacionado a aspectos comportamentais pode justificar uma análise dos critérios utilizados no processo de seleção.
# MAGIC
# MAGIC 8. **Existe concentração de desligamentos por cliente/alocação ou função profissional?**  
# MAGIC    **Público:** RH e gestores responsáveis pelos clientes e equipes. A análise busca identificar concentrações que possam justificar investigações posteriores, respeitando as limitações dos dados de alocação disponíveis.
# MAGIC
# MAGIC 9. **Qual é o tempo médio de casa dos funcionários ativos?**  
# MAGIC    **Público:** RH.
# MAGIC
# MAGIC 10. **Qual era o tempo médio de casa dos funcionários no momento do desligamento?**  
# MAGIC     **Público:** RH e gestores.
# MAGIC
# MAGIC 11. **Existe relação entre tempo de casa e motivo do desligamento?**  
# MAGIC     **Público:** RH e Diretoria, como apoio à análise das políticas de retenção e dos diferentes momentos da relação entre funcionário e empresa.
# MAGIC
# MAGIC 12. **Qual é a distribuição do perfil dos dependentes?**  
# MAGIC     **Público:** RH e, em análises consolidadas, Diretoria. O conhecimento do perfil dos dependentes pode auxiliar na avaliação e no planejamento das políticas de benefícios.
# MAGIC
# MAGIC 13. **Qual é o impacto dos dependentes no custo dos planos de saúde e odontológico?**  
# MAGIC     **Público:** RH e Diretoria. A análise permite avaliar o impacto financeiro dos dependentes e pode contribuir para discussões sobre políticas de benefícios, retenção e ações direcionadas aos funcionários.
# MAGIC
# MAGIC As questões serão analisadas individualmente nas seções seguintes. Para cada análise será apresentada uma breve contextualização da questão, a consulta utilizada, o resultado obtido e sua interpretação, sempre considerando as premissas e limitações dos dados disponíveis.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.1 Quando um funcionário sairá de férias?
# MAGIC
# MAGIC O planejamento das férias é uma atividade importante tanto para o **RH**, responsável pelo acompanhamento dos direitos e períodos de férias dos funcionários, quanto para os **gestores**, que precisam conhecer antecipadamente a disponibilidade de suas equipes.
# MAGIC
# MAGIC Na empresa considerada neste projeto, o período de férias não é necessariamente definido antecipadamente pelo RH. O funcionário pode escolher quando pretende usufruir suas férias, buscando conciliar seus interesses pessoais com as necessidades das atividades da empresa. Essa política permite, por exemplo, que o funcionário planeje suas férias em conjunto com sua família, desde que o período escolhido seja compatível com as necessidades da organização.
# MAGIC
# MAGIC Por esse motivo, nem todo direito de férias existente na base possui necessariamente um período de gozo já programado. A análise deve, portanto, permitir distinguir os **períodos futuros de férias já registrados** daqueles **direitos de férias para os quais ainda não existe período de gozo informado**.
# MAGIC
# MAGIC Para os períodos já programados, a consulta permitirá identificar **quem sairá de férias e em quais datas**. Para os direitos ainda sem programação registrada, as informações disponíveis na base, como o período aquisitivo e a data-limite para início das férias, poderão auxiliar o RH no acompanhamento da necessidade de futura programação.
# MAGIC
# MAGIC A análise tem, assim, uma finalidade tanto operacional quanto de planejamento: fornecer visibilidade sobre as férias futuras já definidas e sobre os direitos que ainda demandam acompanhamento, sem presumir uma data de férias quando ela não estiver registrada nos dados.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     e.drt,
# MAGIC     e.nome,
# MAGIC     f.numero_direito_ferias,
# MAGIC     f.sequencial_ferias,
# MAGIC     f.data_inicio_periodo_aquisitivo,
# MAGIC     f.data_termino_periodo_aquisitivo,
# MAGIC     f.data_limite_aviso,
# MAGIC     f.data_limite_inicio,
# MAGIC     f.data_aviso,
# MAGIC     f.data_inicio_gozo,
# MAGIC     f.data_termino_gozo,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN f.data_inicio_gozo >= CURRENT_DATE()
# MAGIC             THEN 'Férias marcadas'
# MAGIC         WHEN f.data_inicio_gozo IS NULL
# MAGIC             THEN 'Férias ainda não foram marcadas'
# MAGIC     END AS situacao_ferias
# MAGIC
# MAGIC FROM workspace.gold.fato_ferias f
# MAGIC
# MAGIC INNER JOIN workspace.gold.dim_empregado e
# MAGIC     ON f.drt = e.drt
# MAGIC
# MAGIC WHERE
# MAGIC        f.data_inicio_gozo >= CURRENT_DATE()
# MAGIC     OR f.data_inicio_gozo IS NULL
# MAGIC
# MAGIC ORDER BY
# MAGIC     CASE
# MAGIC         WHEN f.data_inicio_gozo >= CURRENT_DATE() THEN 1
# MAGIC         ELSE 2
# MAGIC     END,
# MAGIC     f.data_inicio_gozo,
# MAGIC     f.data_limite_inicio,
# MAGIC     e.nome;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.1. Conclusão da Quando um funcionário sairá de férias?
# MAGIC
# MAGIC A análise não identificou períodos de férias futuros já marcados na base de dados. Os **316 registros** retornados correspondem a direitos de férias para os quais as férias ainda não foram marcadas, abrangendo **312 vínculos distintos**.
# MAGIC
# MAGIC Também foi observado que a data-limite mais recente para início das férias registrada na base é **02/03/2026**. Dessa forma, na data desta análise, não existem informações registradas que permitam responder quando ocorrerão as próximas férias dos funcionários.
# MAGIC
# MAGIC O resultado não significa que esses funcionários necessariamente estejam com férias em atraso. A base utilizada representa um histórico de registros e não contém informações posteriores que permitam verificar se as férias foram posteriormente marcadas ou usufruídas.
# MAGIC
# MAGIC Assim, a consulta demonstra como a estrutura analítica pode ser utilizada para identificar férias futuras já marcadas e direitos ainda sem programação, mas evidencia também uma limitação dos dados disponíveis para responder à questão no momento atual.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.2 Qual é o histórico de férias de um funcionário?
# MAGIC
# MAGIC A consulta ao histórico de férias de um funcionário é uma necessidade principalmente do **RH**, permitindo acompanhar os direitos de férias adquiridos ao longo do vínculo empregatício e os respectivos períodos em que as férias foram usufruídas.
# MAGIC
# MAGIC A análise busca apresentar, de forma cronológica, os períodos aquisitivos do funcionário e, quando existentes, os períodos de gozo correspondentes. Nos casos em que um mesmo direito de férias tenha sido usufruído de forma fracionada, cada período será apresentado separadamente, preservando a sequência do histórico.
# MAGIC
# MAGIC Quando não houver período de gozo registrado para determinado direito, essa situação também será apresentada como **“Férias ainda não foram marcadas”**, respeitando as informações disponíveis na base.
# MAGIC
# MAGIC Dessa forma, a consulta permite ao RH visualizar de maneira consolidada o histórico de férias associado a determinado vínculo empregatício.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     e.drt,
# MAGIC     e.nome,
# MAGIC     f.numero_direito_ferias,
# MAGIC     f.sequencial_ferias,
# MAGIC     f.data_inicio_periodo_aquisitivo,
# MAGIC     f.data_termino_periodo_aquisitivo,
# MAGIC     f.data_limite_aviso,
# MAGIC     f.data_limite_inicio,
# MAGIC     f.data_aviso,
# MAGIC     f.abono,
# MAGIC     f.numero_periodo_gozo,
# MAGIC     f.data_inicio_gozo,
# MAGIC     f.data_termino_gozo,
# MAGIC
# MAGIC     CASE
# MAGIC         WHEN f.data_inicio_gozo IS NULL
# MAGIC             THEN 'Férias ainda não foram marcadas'
# MAGIC         WHEN f.data_inicio_gozo > CURRENT_DATE()
# MAGIC             THEN 'Férias marcadas'
# MAGIC         WHEN f.data_termino_gozo >= CURRENT_DATE()
# MAGIC             THEN 'Em férias'
# MAGIC         ELSE 'Férias realizadas'
# MAGIC     END AS situacao_ferias
# MAGIC
# MAGIC FROM workspace.gold.fato_ferias f
# MAGIC
# MAGIC INNER JOIN workspace.gold.dim_empregado e
# MAGIC     ON f.drt = e.drt
# MAGIC
# MAGIC ORDER BY
# MAGIC     e.nome,
# MAGIC     f.numero_direito_ferias,
# MAGIC     f.numero_periodo_gozo,
# MAGIC     f.data_inicio_gozo;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.2. Conclusão da Qual é o histórico de férias de um funcionário?
# MAGIC
# MAGIC A consulta permitiu consolidar o histórico de férias dos funcionários, apresentando os períodos aquisitivos e os respectivos períodos de gozo registrados ao longo de cada vínculo empregatício.
# MAGIC
# MAGIC Foram retornados **995 registros referentes a 340 vínculos distintos**. Desse total, **679 correspondem a períodos de férias realizados**, enquanto **316 correspondem a direitos para os quais as férias ainda não foram marcadas**.
# MAGIC
# MAGIC A estrutura também permite representar corretamente as situações em que um mesmo direito de férias foi usufruído de forma fracionada, mantendo cada período de gozo individualizado e associado ao respectivo direito.
# MAGIC
# MAGIC Dessa forma, a consulta atende à necessidade do RH de recuperar o histórico de férias de um funcionário. Em uma aplicação destinada ao uso operacional da área, o funcionário poderia ser selecionado por meio de uma interface, utilizando esta estrutura analítica como fonte para a consulta.
# MAGIC
# MAGIC Assim como observado na análise anterior, os registros sem férias marcadas devem ser interpretados considerando que a base utilizada no MVP é histórica, estática e não representa necessariamente a situação atual dos funcionários.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.3 Quantos funcionários estarão de férias em determinado período?
# MAGIC
# MAGIC Conhecer antecipadamente a quantidade de funcionários que estarão de férias em determinado período é relevante para o **RH** e para os **gestores responsáveis pelas equipes**, pois permite avaliar a disponibilidade de profissionais e apoiar o planejamento das atividades da empresa.
# MAGIC
# MAGIC A análise considera um intervalo definido por uma **data inicial e uma data final** e identifica os funcionários que possuem algum período de férias com sobreposição a esse intervalo. Dessa forma, também são considerados os casos em que as férias tenham começado antes da data inicial consultada ou terminem depois da data final.
# MAGIC
# MAGIC Além da quantidade de funcionários, serão apresentados os respectivos nomes e períodos de férias, permitindo identificar quem estará ausente durante o intervalo analisado.
# MAGIC
# MAGIC Em uma aplicação destinada ao uso operacional, as datas poderiam ser informadas pelo usuário por meio de campos de seleção. Neste MVP, o intervalo será definido diretamente na consulta SQL para demonstrar essa funcionalidade.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH parametros AS (
# MAGIC     SELECT
# MAGIC         DATE '2024-01-01' AS data_inicial,
# MAGIC         DATE '2024-12-31' AS data_final
# MAGIC ),
# MAGIC
# MAGIC funcionarios_em_ferias AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         f.sequencial_ferias,
# MAGIC         f.data_inicio_gozo,
# MAGIC         f.data_termino_gozo
# MAGIC
# MAGIC     FROM workspace.gold.fato_ferias f
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_empregado e
# MAGIC         ON f.drt = e.drt
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE f.data_inicio_gozo <= p.data_final
# MAGIC       AND f.data_termino_gozo >= p.data_inicial
# MAGIC ),
# MAGIC
# MAGIC total_periodo AS (
# MAGIC     SELECT
# MAGIC         COUNT(DISTINCT drt) AS quantidade_funcionarios
# MAGIC     FROM funcionarios_em_ferias
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     p.data_inicial AS periodo_consultado_inicio,
# MAGIC     p.data_final AS periodo_consultado_fim,
# MAGIC     t.quantidade_funcionarios,
# MAGIC     f.drt,
# MAGIC     f.nome,
# MAGIC     f.sequencial_ferias,
# MAGIC     f.data_inicio_gozo,
# MAGIC     f.data_termino_gozo
# MAGIC
# MAGIC FROM parametros p
# MAGIC
# MAGIC CROSS JOIN total_periodo t
# MAGIC
# MAGIC LEFT JOIN funcionarios_em_ferias f
# MAGIC     ON 1 = 1
# MAGIC
# MAGIC ORDER BY
# MAGIC     f.data_inicio_gozo,
# MAGIC     f.nome;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.3. Conclusão da Quantos funcionários estarão de férias em determinado período?
# MAGIC
# MAGIC Para demonstrar a consulta, foi utilizado o intervalo de **01/01/2024 a 31/12/2024**. Esse período foi selecionado deliberadamente em razão da natureza histórica, estática e desatualizada da base disponível. A utilização de um período mais recente poderia não apresentar registros e, consequentemente, não permitiria ilustrar adequadamente a capacidade da solução de responder a esta questão de negócio.
# MAGIC
# MAGIC Para o intervalo analisado, foram identificados **26 funcionários distintos** com férias que se sobrepõem ao período consultado. Esses funcionários estão associados a **38 períodos de férias**, uma vez que um mesmo funcionário pode possuir mais de um período de gozo dentro da janela selecionada.
# MAGIC
# MAGIC Além da quantidade de funcionários, a consulta apresenta quem estará de férias e as respectivas datas de início e término, permitindo que o RH e os gestores identifiquem as ausências previstas no período.
# MAGIC
# MAGIC O intervalo de 2024 não representa uma recomendação de janela de análise para o RH, mas uma escolha metodológica para demonstrar o funcionamento da consulta com os dados disponíveis no MVP. Portanto, os resultados não representam a situação atual da empresa.
# MAGIC
# MAGIC Em uma aplicação operacional alimentada por dados atualizados, o mesmo mecanismo permitiria ao usuário selecionar o intervalo de interesse e obter a quantidade e a identificação dos funcionários com férias programadas nesse período, apoiando o planejamento da disponibilidade das equipes.
# MAGIC
# MAGIC A análise também permite identificar **sobreposições entre períodos de férias de diferentes funcionários**. Essas sobreposições não representam necessariamente um problema, mas podem exigir avaliação quando envolvem, por exemplo, profissionais-chave de um mesmo projeto ou equipe. Nesses casos, a informação pode apoiar o RH e os gestores na identificação antecipada de riscos à disponibilidade de recursos e, quando necessário e observadas as regras aplicáveis, na avaliação de ajustes no planejamento das férias de um ou mais funcionários.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.4 Qual é a folha de pagamento em determinado período?
# MAGIC
# MAGIC A folha de pagamento é uma informação relevante para o **RH**, tanto para o acompanhamento dos valores associados à equipe quanto para a geração de demonstrativos individuais destinados aos funcionários.
# MAGIC
# MAGIC Nesta análise, a folha será tratada em **periodicidade mensal**. O usuário deverá informar uma data inicial e uma data final correspondentes ao mês de referência, por exemplo, de **01/05/2024 a 31/05/2024**. A consulta identificará os vínculos ativos no período selecionado a partir das respectivas datas de admissão e desligamento.
# MAGIC
# MAGIC O resultado será apresentado por funcionário, permitindo identificar separadamente o **salário CLT**, os **benefícios** e os demais componentes considerados na análise. Dessa forma, a mesma consulta poderá gerar a visão consolidada da folha da equipe e servir de base para a apresentação individual dos valores associados a cada funcionário.
# MAGIC
# MAGIC Também serão considerados os efeitos temporais das movimentações de pessoal. Funcionários admitidos ou desligados durante o período deverão ser identificados a partir das respectivas datas, evitando que a simples existência do funcionário na `Fato_Custo_Pessoal` anual seja interpretada como permanência durante todo o mês analisado.
# MAGIC
# MAGIC Quando o funcionário não permanecer ativo durante todo o mês, o salário será calculado proporcionalmente aos dias trabalhados, conforme a regra adotada nesta análise:
# MAGIC
# MAGIC **Salário proporcional = salário mensal × dias trabalhados / 30.**
# MAGIC
# MAGIC Para o funcionário que permanecer ativo durante todo o mês, serão considerados 30 dias para efeito desse cálculo.
# MAGIC
# MAGIC Os benefícios de **ticket refeição (TR)** e **ticket alimentação (TA)** serão calculados de acordo com a quantidade de dias úteis trabalhados no período. Para fins deste MVP, serão considerados dias úteis exclusivamente os dias de **segunda a sexta-feira, sem exclusão de feriados**. Essa simplificação decorre do fato de os feriados não terem sido modelados na estrutura de dados.
# MAGIC
# MAGIC Nos casos de desligamento durante o mês, a quantidade de dias utilizada para TR e TA corresponderá ao número de dias de segunda a sexta-feira compreendidos entre o **primeiro dia do mês e a data de desligamento, inclusive**. Analogamente, para admissões ocorridas durante o mês, serão considerados os dias de segunda a sexta-feira compreendidos entre a data de admissão e o final do período analisado.
# MAGIC
# MAGIC O **décimo terceiro salário** será tratado de forma proporcional ao período efetivamente aplicável ao vínculo no ano de referência, evitando considerar meses anteriores à admissão ou posteriores ao desligamento.
# MAGIC
# MAGIC Os **encargos** utilizados nesta análise também serão calculados especificamente para a finalidade da consulta, sem reutilizar diretamente o total existente na `Fato_Custo_Pessoal`, uma vez que a estrutura original inclui componentes que não fazem parte desta análise.
# MAGIC
# MAGIC As **férias não serão consideradas nesta folha**, pois possuem processo e pagamento próprios e são tratadas separadamente na estrutura de dados do MVP.
# MAGIC
# MAGIC Em uma aplicação operacional, o RH poderia selecionar o mês de referência por meio de uma interface, gerar a folha correspondente aos funcionários ativos naquele período e disponibilizar a cada funcionário o respectivo demonstrativo individual.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH parametros AS (
# MAGIC     SELECT
# MAGIC         DATE '2024-05-01' AS data_inicial,
# MAGIC         DATE '2024-05-31' AS data_final
# MAGIC ),
# MAGIC
# MAGIC empregados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.cpf,
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     LEFT JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC ),
# MAGIC
# MAGIC base_folha AS (
# MAGIC     SELECT
# MAGIC         c.drt,
# MAGIC         c.nome,
# MAGIC         c.cpf,
# MAGIC
# MAGIC         e.data_admissao,
# MAGIC         e.data_desligamento,
# MAGIC
# MAGIC         p.data_inicial,
# MAGIC         p.data_final,
# MAGIC
# MAGIC         c.salario AS salario_mensal_contratual,
# MAGIC         c.tr,
# MAGIC         c.ta,
# MAGIC         c.plano_saude_titular,
# MAGIC
# MAGIC         GREATEST(
# MAGIC             e.data_admissao,
# MAGIC             p.data_inicial
# MAGIC         ) AS inicio_atividade_mes,
# MAGIC
# MAGIC         LEAST(
# MAGIC             COALESCE(e.data_desligamento, p.data_final),
# MAGIC             p.data_final
# MAGIC         ) AS fim_atividade_mes
# MAGIC
# MAGIC     FROM workspace.gold.fato_custo_pessoal c
# MAGIC
# MAGIC     INNER JOIN empregados e
# MAGIC         ON c.drt = e.drt
# MAGIC
# MAGIC     CROSS JOIN parametros p
# MAGIC
# MAGIC     WHERE c.ano = YEAR(p.data_final)
# MAGIC
# MAGIC       AND e.data_admissao <= p.data_final
# MAGIC
# MAGIC       AND (
# MAGIC             e.data_desligamento IS NULL
# MAGIC             OR e.data_desligamento >= p.data_inicial
# MAGIC           )
# MAGIC ),
# MAGIC
# MAGIC calculo_dias AS (
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
# MAGIC     FROM base_folha b
# MAGIC
# MAGIC     LEFT JOIN workspace.gold.dim_tempo t
# MAGIC         ON t.data BETWEEN b.inicio_atividade_mes
# MAGIC                       AND b.fim_atividade_mes
# MAGIC
# MAGIC     GROUP BY
# MAGIC         b.drt,
# MAGIC         b.nome,
# MAGIC         b.cpf,
# MAGIC         b.data_admissao,
# MAGIC         b.data_desligamento,
# MAGIC         b.data_inicial,
# MAGIC         b.data_final,
# MAGIC         b.salario_mensal_contratual,
# MAGIC         b.tr,
# MAGIC         b.ta,
# MAGIC         b.plano_saude_titular,
# MAGIC         b.inicio_atividade_mes,
# MAGIC         b.fim_atividade_mes
# MAGIC ),
# MAGIC
# MAGIC calculo_valores AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_mensal_contratual
# MAGIC             * dias_trabalhados / 30.0,
# MAGIC             2
# MAGIC         ) AS salario_periodo,
# MAGIC
# MAGIC         ROUND(
# MAGIC             COALESCE(tr, 0)
# MAGIC             / 21.0
# MAGIC             * LEAST(dias_uteis_trabalhados, 21),
# MAGIC             2
# MAGIC         ) AS ticket_refeicao_periodo,
# MAGIC
# MAGIC         ROUND(
# MAGIC             COALESCE(ta, 0)
# MAGIC             / 21.0
# MAGIC             * LEAST(dias_uteis_trabalhados, 21),
# MAGIC             2
# MAGIC         ) AS ticket_alimentacao_periodo,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN YEAR(data_admissao) < YEAR(data_final)
# MAGIC                 THEN
# MAGIC                     MONTH(data_final)
# MAGIC                     - CASE
# MAGIC                         WHEN dias_trabalhados >= 15 THEN 0
# MAGIC                         ELSE 1
# MAGIC                       END
# MAGIC
# MAGIC             WHEN YEAR(data_admissao) = YEAR(data_final)
# MAGIC                 THEN
# MAGIC                     MONTH(data_final)
# MAGIC                     - MONTH(data_admissao)
# MAGIC                     + 1
# MAGIC                     - CASE
# MAGIC                         WHEN dias_trabalhados >= 15 THEN 0
# MAGIC                         ELSE 1
# MAGIC                       END
# MAGIC
# MAGIC             ELSE 0
# MAGIC         END AS meses_13_salario,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN dias_trabalhados >= 15 THEN 1
# MAGIC             ELSE 0
# MAGIC         END AS avo_13_adquirido_mes
# MAGIC
# MAGIC     FROM calculo_dias
# MAGIC ),
# MAGIC
# MAGIC folha_final AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_mensal_contratual
# MAGIC             / 12.0
# MAGIC             * meses_13_salario,
# MAGIC             2
# MAGIC         ) AS decimo_terceiro_acumulado,
# MAGIC
# MAGIC         ROUND(
# MAGIC             salario_mensal_contratual
# MAGIC             / 12.0
# MAGIC             * avo_13_adquirido_mes,
# MAGIC             2
# MAGIC         ) AS decimo_terceiro_provisionado_mes,
# MAGIC
# MAGIC         ROUND(
# MAGIC               ticket_refeicao_periodo
# MAGIC             + ticket_alimentacao_periodo
# MAGIC             + COALESCE(plano_saude_titular, 0),
# MAGIC             2
# MAGIC         ) AS total_beneficios_periodo
# MAGIC
# MAGIC     FROM calculo_valores
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     cpf,
# MAGIC
# MAGIC     data_admissao,
# MAGIC     data_desligamento,
# MAGIC
# MAGIC     data_inicial AS inicio_periodo_folha,
# MAGIC     data_final AS fim_periodo_folha,
# MAGIC
# MAGIC     dias_trabalhados,
# MAGIC     dias_uteis_trabalhados,
# MAGIC
# MAGIC     salario_mensal_contratual,
# MAGIC     salario_periodo,
# MAGIC
# MAGIC     ticket_refeicao_periodo,
# MAGIC     ticket_alimentacao_periodo,
# MAGIC     plano_saude_titular,
# MAGIC     total_beneficios_periodo,
# MAGIC
# MAGIC     meses_13_salario,
# MAGIC     decimo_terceiro_acumulado,
# MAGIC
# MAGIC     avo_13_adquirido_mes,
# MAGIC     decimo_terceiro_provisionado_mes,
# MAGIC
# MAGIC     ROUND(
# MAGIC           salario_periodo
# MAGIC         + total_beneficios_periodo,
# MAGIC         2
# MAGIC     ) AS remuneracao_beneficios_mes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         0.08 * (
# MAGIC               salario_periodo
# MAGIC             + decimo_terceiro_provisionado_mes
# MAGIC         ),
# MAGIC         2
# MAGIC     ) AS fgts_considerado,
# MAGIC
# MAGIC     ROUND(
# MAGIC           salario_periodo
# MAGIC         + total_beneficios_periodo
# MAGIC         + (
# MAGIC             0.08 * (
# MAGIC                   salario_periodo
# MAGIC                 + decimo_terceiro_provisionado_mes
# MAGIC             )
# MAGIC           ),
# MAGIC         2
# MAGIC     ) AS custo_considerado
# MAGIC
# MAGIC FROM folha_final
# MAGIC
# MAGIC ORDER BY nome;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.4. Conclusão da Qual é a folha de pagamento em determinado período?
# MAGIC
# MAGIC A consulta demonstrou que a estrutura analítica permite gerar uma **folha mensal dos funcionários com vínculo ativo no período selecionado**, considerando as respectivas datas de admissão e desligamento.
# MAGIC
# MAGIC Para a demonstração foi utilizado o período de **01/05/2024 a 31/05/2024**, no qual foram identificados **32 funcionários** com vínculo durante pelo menos parte do mês.
# MAGIC
# MAGIC A análise também permitiu tratar situações de admissão ou desligamento dentro do período. Nesses casos, o salário é calculado proporcionalmente segundo a regra **salário mensal × dias trabalhados / 30**.
# MAGIC
# MAGIC Os benefícios de **ticket refeição (TR)** e **ticket alimentação (TA)** são calculados proporcionalmente aos dias úteis trabalhados. Para fins deste MVP, foram considerados dias úteis os dias de **segunda a sexta-feira, sem exclusão de feriados**, uma vez que os feriados não foram modelados na estrutura de dados. O plano de saúde, por sua natureza mensal, foi mantido integralmente enquanto existente para o vínculo considerado.
# MAGIC
# MAGIC O décimo terceiro salário também pode ser acompanhado de forma proporcional. A consulta permite distinguir o **direito acumulado ao 13º ao longo do ano** da **provisão adquirida no mês analisado**. Para a composição mensal dos encargos, deve ser considerado somente o avo adquirido naquele mês, evitando contabilizar novamente provisões correspondentes aos meses anteriores.
# MAGIC
# MAGIC Consequentemente, o FGTS da competência deve ser calculado sobre os componentes aplicáveis àquele mês, e não sobre todo o 13º acumulado desde o início do ano. As férias foram excluídas desta análise por possuírem processo e pagamento próprios.
# MAGIC
# MAGIC Os casos de desligamento ocorridos durante maio permitiram validar as regras de proporcionalidade. Foram identificados, por exemplo, funcionários desligados em **01/05/2024** e **03/05/2024**, para os quais a consulta calculou respectivamente 1 e 3 dias de salário e 1 e 3 dias úteis para TR e TA. Como ambos trabalharam menos de 15 dias no mês, maio não acrescentou um novo avo de décimo terceiro nesses casos.
# MAGIC
# MAGIC Dessa forma, a solução permite ao RH selecionar uma competência mensal, identificar os funcionários que fizeram parte da folha e gerar o detalhamento individual dos componentes disponíveis na estrutura analítica. Em uma aplicação operacional, essa consulta poderia alimentar tanto a visão consolidada da folha da equipe quanto demonstrativos individuais disponibilizados aos funcionários.
# MAGIC
# MAGIC A solução desenvolvida possui finalidade **analítica e demonstrativa**. A base do MVP não contém todos os elementos necessários a um sistema transacional completo de folha de pagamento, como todos os descontos legais, regras tributárias e demais eventos de folha. Portanto, o resultado não deve ser interpretado como substituto de um sistema oficial de processamento de folha.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.5 Qual é o turnover anual?
# MAGIC
# MAGIC O acompanhamento do **turnover** permite ao RH e à Diretoria avaliar a movimentação de saída de funcionários em relação ao tamanho do quadro da empresa. O indicador pode contribuir para o acompanhamento das políticas de retenção e para a identificação de períodos que mereçam análise mais detalhada.
# MAGIC
# MAGIC Como existem diferentes formas de calcular turnover, neste MVP será adotada explicitamente a seguinte definição:
# MAGIC
# MAGIC **Turnover anual = número de desligamentos ocorridos no ano / número médio de funcionários no ano × 100**
# MAGIC
# MAGIC O número médio de funcionários será calculado pela média entre o quadro ativo no início e no final de cada ano:
# MAGIC
# MAGIC **Quadro médio = (funcionários ativos no início do ano + funcionários ativos no final do ano) / 2**
# MAGIC
# MAGIC Serão consideradas as datas de admissão e desligamento de cada vínculo empregatício. Dessa forma, o cálculo não dependerá apenas da existência do funcionário na base, mas da vigência efetiva do vínculo nas datas utilizadas para determinar o tamanho do quadro.
# MAGIC
# MAGIC O turnover será apresentado como indicador descritivo. Um valor maior ou menor, isoladamente, não permite concluir se existe um problema de retenção nem identificar suas causas. Essa interpretação deverá ser realizada em conjunto com outras análises, como a evolução histórica do indicador, os motivos de desligamento e o tempo de permanência dos funcionários.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH empregados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     LEFT JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC ),
# MAGIC
# MAGIC limites AS (
# MAGIC     SELECT
# MAGIC         YEAR(MIN(data_admissao)) AS ano_inicial,
# MAGIC         YEAR(MAX(COALESCE(data_desligamento, CURRENT_DATE()))) AS ano_final
# MAGIC     FROM empregados
# MAGIC ),
# MAGIC
# MAGIC anos AS (
# MAGIC     SELECT
# MAGIC         EXPLODE(
# MAGIC             SEQUENCE(ano_inicial, ano_final)
# MAGIC         ) AS ano
# MAGIC     FROM limites
# MAGIC ),
# MAGIC
# MAGIC indicadores AS (
# MAGIC     SELECT
# MAGIC         a.ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN e.data_admissao <= MAKE_DATE(a.ano, 1, 1)
# MAGIC                  AND (
# MAGIC                         e.data_desligamento IS NULL
# MAGIC                         OR e.data_desligamento >= MAKE_DATE(a.ano, 1, 1)
# MAGIC                      )
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS funcionarios_inicio_ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN e.data_admissao <= MAKE_DATE(a.ano, 12, 31)
# MAGIC                  AND (
# MAGIC                         e.data_desligamento IS NULL
# MAGIC                         OR e.data_desligamento >= MAKE_DATE(a.ano, 12, 31)
# MAGIC                      )
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS funcionarios_final_ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN YEAR(e.data_desligamento) = a.ano
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS desligamentos_ano
# MAGIC
# MAGIC     FROM anos a
# MAGIC
# MAGIC     CROSS JOIN empregados e
# MAGIC
# MAGIC     GROUP BY a.ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano,
# MAGIC
# MAGIC     funcionarios_inicio_ano,
# MAGIC     funcionarios_final_ano,
# MAGIC
# MAGIC     ROUND(
# MAGIC         (funcionarios_inicio_ano + funcionarios_final_ano) / 2.0,
# MAGIC         2
# MAGIC     ) AS quadro_medio,
# MAGIC
# MAGIC     desligamentos_ano,
# MAGIC
# MAGIC     ROUND(
# MAGIC         desligamentos_ano
# MAGIC         /
# MAGIC         NULLIF(
# MAGIC             (funcionarios_inicio_ano + funcionarios_final_ano) / 2.0,
# MAGIC             0
# MAGIC         )
# MAGIC         * 100,
# MAGIC         2
# MAGIC     ) AS turnover_percentual
# MAGIC
# MAGIC FROM indicadores
# MAGIC
# MAGIC ORDER BY ano;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.5. Conclusão da Qual é o turnover anual?
# MAGIC
# MAGIC A análise permitiu calcular o turnover anual a partir do número de desligamentos e do quadro médio de funcionários em cada ano. Para este MVP, foram considerados todos os desligamentos registrados, independentemente do respectivo motivo.
# MAGIC
# MAGIC Os resultados mostram variações relevantes ao longo do histórico disponível. Entre os anos com desligamentos registrados, o turnover variou de **24,59% em 2018** a **77,78% em 2021**. Em 2024, por exemplo, foram registrados **20 desligamentos**, para um quadro médio de **28,5 funcionários**, resultando em turnover de **70,18%**.
# MAGIC
# MAGIC Nos períodos em que não existem desligamentos registrados na base, o indicador calculado é igual a zero. Esse resultado deve ser interpretado considerando as características da fonte utilizada: a ausência de desligamentos registrados não permite, isoladamente, concluir que não tenha ocorrido rotatividade na empresa.
# MAGIC
# MAGIC O turnover também não deve ser interpretado isoladamente como evidência de sucesso ou problema nas políticas de retenção. O indicador mostra a intensidade dos desligamentos em relação ao tamanho do quadro, mas não explica suas causas. Para isso, é necessário combiná-lo com outras informações, como os motivos de desligamento, o tempo de permanência dos funcionários e eventuais concentrações por período, função ou alocação.
# MAGIC
# MAGIC Dessa forma, o indicador fornece ao RH e à Diretoria uma medida objetiva para acompanhar a rotatividade da força de trabalho e identificar períodos que mereçam investigação mais detalhada.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.6 Como o turnover evoluiu ao longo dos anos?
# MAGIC
# MAGIC Após o cálculo do turnover anual, é possível analisar sua **evolução ao longo do tempo**, permitindo ao RH e à Diretoria identificar períodos de aumento ou redução da rotatividade e direcionar investigações para os anos que apresentem mudanças relevantes no comportamento do indicador.
# MAGIC
# MAGIC A análise temporal é particularmente importante porque um valor isolado de turnover fornece apenas uma fotografia de determinado ano. A comparação entre diferentes períodos permite avaliar a trajetória do indicador e identificar anos que se diferenciam do comportamento observado no restante da série histórica.
# MAGIC
# MAGIC A evolução do turnover será analisada utilizando a mesma definição adotada na seção anterior:
# MAGIC
# MAGIC **Turnover anual = número de desligamentos no ano / quadro médio de funcionários no ano × 100.**
# MAGIC
# MAGIC Os resultados devem ser interpretados como **indicadores descritivos**. Uma elevação ou redução do turnover não permite, isoladamente, concluir que determinada política de retenção, decisão gerencial ou outro fator tenha provocado a mudança. Essas hipóteses exigiriam informações adicionais e análises complementares.
# MAGIC
# MAGIC Também devem ser consideradas as limitações da base histórica utilizada no MVP, especialmente nos períodos em que não existem desligamentos registrados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH empregados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     LEFT JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC ),
# MAGIC
# MAGIC limites AS (
# MAGIC     SELECT
# MAGIC         YEAR(MIN(data_admissao)) AS ano_inicial,
# MAGIC         YEAR(MAX(COALESCE(data_desligamento, CURRENT_DATE()))) AS ano_final
# MAGIC     FROM empregados
# MAGIC ),
# MAGIC
# MAGIC anos AS (
# MAGIC     SELECT
# MAGIC         EXPLODE(SEQUENCE(ano_inicial, ano_final)) AS ano
# MAGIC     FROM limites
# MAGIC ),
# MAGIC
# MAGIC indicadores AS (
# MAGIC     SELECT
# MAGIC         a.ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN e.data_admissao <= MAKE_DATE(a.ano, 1, 1)
# MAGIC                  AND (
# MAGIC                         e.data_desligamento IS NULL
# MAGIC                         OR e.data_desligamento >= MAKE_DATE(a.ano, 1, 1)
# MAGIC                      )
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS funcionarios_inicio_ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN e.data_admissao <= MAKE_DATE(a.ano, 12, 31)
# MAGIC                  AND (
# MAGIC                         e.data_desligamento IS NULL
# MAGIC                         OR e.data_desligamento >= MAKE_DATE(a.ano, 12, 31)
# MAGIC                      )
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS funcionarios_final_ano,
# MAGIC
# MAGIC         COUNT(
# MAGIC             DISTINCT CASE
# MAGIC                 WHEN YEAR(e.data_desligamento) = a.ano
# MAGIC                 THEN e.drt
# MAGIC             END
# MAGIC         ) AS desligamentos_ano
# MAGIC
# MAGIC     FROM anos a
# MAGIC
# MAGIC     CROSS JOIN empregados e
# MAGIC
# MAGIC     GROUP BY a.ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano,
# MAGIC
# MAGIC     ROUND(
# MAGIC         desligamentos_ano
# MAGIC         /
# MAGIC         NULLIF(
# MAGIC             (funcionarios_inicio_ano + funcionarios_final_ano) / 2.0,
# MAGIC             0
# MAGIC         )
# MAGIC         * 100,
# MAGIC         2
# MAGIC     ) AS turnover_percentual
# MAGIC
# MAGIC FROM indicadores
# MAGIC
# MAGIC ORDER BY ano;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.6. Conclusão da Como o turnover evoluiu ao longo dos anos?
# MAGIC
# MAGIC A análise da evolução do turnover evidencia **variações relevantes ao longo dos anos**, sem apresentar uma trajetória contínua de crescimento ou redução.
# MAGIC
# MAGIC Entre os anos com desligamentos registrados, o turnover passou de **26,09% em 2012** para **55,00% em 2014** e permaneceu elevado em 2015, com **52,98%**. Nos anos seguintes houve redução, chegando a **24,59% em 2018**.
# MAGIC
# MAGIC O indicador voltou a crescer em 2019 e 2020 e atingiu **77,78% em 2021**, maior valor observado entre os anos com desligamentos registrados. Posteriormente, ocorreu uma redução expressiva para **26,19% em 2022** e **29,73% em 2023**, seguida de novo aumento para **70,18% em 2024**.
# MAGIC
# MAGIC Essa oscilação demonstra a importância de não analisar o turnover apenas em um único período. A série histórica permite ao RH e à Diretoria identificar anos que se diferenciam do comportamento observado em períodos próximos e direcionar análises complementares para compreender o que ocorreu nesses momentos.
# MAGIC
# MAGIC Os anos em que o indicador aparece como **0%** devem ser interpretados considerando as limitações da base histórica. A ausência de desligamentos registrados não é suficiente, isoladamente, para concluir que não houve rotatividade nesses períodos.
# MAGIC
# MAGIC Da mesma forma, as variações observadas não permitem atribuir causalidade a políticas de retenção ou decisões específicas da empresa. Para investigar possíveis explicações, o turnover deve ser analisado em conjunto com outras informações disponíveis, como os **motivos dos desligamentos, o tempo de permanência dos funcionários e possíveis concentrações por função ou alocação**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.7 Quais são os principais motivos de desligamento?
# MAGIC
# MAGIC Além de acompanhar a quantidade de desligamentos e o turnover, o **RH** precisa compreender os motivos registrados para as saídas dos funcionários.
# MAGIC
# MAGIC A identificação dos motivos mais frequentes permite avaliar quais situações apresentam maior recorrência e direcionar investigações mais específicas. Dependendo do padrão encontrado, essas informações podem apoiar a revisão de políticas de retenção, práticas de gestão e até dos processos de recrutamento e seleção.
# MAGIC
# MAGIC Por exemplo, a recorrência de determinados motivos relacionados à adequação do profissional ao trabalho pode indicar a necessidade de investigar se os critérios utilizados na seleção estão alinhados às necessidades da empresa. Entretanto, a frequência de um motivo de desligamento, isoladamente, **não permite concluir que houve falha no processo de contratação ou determinar a causa do problema**.
# MAGIC
# MAGIC A análise será realizada sobre os desligamentos efetivamente registrados na base, agrupando-os pelo respectivo motivo e apresentando tanto a quantidade quanto a participação percentual de cada motivo no total de desligamentos.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH desligamentos AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         COALESCE(
# MAGIC             NULLIF(TRIM(motivo_desligamento), ''),
# MAGIC             'Não informado'
# MAGIC         ) AS motivo_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado
# MAGIC
# MAGIC     WHERE id_tempo_desligamento IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_desligamentos
# MAGIC     FROM desligamentos
# MAGIC ),
# MAGIC
# MAGIC motivos AS (
# MAGIC     SELECT
# MAGIC         motivo_desligamento,
# MAGIC         COUNT(*) AS quantidade_desligamentos
# MAGIC
# MAGIC     FROM desligamentos
# MAGIC
# MAGIC     GROUP BY
# MAGIC         motivo_desligamento
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     m.motivo_desligamento,
# MAGIC     m.quantidade_desligamentos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         m.quantidade_desligamentos
# MAGIC         / t.total_desligamentos
# MAGIC         * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_desligamentos
# MAGIC
# MAGIC FROM motivos m
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC ORDER BY
# MAGIC     m.quantidade_desligamentos DESC,
# MAGIC     m.motivo_desligamento;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.7. Conclusão da Quais são os principais motivos de desligamento?
# MAGIC
# MAGIC A análise identificou **333 desligamentos**, distribuídos entre 11 motivos registrados na base.
# MAGIC
# MAGIC O motivo mais frequente foi **“Demitido - Falta de Projeto”**, com **89 desligamentos (26,73%)**, seguido de **“Pedido de Demissão - Motivos Particulares e Outros”**, com **82 casos (24,62%)**. Juntos, esses dois motivos representam **51,35%** dos desligamentos registrados.
# MAGIC
# MAGIC Também apresentam participação relevante **“Demitido - Outros Motivos”**, com **45 casos (13,51%)**, **“Pedido de Demissão - Contratação pelo Cliente”**, com **43 casos (12,91%)**, e **“Pedido de Demissão - Motivação Salarial”**, com **30 casos (9,01%)**.
# MAGIC
# MAGIC Entre os motivos diretamente relacionados ao desempenho ou comportamento profissional, foram registrados **19 desligamentos por baixo rendimento técnico (5,71%)**, **10 por problema comportamental (3,00%)** e **9 por assiduidade e outros desvios do contrato de trabalho (2,70%)**.
# MAGIC
# MAGIC Os resultados permitem ao RH direcionar investigações conforme a natureza dos desligamentos. A participação de desligamentos por **falta de projeto**, por exemplo, pode ser analisada em conjunto com informações sobre demanda e alocação de profissionais. Os pedidos de demissão associados à **motivação salarial** podem subsidiar análises sobre remuneração e retenção, enquanto os casos relacionados a **rendimento técnico, comportamento e assiduidade** podem motivar avaliações dos processos de recrutamento, seleção, acompanhamento e desenvolvimento dos profissionais.
# MAGIC
# MAGIC Da mesma forma, a **contratação de funcionários pelos próprios clientes** aparece como motivo relevante de saída e pode ser considerada pelo RH e pelos gestores na avaliação das relações de alocação e das políticas de retenção.
# MAGIC
# MAGIC Essas associações devem ser entendidas como **direcionamentos para investigação**, e não como demonstração de causalidade. O motivo registrado para o desligamento, isoladamente, não permite determinar todas as circunstâncias que levaram à saída do funcionário.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.8 Há concentração de desligamentos por cliente/alocação ou função profissional?
# MAGIC
# MAGIC Após identificar os principais motivos de desligamento, é relevante avaliar se as saídas apresentam concentração em determinadas **alocações** ou **funções profissionais**.
# MAGIC
# MAGIC Essa análise pode apoiar o **RH** e os **gestores responsáveis pelos clientes e equipes** na identificação de grupos que apresentem maior quantidade de desligamentos e que, consequentemente, possam justificar uma investigação mais detalhada.
# MAGIC
# MAGIC Entretanto, a interpretação dos resultados por alocação exige uma limitação importante. A base disponível no MVP **não contém o histórico completo das alocações dos funcionários ao longo do tempo**. Dessa forma, a alocação registrada não pode ser interpretada necessariamente como aquela em que o funcionário se encontrava na data de seu desligamento.
# MAGIC
# MAGIC Por esse motivo, eventuais concentrações identificadas por cliente ou alocação serão apresentadas como uma característica dos registros disponíveis, e não como evidência de que determinada alocação tenha provocado ou esteja diretamente associada aos desligamentos.
# MAGIC
# MAGIC Para a análise da **função profissional**, será utilizado o cargo registrado no histórico salarial, preservando a distinção entre cargo profissional e atividade registrada na alocação.
# MAGIC
# MAGIC Os resultados serão utilizados como indicadores para direcionar análises do RH e dos gestores, sem atribuição automática de causalidade.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH empregados_desligados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         td.data AS data_desligamento,
# MAGIC         e.motivo_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC ),
# MAGIC
# MAGIC cargo_desligamento AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.data_desligamento,
# MAGIC         e.motivo_desligamento,
# MAGIC         s.cargo,
# MAGIC         s.data_alteracao,
# MAGIC
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY e.drt
# MAGIC             ORDER BY s.data_alteracao DESC
# MAGIC         ) AS ordem_cargo
# MAGIC
# MAGIC     FROM empregados_desligados e
# MAGIC
# MAGIC     LEFT JOIN workspace.silver.salario_anonimizado s
# MAGIC         ON e.drt = s.drt
# MAGIC        AND s.data_alteracao <= e.data_desligamento
# MAGIC ),
# MAGIC
# MAGIC base AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_desligamento,
# MAGIC         motivo_desligamento,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             NULLIF(TRIM(cargo), ''),
# MAGIC             'Cargo não informado'
# MAGIC         ) AS cargo
# MAGIC
# MAGIC     FROM cargo_desligamento
# MAGIC
# MAGIC     WHERE ordem_cargo = 1
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_desligamentos
# MAGIC     FROM base
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     b.cargo,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_desligamentos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COUNT(*) / t.total_desligamentos * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_desligamentos
# MAGIC
# MAGIC FROM base b
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC GROUP BY
# MAGIC     b.cargo,
# MAGIC     t.total_desligamentos
# MAGIC
# MAGIC ORDER BY
# MAGIC     quantidade_desligamentos DESC,
# MAGIC     b.cargo;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH empregados_desligados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.motivo_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     WHERE e.id_tempo_desligamento IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC base AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         e.motivo_desligamento,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             NULLIF(TRIM(a.alocacao_principal), ''),
# MAGIC             'Alocação não disponível'
# MAGIC         ) AS alocacao_principal
# MAGIC
# MAGIC     FROM empregados_desligados e
# MAGIC
# MAGIC     LEFT JOIN workspace.silver.alocacao_anonimizado a
# MAGIC         ON e.drt = a.drt
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(DISTINCT drt) AS total_desligamentos
# MAGIC     FROM base
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     b.alocacao_principal,
# MAGIC
# MAGIC     COUNT(DISTINCT b.drt) AS quantidade_desligamentos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COUNT(DISTINCT b.drt)
# MAGIC         / t.total_desligamentos
# MAGIC         * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_desligamentos
# MAGIC
# MAGIC FROM base b
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC GROUP BY
# MAGIC     b.alocacao_principal,
# MAGIC     t.total_desligamentos
# MAGIC
# MAGIC ORDER BY
# MAGIC     quantidade_desligamentos DESC,
# MAGIC     b.alocacao_principal;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.8. Conclusão da Há concentração de desligamentos por cliente/alocação ou função profissional?
# MAGIC
# MAGIC Para responder a esta questão foram realizadas **duas análises complementares**. A primeira avaliou a concentração dos desligamentos segundo a **função profissional exercida pelo funcionário**, enquanto a segunda avaliou sua distribuição segundo a **alocação disponível na base**.
# MAGIC
# MAGIC As duas análises possuem objetivos e limitações diferentes e, por isso, seus resultados são apresentados separadamente.
# MAGIC
# MAGIC ### Análise 1 — Concentração dos desligamentos por função profissional
# MAGIC
# MAGIC A primeira consulta teve como objetivo verificar **em quais funções profissionais se concentram os desligamentos registrados**.
# MAGIC
# MAGIC Para isso, foi utilizado o histórico salarial de cada funcionário. Para cada vínculo desligado, a consulta buscou o **último cargo registrado em data igual ou anterior à data do desligamento**, procurando representar a função profissional existente no momento mais próximo da saída.
# MAGIC
# MAGIC Entre os **333 desligamentos**, os cargos com maior número de ocorrências foram:
# MAGIC
# MAGIC - **CONSULTOR EM TI - III:** 130 desligamentos (39,04%);
# MAGIC - **CONSULTOR EM TI - IV:** 110 desligamentos (33,03%);
# MAGIC - **CONSULTOR EM TI - II:** 60 desligamentos (18,02%).
# MAGIC
# MAGIC Somados, esses três cargos representam **300 dos 333 desligamentos (90,09%)**.
# MAGIC
# MAGIC **Conclusão da primeira análise:** os desligamentos registrados apresentam forte concentração, em números absolutos, nas funções **CONSULTOR EM TI - II, III e IV**.
# MAGIC
# MAGIC Esse resultado, entretanto, não significa que essas funções apresentem maior propensão ao desligamento. A consulta mede a participação de cada cargo no total de desligamentos, mas não compara os desligamentos com a quantidade total de funcionários que ocuparam cada cargo. Assim, parte dessa concentração pode decorrer da própria composição do quadro da empresa.
# MAGIC
# MAGIC Também foram identificadas pequenas diferenças de padronização na descrição de alguns cargos, capazes de fragmentar categorias equivalentes e que devem ser consideradas como uma questão de qualidade dos dados.
# MAGIC
# MAGIC ### Análise 2 — Concentração dos desligamentos por alocação
# MAGIC
# MAGIC A segunda consulta teve como objetivo verificar **como os desligamentos se distribuem entre as alocações disponíveis na base**.
# MAGIC
# MAGIC As maiores concentrações foram observadas em:
# MAGIC
# MAGIC - **BRAVIA:** 52 desligamentos (15,62%);
# MAGIC - **LUMINA:** 48 desligamentos (14,41%);
# MAGIC - **XXX:** 43 desligamentos (12,91%);
# MAGIC - **FÁBRICA:** 23 desligamentos (6,91%);
# MAGIC - **ARVENA:** 20 desligamentos (6,01%).
# MAGIC
# MAGIC Também foi identificada a categoria **FABRICA**, sem acento, com 13 desligamentos (3,90%), indicando uma possível necessidade de padronização dos valores de alocação. Além disso, 5 desligamentos (1,50%) não possuem alocação disponível.
# MAGIC
# MAGIC **Conclusão da segunda análise:** os registros disponíveis também apresentam concentração dos desligamentos em determinadas alocações, principalmente **BRAVIA, LUMINA e XXX**.
# MAGIC
# MAGIC Essa conclusão possui, entretanto, uma limitação estrutural importante. A base utilizada no MVP **não contém o histórico completo das alocações dos funcionários**. Consequentemente, não é possível assegurar que a alocação disponível corresponda exatamente àquela em que o funcionário se encontrava na data do desligamento.
# MAGIC
# MAGIC Além disso, assim como na análise por função, os percentuais representam a participação de cada alocação no total de desligamentos, e não uma taxa de desligamento dentro de cada alocação. Portanto, não se pode concluir que determinada alocação apresente maior risco de desligamento apenas a partir desses resultados.
# MAGIC
# MAGIC ### Conclusão conjunta
# MAGIC
# MAGIC As duas consultas mostram que os desligamentos registrados **não se distribuem uniformemente** entre as funções profissionais e as alocações disponíveis na base.
# MAGIC
# MAGIC Na perspectiva profissional, existe forte concentração nos cargos de **Consultor em TI II, III e IV**. Na perspectiva das alocações disponíveis, destacam-se principalmente **BRAVIA, LUMINA e XXX**.
# MAGIC
# MAGIC Essas concentrações constituem indicadores úteis para o **RH e para os gestores**, pois permitem direcionar investigações para determinados grupos. Entretanto, não estabelecem relação causal entre função ou alocação e desligamento.
# MAGIC
# MAGIC Em uma evolução da solução, especialmente com um histórico completo das alocações e com a população de funcionários exposta a cada função ou cliente ao longo do tempo, seria possível calcular **taxas específicas de desligamento** e realizar comparações mais robustas entre os diferentes grupos.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.9 Qual é o tempo médio de permanência dos funcionários ativos?
# MAGIC
# MAGIC O tempo de permanência dos funcionários é um indicador relevante para o acompanhamento da **retenção de profissionais**, permitindo ao RH compreender há quanto tempo os funcionários atualmente ativos permanecem na empresa.
# MAGIC
# MAGIC Nesta análise serão considerados somente os vínculos que permanecem **ativos na base**, ou seja, aqueles que não possuem data de desligamento registrada.
# MAGIC
# MAGIC Para cada funcionário ativo, o tempo de permanência será calculado a partir de sua data de admissão até uma **data de referência compatível com o período representado pelos dados**. Como a base utilizada no MVP é histórica e não recebe atualização contínua, não será utilizada automaticamente a data atual do sistema, pois isso aumentaria artificialmente o tempo de permanência dos funcionários.
# MAGIC
# MAGIC Além da média geral, a análise permitirá observar os tempos individuais de permanência, evitando que a interpretação fique restrita a um único valor agregado.
# MAGIC
# MAGIC O indicador deve ser interpretado como uma descrição dos funcionários que permanecem ativos na data de referência da base, não constituindo, isoladamente, uma medida de qualidade das políticas de retenção da empresa.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH funcionarios_ativos AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         ta.data AS data_admissao,
# MAGIC         DATE('2024-12-31') AS data_referencia
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     WHERE e.id_tempo_desligamento IS NULL
# MAGIC ),
# MAGIC
# MAGIC permanencia AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_admissao,
# MAGIC         data_referencia,
# MAGIC
# MAGIC         DATEDIFF(
# MAGIC             data_referencia,
# MAGIC             data_admissao
# MAGIC         ) AS permanencia_dias,
# MAGIC
# MAGIC         ROUND(
# MAGIC             DATEDIFF(data_referencia, data_admissao) / 365.25,
# MAGIC             2
# MAGIC         ) AS permanencia_anos
# MAGIC
# MAGIC     FROM funcionarios_ativos
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     data_admissao,
# MAGIC     data_referencia,
# MAGIC     permanencia_dias,
# MAGIC     permanencia_anos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         AVG(permanencia_anos) OVER (),
# MAGIC         2
# MAGIC     ) AS permanencia_media_anos
# MAGIC
# MAGIC FROM permanencia
# MAGIC
# MAGIC ORDER BY
# MAGIC     permanencia_anos DESC,
# MAGIC     drt;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.9. Conclusão da Qual é o tempo médio de permanência dos funcionários ativos?
# MAGIC
# MAGIC Considerando **31/12/2024 como data de referência**, foram identificados **14 vínculos ativos** na base.
# MAGIC
# MAGIC O **tempo médio de permanência desses funcionários é de 9,68 anos**.
# MAGIC
# MAGIC Os tempos individuais apresentam amplitude considerável. O funcionário ativo com maior tempo de permanência registra **24,38 anos**, enquanto o menor tempo observado é de **0,90 ano**. Dessa forma, o quadro ativo reúne tanto profissionais com longa permanência na empresa quanto funcionários admitidos mais recentemente.
# MAGIC
# MAGIC A utilização de **31/12/2024 como data de referência** é importante para a interpretação do indicador. Essa data corresponde ao limite dos registros de desligamento disponíveis na base. Como os dados utilizados no MVP são históricos e não recebem atualização contínua, utilizar a data atual do sistema aumentaria artificialmente o tempo de permanência dos funcionários que continuam classificados como ativos.
# MAGIC
# MAGIC Portanto, o resultado de **9,68 anos** representa o tempo médio de permanência dos funcionários que estavam registrados como ativos **na data de referência adotada para a análise**, não devendo ser interpretado como uma medida atualizada da situação da empresa.
# MAGIC
# MAGIC O indicador fornece ao RH uma visão consolidada da permanência do quadro ativo e pode ser utilizado, em conjunto com os indicadores de turnover e desligamentos, para apoiar análises de retenção de profissionais. Isoladamente, entretanto, um tempo médio elevado ou reduzido não permite concluir sobre a eficácia das políticas de retenção.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.10 Qual é o tempo médio de permanência no momento do desligamento?
# MAGIC
# MAGIC Além de conhecer o tempo de permanência dos funcionários que continuam ativos, é relevante analisar **quanto tempo os profissionais desligados permaneceram na empresa até a sua saída**.
# MAGIC
# MAGIC Nesta análise serão considerados somente os vínculos que possuem desligamento registrado. Para cada vínculo, o tempo de permanência será calculado entre a **data de admissão** e a respectiva **data de desligamento**.
# MAGIC
# MAGIC A análise apresentará o tempo individual de permanência e a média observada entre os funcionários desligados. Esse indicador complementa a análise dos funcionários ativos e permite ao RH compreender em que horizonte de permanência ocorreram os desligamentos registrados.
# MAGIC
# MAGIC O resultado possui caráter descritivo. O tempo médio de permanência no desligamento, isoladamente, não permite determinar as causas das saídas nem avaliar a eficácia das políticas de retenção da empresa.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH funcionarios_desligados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC         e.nome,
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento,
# MAGIC         e.motivo_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC
# MAGIC     WHERE e.id_tempo_desligamento IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC permanencia AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_admissao,
# MAGIC         data_desligamento,
# MAGIC         motivo_desligamento,
# MAGIC
# MAGIC         DATEDIFF(
# MAGIC             data_desligamento,
# MAGIC             data_admissao
# MAGIC         ) AS permanencia_dias,
# MAGIC
# MAGIC         ROUND(
# MAGIC             DATEDIFF(data_desligamento, data_admissao) / 365.25,
# MAGIC             2
# MAGIC         ) AS permanencia_anos
# MAGIC
# MAGIC     FROM funcionarios_desligados
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     nome,
# MAGIC     data_admissao,
# MAGIC     data_desligamento,
# MAGIC     motivo_desligamento,
# MAGIC     permanencia_dias,
# MAGIC     permanencia_anos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         AVG(permanencia_anos) OVER (),
# MAGIC         2
# MAGIC     ) AS permanencia_media_desligados_anos
# MAGIC
# MAGIC FROM permanencia
# MAGIC
# MAGIC ORDER BY
# MAGIC     permanencia_anos DESC,
# MAGIC     drt;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.10. Conclusão da Qual é o tempo médio de permanência no momento do desligamento?
# MAGIC
# MAGIC Foram analisados **333 vínculos com desligamento registrado**. O **tempo médio de permanência até o desligamento foi de 2,09 anos**.
# MAGIC
# MAGIC Os tempos individuais apresentam grande variação. O menor período observado foi de **1 dia**, enquanto o maior foi de aproximadamente **15 anos**. A **mediana foi de 1,16 ano**, indicando que metade dos vínculos desligados permaneceu na empresa por até aproximadamente esse período.
# MAGIC
# MAGIC A diferença entre a média de **2,09 anos** e a mediana de **1,16 ano** mostra que a distribuição dos tempos de permanência não é uniforme. A existência de funcionários que permaneceram por períodos consideravelmente mais longos eleva a média do grupo, tornando a mediana uma informação complementar importante para a interpretação do indicador.
# MAGIC
# MAGIC Como referência, na análise anterior os **14 vínculos ativos em 31/12/2024 apresentaram permanência média de 9,68 anos**, valor substancialmente superior aos 2,09 anos observados entre os vínculos desligados. Essa comparação descreve uma diferença entre os dois grupos existentes na base, mas não permite concluir que maior tempo de permanência seja consequência de determinada política de retenção ou que menor permanência explique os desligamentos.
# MAGIC
# MAGIC O resultado permite ao RH compreender melhor o horizonte temporal em que ocorreram as saídas registradas e complementa os indicadores de turnover e motivos de desligamento. A próxima análise aprofunda essa perspectiva ao relacionar o **tempo de permanência com os diferentes motivos de desligamento**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.11 Existe relação entre o tempo de permanência e o motivo do desligamento?
# MAGIC
# MAGIC Após identificar o tempo médio de permanência dos funcionários desligados, é relevante verificar se esse tempo apresenta diferenças conforme o **motivo registrado para o desligamento**.
# MAGIC
# MAGIC Nesta análise, os vínculos desligados serão agrupados pelo motivo da saída. Para cada grupo serão apresentados a **quantidade de desligamentos**, o **tempo médio de permanência** e o **tempo mediano de permanência**.
# MAGIC
# MAGIC A utilização conjunta da média e da mediana é importante porque a análise anterior mostrou que os tempos de permanência apresentam uma distribuição assimétrica, na qual alguns vínculos de longa duração podem elevar a média.
# MAGIC
# MAGIC A comparação permite ao RH identificar se determinados motivos de desligamento aparecem associados, nos dados históricos disponíveis, a profissionais com maior ou menor tempo de permanência na empresa.
# MAGIC
# MAGIC Os resultados possuem caráter **descritivo e associativo**. Eventuais diferenças entre os grupos não demonstram que o tempo de permanência tenha causado determinado motivo de desligamento, nem que o motivo registrado explique, isoladamente, o período durante o qual o funcionário permaneceu na empresa.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH funcionarios_desligados AS (
# MAGIC     SELECT
# MAGIC         e.drt,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             NULLIF(TRIM(e.motivo_desligamento), ''),
# MAGIC             'Não informado'
# MAGIC         ) AS motivo_desligamento,
# MAGIC
# MAGIC         ta.data AS data_admissao,
# MAGIC         td.data AS data_desligamento
# MAGIC
# MAGIC     FROM workspace.gold.dim_empregado e
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo ta
# MAGIC         ON e.id_tempo_admissao = ta.id_tempo
# MAGIC
# MAGIC     INNER JOIN workspace.gold.dim_tempo td
# MAGIC         ON e.id_tempo_desligamento = td.id_tempo
# MAGIC
# MAGIC     WHERE e.id_tempo_desligamento IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC permanencia AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         motivo_desligamento,
# MAGIC
# MAGIC         DATEDIFF(
# MAGIC             data_desligamento,
# MAGIC             data_admissao
# MAGIC         ) / 365.25 AS permanencia_anos
# MAGIC
# MAGIC     FROM funcionarios_desligados
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     motivo_desligamento,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_desligamentos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         AVG(permanencia_anos),
# MAGIC         2
# MAGIC     ) AS permanencia_media_anos,
# MAGIC
# MAGIC     ROUND(
# MAGIC         PERCENTILE_APPROX(permanencia_anos, 0.5),
# MAGIC         2
# MAGIC     ) AS permanencia_mediana_anos
# MAGIC
# MAGIC FROM permanencia
# MAGIC
# MAGIC GROUP BY
# MAGIC     motivo_desligamento
# MAGIC
# MAGIC ORDER BY
# MAGIC     quantidade_desligamentos DESC,
# MAGIC     motivo_desligamento;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.11. Conclusão da Existe relação entre o tempo de permanência e o motivo do desligamento?
# MAGIC
# MAGIC A análise mostra que o **tempo de permanência apresenta diferenças entre os diferentes motivos de desligamento registrados na base**.
# MAGIC
# MAGIC Entre os motivos com maior número de ocorrências, os desligamentos por **falta de projeto**, com 89 casos, apresentam permanência média de **2,78 anos** e mediana de **1,75 ano**. Os pedidos de demissão por **motivos particulares e outros**, com 82 casos, apresentam média de **1,87 ano** e mediana de **1,16 ano**.
# MAGIC
# MAGIC Os 43 funcionários que pediram demissão em razão de **contratação pelo cliente** permaneceram, em média, **2,21 anos**, com mediana de **1,72 ano**. Já os 30 desligamentos relacionados à **motivação salarial** apresentam tempos menores, com média de **1,06 ano** e mediana de **0,89 ano**.
# MAGIC
# MAGIC Uma diferença particularmente relevante aparece nos desligamentos por **baixo rendimento técnico**. Nos 19 casos registrados, a permanência média foi de apenas **0,38 ano**, com mediana de **0,36 ano**, constituindo o menor tempo de permanência entre os motivos com quantidade relevante de registros. Os desligamentos relacionados à **assiduidade e outros desvios do contrato de trabalho**, com 9 casos, também apresentam permanência relativamente curta, com média de **0,93 ano** e mediana de **0,72 ano**.
# MAGIC
# MAGIC Os resultados mostram, portanto, que os diferentes motivos de desligamento estão associados, na base analisada, a **diferentes padrões de tempo de permanência**. Essa informação pode direcionar investigações do RH. Por exemplo, os desligamentos por baixo rendimento técnico ocorrem, em geral, em um período relativamente curto após a admissão, enquanto os desligamentos por falta de projeto e contratação pelo cliente aparecem associados a permanências mais longas.
# MAGIC
# MAGIC Essas diferenças, entretanto, **não demonstram causalidade**. A análise não permite concluir que determinado tempo de permanência provoque um motivo de desligamento ou que o motivo registrado explique, isoladamente, o período de permanência do funcionário.
# MAGIC
# MAGIC Também é necessário considerar o tamanho de cada grupo. A categoria **“Pedido de Demissão - Falta de Perspectiva”**, por exemplo, apresenta permanência de 4,90 anos, mas possui somente **um registro**, não sendo adequado generalizar esse resultado.
# MAGIC
# MAGIC Por fim, a média é superior à mediana na maioria dos grupos com quantidade relevante de registros, indicando a presença de vínculos de maior duração que elevam o valor médio. Por essa razão, **média, mediana e quantidade de ocorrências devem ser avaliadas conjuntamente** na interpretação dos resultados.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.12 Qual é a distribuição do perfil dos dependentes?
# MAGIC
# MAGIC Conhecer o perfil dos dependentes dos funcionários permite ao RH compreender a composição da população vinculada aos benefícios oferecidos pela empresa e pode apoiar o planejamento e o acompanhamento de políticas de benefícios.
# MAGIC
# MAGIC Nesta análise, a unidade considerada é o **dependente**. O perfil será observado segundo o **grau de parentesco**, o **gênero** e a **faixa etária**, utilizando as informações disponíveis na base de dependentes.
# MAGIC
# MAGIC Para o cálculo da idade será utilizada a data de **31/12/2024** como referência, mantendo consistência com o horizonte temporal adotado nas análises anteriores e evitando que uma base histórica seja atualizada artificialmente pela data corrente do sistema.
# MAGIC
# MAGIC Os resultados possuem caráter descritivo e representam a composição dos dependentes registrada na base, não permitindo, isoladamente, inferir necessidades individuais de utilização dos benefícios.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH base AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             NULLIF(TRIM(parentesco), ''),
# MAGIC             'Não informado'
# MAGIC         ) AS parentesco
# MAGIC
# MAGIC     FROM workspace.silver.dependentes_anonimizados
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_dependentes
# MAGIC     FROM base
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     b.parentesco,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COUNT(*) / t.total_dependentes * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_dependentes
# MAGIC
# MAGIC FROM base b
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC GROUP BY
# MAGIC     b.parentesco,
# MAGIC     t.total_dependentes
# MAGIC
# MAGIC ORDER BY
# MAGIC     quantidade_dependentes DESC,
# MAGIC     b.parentesco;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH base AS (
# MAGIC     SELECT
# MAGIC         CASE
# MAGIC             WHEN genero IS NULL OR TRIM(genero) = ''
# MAGIC                 THEN 'Não informado'
# MAGIC             ELSE INITCAP(LOWER(TRIM(genero)))
# MAGIC         END AS genero
# MAGIC
# MAGIC     FROM workspace.silver.dependentes_anonimizados
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_dependentes
# MAGIC     FROM base
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     b.genero,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COUNT(*) / t.total_dependentes * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_dependentes
# MAGIC
# MAGIC FROM base b
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC GROUP BY
# MAGIC     b.genero,
# MAGIC     t.total_dependentes
# MAGIC
# MAGIC ORDER BY
# MAGIC     quantidade_dependentes DESC,
# MAGIC     b.genero;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH idades AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         data_nascimento,
# MAGIC
# MAGIC         FLOOR(
# MAGIC             MONTHS_BETWEEN(
# MAGIC                 DATE('2024-12-31'),
# MAGIC                 data_nascimento
# MAGIC             ) / 12
# MAGIC         ) AS idade
# MAGIC
# MAGIC     FROM workspace.silver.dependentes_anonimizados
# MAGIC
# MAGIC     WHERE data_nascimento IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC faixas AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         nome,
# MAGIC         idade,
# MAGIC
# MAGIC         CASE
# MAGIC             WHEN idade < 0 THEN 'Data inconsistente'
# MAGIC             WHEN idade <= 5 THEN '0 a 5 anos'
# MAGIC             WHEN idade <= 11 THEN '6 a 11 anos'
# MAGIC             WHEN idade <= 17 THEN '12 a 17 anos'
# MAGIC             WHEN idade <= 24 THEN '18 a 24 anos'
# MAGIC             WHEN idade <= 39 THEN '25 a 39 anos'
# MAGIC             WHEN idade <= 59 THEN '40 a 59 anos'
# MAGIC             ELSE '60 anos ou mais'
# MAGIC         END AS faixa_etaria
# MAGIC
# MAGIC     FROM idades
# MAGIC ),
# MAGIC
# MAGIC total AS (
# MAGIC     SELECT
# MAGIC         COUNT(*) AS total_dependentes
# MAGIC     FROM faixas
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     f.faixa_etaria,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COUNT(*) / t.total_dependentes * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_dependentes
# MAGIC
# MAGIC FROM faixas f
# MAGIC
# MAGIC CROSS JOIN total t
# MAGIC
# MAGIC GROUP BY
# MAGIC     f.faixa_etaria,
# MAGIC     t.total_dependentes
# MAGIC
# MAGIC ORDER BY
# MAGIC     MIN(f.idade);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.12. Conclusão da Qual é a distribuição do perfil dos dependentes?
# MAGIC
# MAGIC Para analisar o perfil dos dependentes foram realizadas **três consultas complementares**, considerando as dimensões de **parentesco, gênero e faixa etária**. Cada consulta apresenta uma perspectiva diferente sobre a composição dos 218 dependentes registrados na base.
# MAGIC
# MAGIC ### Análise 1 — Distribuição dos dependentes por parentesco
# MAGIC
# MAGIC A primeira consulta teve como objetivo identificar **como os dependentes se distribuem segundo o grau de parentesco registrado em relação ao funcionário**.
# MAGIC
# MAGIC Dos **218 dependentes**, a maior concentração corresponde à categoria **FILHO(A)**, com **152 registros (69,72%)**. Em seguida aparecem **CÔNJUGE**, com **27 (12,39%)**, **ENTEADO(A)**, com **15 (6,88%)**, e **ESPOSA**, com **13 (5,96%)**. As demais categorias apresentam participações menores.
# MAGIC
# MAGIC **Conclusão da primeira análise:** o perfil de parentesco é predominantemente composto por **filhos**, que representam mais de dois terços dos dependentes registrados.
# MAGIC
# MAGIC A consulta também evidenciou diferenças de padronização na classificação dos parentescos, com categorias semanticamente próximas registradas separadamente, como `FILHO(A)` e `FILHA`, ou `CÔNJUGE`, `ESPOSA` e `COMPANHEIRO(A)`. Os valores foram preservados conforme registrados na base, sem consolidação automática dessas categorias.
# MAGIC
# MAGIC ### Análise 2 — Distribuição dos dependentes por gênero
# MAGIC
# MAGIC A segunda consulta teve como objetivo verificar **como os dependentes se distribuem segundo o gênero**.
# MAGIC
# MAGIC Dos **218 dependentes**, **110 (50,46%)** são do gênero masculino e **108 (49,54%)** do gênero feminino.
# MAGIC
# MAGIC **Conclusão da segunda análise:** a distribuição por gênero é **praticamente equilibrada**, com diferença de apenas dois dependentes entre as duas categorias. Dessa forma, não se observa concentração relevante dos dependentes em determinado gênero.
# MAGIC
# MAGIC ### Análise 3 — Distribuição dos dependentes por faixa etária
# MAGIC
# MAGIC A terceira consulta teve como objetivo identificar **como os dependentes se distribuem segundo a idade**, utilizando **31/12/2024 como data de referência** para o cálculo.
# MAGIC
# MAGIC A distribuição encontrada foi:
# MAGIC
# MAGIC - **0 a 5 anos:** 4 dependentes (1,83%);
# MAGIC - **6 a 11 anos:** 35 (16,06%);
# MAGIC - **12 a 17 anos:** 51 (23,39%);
# MAGIC - **18 a 24 anos:** 44 (20,18%);
# MAGIC - **25 a 39 anos:** 47 (21,56%);
# MAGIC - **40 a 59 anos:** 22 (10,09%);
# MAGIC - **60 anos ou mais:** 15 (6,88%).
# MAGIC
# MAGIC **Conclusão da terceira análise:** os dependentes estão distribuídos por todas as faixas etárias, porém a maior concentração ocorre entre **12 e 39 anos**. As três faixas compreendidas entre 12 e 39 anos reúnem **142 dos 218 dependentes (65,14%)**.
# MAGIC
# MAGIC A faixa individual com maior quantidade é a de **12 a 17 anos**, com 51 dependentes (23,39%), seguida de **25 a 39 anos**, com 47 (21,56%), e **18 a 24 anos**, com 44 (20,18%).
# MAGIC
# MAGIC ### Conclusão conjunta
# MAGIC
# MAGIC As três consultas permitem caracterizar o perfil dos dependentes sob perspectivas complementares.
# MAGIC
# MAGIC Quanto ao **parentesco**, existe forte predominância de filhos. Quanto ao **gênero**, a distribuição é praticamente equilibrada. Quanto à **idade**, embora existam dependentes em todas as faixas analisadas, observa-se maior concentração entre 12 e 39 anos.
# MAGIC
# MAGIC Esse perfil fornece ao RH uma visão consolidada da população de dependentes registrada na base e pode apoiar análises relacionadas à composição e ao planejamento dos benefícios oferecidos pela empresa.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.13 Qual é o impacto dos dependentes nos custos de plano de saúde/odontológico?
# MAGIC
# MAGIC A quantidade e o perfil dos dependentes podem influenciar os custos dos benefícios concedidos aos funcionários, especialmente aqueles relacionados à assistência à saúde.
# MAGIC
# MAGIC A `Fato_Dependentes` disponibiliza, para cada dependente e ano, o respectivo **custo de plano de saúde**, permitindo mensurar diretamente o impacto financeiro dos dependentes nesse benefício, sem necessidade de estimar valores a partir apenas da quantidade de dependentes.
# MAGIC
# MAGIC Nesta análise será avaliada a **evolução anual do custo do plano de saúde dos dependentes**, considerando o número de dependentes com registros em cada ano, o custo total e o custo médio por dependente.
# MAGIC
# MAGIC A estrutura disponível não contém um campo correspondente ao **custo de plano odontológico dos dependentes**. Dessa forma, o impacto financeiro desse benefício não poderá ser quantificado com os dados disponíveis no MVP. A análise financeira desta seção ficará restrita ao plano de saúde, e essa limitação será considerada na interpretação dos resultados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     ano,
# MAGIC
# MAGIC     COUNT(*) AS quantidade_registros_dependentes,
# MAGIC
# MAGIC     COUNT(DISTINCT drt) AS quantidade_funcionarios_com_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         SUM(custo_plano_saude),
# MAGIC         2
# MAGIC     ) AS custo_total_plano_saude_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         AVG(custo_plano_saude),
# MAGIC         2
# MAGIC     ) AS custo_medio_plano_saude_por_dependente
# MAGIC
# MAGIC FROM workspace.gold.fato_dependentes
# MAGIC
# MAGIC GROUP BY
# MAGIC     ano
# MAGIC
# MAGIC ORDER BY
# MAGIC     ano;

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH titulares AS (
# MAGIC     SELECT
# MAGIC         ano,
# MAGIC
# MAGIC         SUM(
# MAGIC             COALESCE(plano_saude_titular, 0)
# MAGIC         ) AS custo_plano_saude_titulares
# MAGIC
# MAGIC     FROM workspace.gold.fato_custo_pessoal
# MAGIC
# MAGIC     GROUP BY
# MAGIC         ano
# MAGIC ),
# MAGIC
# MAGIC dependentes AS (
# MAGIC     SELECT
# MAGIC         ano,
# MAGIC
# MAGIC         SUM(
# MAGIC             COALESCE(custo_plano_saude, 0)
# MAGIC         ) AS custo_plano_saude_dependentes
# MAGIC
# MAGIC     FROM workspace.gold.fato_dependentes
# MAGIC
# MAGIC     GROUP BY
# MAGIC         ano
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     t.ano,
# MAGIC
# MAGIC     ROUND(
# MAGIC         t.custo_plano_saude_titulares,
# MAGIC         2
# MAGIC     ) AS custo_plano_saude_titulares,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COALESCE(d.custo_plano_saude_dependentes, 0),
# MAGIC         2
# MAGIC     ) AS custo_plano_saude_dependentes,
# MAGIC
# MAGIC     ROUND(
# MAGIC         t.custo_plano_saude_titulares
# MAGIC         + COALESCE(d.custo_plano_saude_dependentes, 0),
# MAGIC         2
# MAGIC     ) AS custo_total_plano_saude,
# MAGIC
# MAGIC     ROUND(
# MAGIC         COALESCE(d.custo_plano_saude_dependentes, 0)
# MAGIC         /
# MAGIC         NULLIF(
# MAGIC             t.custo_plano_saude_titulares
# MAGIC             + COALESCE(d.custo_plano_saude_dependentes, 0),
# MAGIC             0
# MAGIC         )
# MAGIC         * 100.0,
# MAGIC         2
# MAGIC     ) AS percentual_custo_dependentes
# MAGIC
# MAGIC FROM titulares t
# MAGIC
# MAGIC LEFT JOIN dependentes d
# MAGIC     ON t.ano = d.ano
# MAGIC
# MAGIC WHERE
# MAGIC     t.ano >= 2010
# MAGIC
# MAGIC ORDER BY
# MAGIC     t.ano;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.13. Conclusão da Qual é o impacto dos dependentes nos custos de plano de saúde/odontológico?
# MAGIC
# MAGIC Para avaliar o impacto financeiro dos dependentes foram realizadas **duas análises complementares**. A primeira avaliou a evolução dos custos do plano de saúde dos próprios dependentes ao longo do tempo. A segunda comparou esses valores com os custos do plano de saúde dos titulares, permitindo mensurar a participação dos dependentes no custo total desse benefício.
# MAGIC
# MAGIC ### Análise 1 — Evolução do custo do plano de saúde dos dependentes
# MAGIC
# MAGIC A primeira consulta teve como objetivo analisar **como evoluíram os custos do plano de saúde dos dependentes ao longo dos anos**, considerando a quantidade de dependentes registrada, o custo total anual e o custo médio por dependente.
# MAGIC
# MAGIC O custo total anual dos dependentes passou de **R$ 2.613,74 em 2010** para valores progressivamente maiores nos anos seguintes, atingindo seu maior valor em **2021, com R$ 44.684,69**. Posteriormente, caiu para R$ 33.960,99 em 2022, R$ 17.355,54 em 2023 e **R$ 15.275,77 em 2024**.
# MAGIC
# MAGIC Essa redução do custo total nos anos mais recentes ocorre simultaneamente à diminuição da quantidade de dependentes registrada. Em 2021 havia 57 dependentes na análise, enquanto em 2024 havia 23.
# MAGIC
# MAGIC O custo médio por dependente apresenta comportamento diferente do custo total. Ele passou de **R$ 261,37 em 2010** para **R$ 664,16 em 2024**, tendo alcançado **R$ 828,32 em 2022**.
# MAGIC
# MAGIC **Conclusão da primeira análise:** o custo total do plano de saúde dos dependentes é influenciado tanto pelo **número de dependentes** quanto pelo **custo médio individual**. Dessa forma, a redução observada no custo total nos anos mais recentes não deve ser interpretada isoladamente como redução do custo do benefício, pois ocorreu também uma diminuição relevante da população de dependentes registrada.
# MAGIC
# MAGIC ### Análise 2 — Participação dos dependentes no custo total do plano de saúde
# MAGIC
# MAGIC A segunda consulta teve como objetivo mensurar **quanto os dependentes representam no custo total do plano de saúde**, comparando seus custos com aqueles correspondentes aos titulares.
# MAGIC
# MAGIC Entre 2010 e 2024, os dependentes representaram entre **23,49% e 32,20% do custo total do plano de saúde**. O maior percentual ocorreu em 2012, quando os dependentes responderam por **32,20%** do custo total, enquanto o menor foi observado em 2019, com **23,49%**.
# MAGIC
# MAGIC Em **2024**, o custo do plano de saúde dos titulares foi de **R$ 46.098,20**, enquanto o custo dos dependentes foi de **R$ 15.275,77**, resultando em um custo total de **R$ 61.373,97**. Os dependentes representaram, portanto, **24,89% do custo total do plano de saúde naquele ano**.
# MAGIC
# MAGIC **Conclusão da segunda análise:** os dependentes possuem **impacto financeiro relevante** no custo do plano de saúde. Em todos os anos analisados, sua participação correspondeu a aproximadamente um quarto ou mais do custo total do benefício, chegando a superar 30% em alguns períodos.
# MAGIC
# MAGIC ### Conclusão conjunta
# MAGIC
# MAGIC As duas análises demonstram que os dependentes constituem uma parcela relevante dos custos de assistência à saúde da empresa.
# MAGIC
# MAGIC A primeira análise mostrou que a evolução do custo total dos dependentes deve ser interpretada conjuntamente com a quantidade de dependentes e com o custo médio individual. A segunda mostrou que, ao comparar titulares e dependentes, estes últimos representaram entre **23,49% e 32,20% do custo total do plano de saúde** no período analisado.
# MAGIC
# MAGIC Esses resultados permitem ao RH e à gestão acompanhar não apenas o valor absoluto destinado aos dependentes, mas também sua participação no custo total do benefício, fornecendo informações para planejamento e acompanhamento das despesas com assistência à saúde.
# MAGIC
# MAGIC A base disponível no MVP, entretanto, **não contém o custo do plano odontológico dos dependentes**. Por esse motivo, não foi possível mensurar seu impacto financeiro, e a análise quantitativa desta questão ficou restrita ao **plano de saúde**.