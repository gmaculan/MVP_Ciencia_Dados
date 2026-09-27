# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Alocação
# MAGIC
# MAGIC Este notebook será destinado à análise e ao tratamento dos dados de **Alocação** no processo de transformação da camada Bronze para a camada Silver.
# MAGIC
# MAGIC A Alocação representa a associação do profissional a uma determinada alocação ao longo de sua permanência na empresa e possui papel importante na integração das informações utilizadas pelo MVP, permitindo posteriormente relacionar informações de profissionais, custos e faturamento nas consultas analíticas.
# MAGIC
# MAGIC ## Limitação da fonte de dados
# MAGIC
# MAGIC A fonte de Alocação utilizada neste projeto representa **apenas parte do histórico disponível na empresa**.
# MAGIC
# MAGIC Durante determinado período, o controle das alocações foi realizado por meio de planilha. Posteriormente, essas informações passaram a ser registradas em um **sistema específico**, deixando de ser mantidas integralmente na fonte utilizada neste MVP.
# MAGIC
# MAGIC O acesso aos dados desse sistema não foi disponibilizado para a realização do projeto. Consequentemente, a base disponível não permite reconstruir todo o histórico de alocações da empresa e deve ser interpretada considerando essa limitação de cobertura.
# MAGIC
# MAGIC A ausência de registros após determinado período não representa necessariamente inexistência de alocações, mas uma consequência da mudança da fonte utilizada para seu registro.
# MAGIC
# MAGIC Diferentemente de outras situações em que podem ser adotadas premissas para demonstração analítica, **não será realizada extrapolação dos dados de Alocação**. Serão utilizados exclusivamente os registros efetivamente disponíveis na fonte.
# MAGIC
# MAGIC Essa limitação será tratada por meio da **temporalidade das consultas realizadas no MVP**. As diferentes fontes de dados não precisam necessariamente apresentar a mesma abrangência temporal. Dessa forma, cada consulta será realizada considerando o período para o qual existam dados adequados nas fontes necessárias à análise.
# MAGIC
# MAGIC Por exemplo, uma consulta de fluxo de caixa poderá utilizar dados referentes ao período de 2015 a 2025, enquanto uma consulta dependente das informações de Alocação poderá utilizar um intervalo diferente e mais restrito, determinado pela cobertura efetivamente existente nessa fonte.
# MAGIC
# MAGIC Essa abordagem permite demonstrar as capacidades analíticas da proposta de ERP sem criar registros inexistentes ou atribuir às fontes uma cobertura temporal que elas não possuem.
# MAGIC
# MAGIC O processamento seguirá a metodologia adotada nos notebooks anteriores. Inicialmente será identificada a estrutura efetivamente disponível na camada Bronze e definido o mapeamento dos atributos relevantes para o MVP. Em seguida, serão realizadas as verificações de qualidade necessárias antes da construção da respectiva estrutura na camada Silver.
# MAGIC
# MAGIC ## 1.1 Identificação das colunas e tipos de dados de Alocação
# MAGIC
# MAGIC Como primeira etapa do tratamento Bronze → Silver, serão identificadas todas as colunas existentes em `workspace.bronze.alocacao_anonimizado` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Essa identificação permitirá compreender a estrutura efetivamente carregada na camada Bronze e servirá de base para a definição dos atributos que serão mantidos, descartados ou transformados na camada Silver.
# MAGIC
# MAGIC Nesta etapa inicial nenhuma alteração será realizada nos dados.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.alocacao_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 Mapeamento dos atributos de Alocação para a camada Silver
# MAGIC
# MAGIC Após a identificação da estrutura existente na camada Bronze, foram selecionados os atributos necessários para representar as informações de Alocação utilizadas no escopo do MVP.
# MAGIC
# MAGIC Os atributos selecionados permitem identificar o vínculo do profissional por meio do DRT, o profissional associado, sua alocação principal, a atividade e o nível registrados, além da data de início da respectiva alocação.
# MAGIC
# MAGIC | Coluna Bronze | Coluna Silver | Tipo Silver | Descrição |
# MAGIC |---|---|---|---|
# MAGIC | `DRT` | `drt` | STRING | Identificação do vínculo do profissional |
# MAGIC | `NOME REDUZIDO` | `nome_reduzido` | STRING | Nome reduzido do profissional |
# MAGIC | `ALOCAÇÃO PRINCIPAL` | `alocacao_principal` | STRING | Identificação da alocação principal |
# MAGIC | `ATIVIDADE` | `atividade` | STRING | Atividade exercida na alocação |
# MAGIC | `NÍVEL` | `nivel` | STRING | Nível associado à atuação do profissional |
# MAGIC | `INÍCIO` | `data_inicio` | DATE | Data de início da alocação |
# MAGIC
# MAGIC Os demais atributos existentes na camada Bronze não serão utilizados na tabela Silver de Alocação por não serem necessários às análises previstas no escopo do MVP.
# MAGIC
# MAGIC Os tipos apresentados representam a estrutura pretendida para a camada Silver. A conversão e a padronização dos dados serão realizadas posteriormente, após a avaliação da qualidade dos atributos selecionados.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.3 Validação inicial dos atributos selecionados
# MAGIC
# MAGIC A primeira verificação tem como objetivo avaliar a qualidade básica dos seis atributos selecionados para a camada Silver.
# MAGIC
# MAGIC Serão verificadas a quantidade total de registros, a quantidade de DRTs distintos, a ocorrência de valores nulos em cada atributo e as datas mínima e máxima de início das alocações disponíveis.
# MAGIC
# MAGIC A identificação do intervalo temporal é particularmente relevante nesta fonte, pois os dados disponíveis representam apenas parte do histórico de Alocação. Essa verificação permitirá estabelecer a cobertura efetivamente existente na base antes da realização das consultas analíticas do MVP.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC     COUNT(DISTINCT `DRT`) AS drts_distintos,
# MAGIC
# MAGIC     SUM(CASE WHEN `DRT` IS NULL THEN 1 ELSE 0 END) AS nulos_drt,
# MAGIC     SUM(CASE WHEN `NOME REDUZIDO` IS NULL THEN 1 ELSE 0 END) AS nulos_nome_reduzido,
# MAGIC     SUM(CASE WHEN `ALOCAÇÃO PRINCIPAL` IS NULL THEN 1 ELSE 0 END) AS nulos_alocacao_principal,
# MAGIC     SUM(CASE WHEN `ATIVIDADE` IS NULL THEN 1 ELSE 0 END) AS nulos_atividade,
# MAGIC     SUM(CASE WHEN `NÍVEL` IS NULL THEN 1 ELSE 0 END) AS nulos_nivel,
# MAGIC     SUM(CASE WHEN `INÍCIO` IS NULL THEN 1 ELSE 0 END) AS nulos_data_inicio,
# MAGIC
# MAGIC     MIN(`INÍCIO`) AS primeira_data_inicio,
# MAGIC     MAX(`INÍCIO`) AS ultima_data_inicio
# MAGIC
# MAGIC FROM workspace.bronze.alocacao_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.3 Resultado da análise da validação inicial dos atributos selecionados**
# MAGIC
# MAGIC Foram identificados cinco registros sem preenchimento em `NOME REDUZIDO`. A análise dessas ocorrências demonstrou que todos correspondem a **estagiários**, que apresentam também um padrão de DRT diferente daquele utilizado para os demais profissionais considerados no projeto.
# MAGIC
# MAGIC Os estagiários não fazem parte das análises previstas para o MVP e, portanto, esses registros **não serão utilizados na construção da tabela Silver de Alocação**.
# MAGIC
# MAGIC Dessa forma, os cinco valores nulos identificados em `NOME REDUZIDO` não representam uma inconsistência que necessite de tratamento por preenchimento, substituição ou inferência. Os respectivos registros serão desconsiderados por uma **regra de escopo do projeto**.
# MAGIC
# MAGIC Após essa exclusão, serão considerados **342 registros** para a construção da tabela Silver de Alocação.
# MAGIC
# MAGIC A análise também demonstrou que, entre os registros originalmente disponíveis, cada DRT aparece uma única vez. Assim, a fonte disponível não deve ser interpretada como um histórico completo das alterações de Alocação de cada profissional, mas como o conjunto de informações efetivamente disponível na planilha utilizada antes da migração desse controle para outro sistema.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.4 Premissas para apropriação dos custos às Alocações
# MAGIC
# MAGIC A entidade Alocação possui papel central na integração das informações gerenciais propostas para o MVP. É por meio dela que poderão ser relacionadas informações de profissionais, custos, despesas e faturamento, permitindo a construção de consultas destinadas à análise de custos e resultados das diferentes Alocações.
# MAGIC
# MAGIC O objetivo principal do MVP não é reproduzir integralmente os valores históricos da empresa, uma vez que nem todas as fontes e informações necessárias estão disponíveis. O objetivo é demonstrar como os dados de uma estrutura integrada de ERP podem ser organizados e relacionados para viabilizar consultas relevantes à gestão.
# MAGIC
# MAGIC Caso todas as informações operacionais estivessem disponíveis, a estrutura geral dessas consultas permaneceria essencialmente a mesma. A principal diferença estaria na eliminação ou revisão de algumas das simplificações adotadas no MVP e na utilização dos dados efetivamente registrados pela operação.
# MAGIC
# MAGIC ### Apropriação do custo de pessoal
# MAGIC
# MAGIC Na operação real, um profissional pode atuar simultaneamente em diferentes projetos, Alocações ou atividades administrativas. A apropriação adequada de seu custo dependeria, portanto, do registro das horas dedicadas a cada uma dessas atividades.
# MAGIC
# MAGIC Os dados de apontamento de horas dos profissionais não estão disponíveis nas fontes utilizadas neste projeto. Por esse motivo, foi adotada uma **simplificação para o MVP**, segundo a qual cada profissional será associado a apenas uma Alocação.
# MAGIC
# MAGIC Consequentemente, para fins das consultas desenvolvidas no projeto, o custo de cada profissional será integralmente apropriado à sua Alocação.
# MAGIC
# MAGIC O custo de pessoal poderá considerar salário e benefícios e, caso sejam incorporados ao MVP por meio de cálculo, encargos e provisões relacionados ao profissional, como FGTS, 13º salário e férias.
# MAGIC
# MAGIC Em uma implementação operacional do ERP, essa simplificação poderia ser substituída pelo apontamento efetivo das horas de cada profissional, permitindo distribuir seu custo entre diferentes Alocações.
# MAGIC
# MAGIC ### Apropriação de outros custos e despesas
# MAGIC
# MAGIC Além do custo de pessoal, uma Alocação poderá receber parcelas de outros custos e despesas da empresa.
# MAGIC
# MAGIC Para o MVP, os valores relacionados a **Fornecedores e PJs** poderão ser apropriados às Alocações por meio do mecanismo de rateio previsto no modelo.
# MAGIC
# MAGIC Como não estão disponíveis informações que permitam reproduzir os critérios de rateio efetivamente utilizados pela empresa, será adotado no MVP um **rateio igualitário entre as Alocações disponíveis nos dados utilizados pelo projeto**.
# MAGIC
# MAGIC É importante destacar que essas Alocações não representam necessariamente o conjunto completo de Alocações existentes na empresa em cada período. A fonte disponível possui cobertura parcial: existem Alocações anteriores, concomitantes e posteriores às registradas na base que não puderam ser mapeadas devido à indisponibilidade de fontes complementares e do sistema para o qual esse controle foi posteriormente migrado.
# MAGIC
# MAGIC Pela mesma razão, podem existir profissionais para os quais não seja possível determinar, a partir dos dados disponíveis, uma Alocação explícita. A ausência dessa associação no MVP não deve ser interpretada como evidência de que o profissional não estivesse alocado, mas como uma limitação das fontes disponibilizadas para o projeto.
# MAGIC
# MAGIC O rateio será realizado, portanto, exclusivamente sobre o conjunto de Alocações que puder ser representado a partir dos dados disponíveis no MVP. Não haverá tentativa de criar ou inferir Alocações ausentes para completar artificialmente o histórico.
# MAGIC
# MAGIC Também não serão utilizados critérios alternativos de rateio, como faturamento, quantidade de profissionais ou custo de pessoal. Além de não haver informações que indiquem que esses critérios correspondam à prática efetivamente utilizada pela empresa, sua aplicação poderia produzir distribuições variáveis entre períodos e Alocações, introduzindo uma complexidade artificial que não contribuiria para o objetivo do MVP.
# MAGIC
# MAGIC O **rateio igualitário** foi escolhido por constituir uma regra simples, objetiva e claramente identificável como uma premissa do projeto. Seu propósito não é reproduzir a apropriação histórica efetivamente realizada pela empresa, mas permitir a demonstração das consultas gerenciais que relacionam despesas, custos e Alocações.
# MAGIC
# MAGIC Em uma implementação completa do ERP, com acesso ao conjunto integral de Alocações, aos apontamentos dos profissionais e aos critérios efetivamente definidos pela empresa, essas simplificações poderiam ser substituídas pelas regras operacionais reais, mantendo-se essencialmente a mesma lógica das consultas analíticas propostas.
# MAGIC
# MAGIC ### Alocações com e sem faturamento
# MAGIC
# MAGIC As Alocações podem representar tanto projetos ou atividades que geram faturamento quanto atividades administrativas que não possuem receita diretamente associada.
# MAGIC
# MAGIC Dessa forma, a existência de custos em uma Alocação não implica necessariamente a existência de faturamento correspondente. Essa distinção permitirá que as consultas do MVP representem tanto Alocações geradoras de receita quanto estruturas administrativas e demais atividades necessárias à operação da empresa.
# MAGIC
# MAGIC ### Finalidade analítica
# MAGIC
# MAGIC As simplificações adotadas neste MVP decorrem principalmente da disponibilidade parcial das fontes e não representam limitações conceituais da proposta de ERP.
# MAGIC
# MAGIC O propósito é demonstrar que, uma vez integradas as informações de pessoal, benefícios, despesas, fornecedores, PJs, Alocações e faturamento, torna-se possível construir consultas gerenciais para analisar, entre outros aspectos, a composição dos custos das Alocações, sua evolução ao longo do tempo e, quando houver faturamento associado, a relação entre custos, receitas e resultado.
# MAGIC
# MAGIC Em uma implementação completa do ERP, a disponibilidade dos dados operacionais efetivos permitiria aumentar a precisão dessas análises e substituir as premissas simplificadoras adotadas no MVP, sem alterar substancialmente a lógica das consultas propostas.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.5 Conclusão da análise de Alocação
# MAGIC
# MAGIC A análise da fonte de Alocação demonstrou que os atributos selecionados apresentam qualidade suficiente para sua utilização no escopo do MVP.
# MAGIC
# MAGIC A camada Bronze contém 347 registros, correspondentes a 347 DRTs distintos. Foram identificados cinco registros sem preenchimento em `NOME REDUZIDO`, todos referentes a estagiários, que não fazem parte do escopo das análises propostas. Dessa forma, serão considerados 342 registros para a construção da camada Silver de Alocação.
# MAGIC
# MAGIC A fonte disponível possui cobertura parcial e não representa necessariamente todas as Alocações existentes na empresa nem todo o histórico de movimentações dos profissionais. Parte dessas informações estava disponível em fontes complementares e, posteriormente, em outro sistema ao qual não se obteve acesso para a realização do projeto.
# MAGIC
# MAGIC Por esse motivo, não serão criadas, inferidas ou extrapoladas Alocações para períodos ou profissionais sem informação disponível. As análises serão realizadas exclusivamente a partir das associações que puderem ser estabelecidas objetivamente com os dados utilizados no MVP.
# MAGIC
# MAGIC Para viabilizar as consultas propostas, será adotada a simplificação de uma única Alocação por profissional, uma vez que não estão disponíveis os apontamentos de horas necessários para distribuir o custo de um mesmo profissional entre diferentes Alocações.
# MAGIC
# MAGIC Da mesma forma, os custos e despesas de Fornecedores e PJs serão distribuídos de forma igualitária entre as Alocações representadas pelos dados utilizados no projeto, constituindo uma premissa simplificadora para permitir a demonstração das consultas gerenciais.
# MAGIC
# MAGIC Essas limitações afetam a abrangência e a representatividade dos resultados obtidos com as fontes disponíveis, mas não alteram o objetivo central do MVP: demonstrar como uma estrutura integrada de dados pode permitir consultas envolvendo profissionais, custos, despesas, faturamento e Alocações.
# MAGIC
# MAGIC Em uma implementação completa do ERP, com disponibilidade integral dos dados operacionais, as mesmas estruturas de consulta poderiam ser utilizadas com maior abrangência e precisão, substituindo-se as simplificações adotadas no MVP pelos critérios efetivamente utilizados pela empresa.