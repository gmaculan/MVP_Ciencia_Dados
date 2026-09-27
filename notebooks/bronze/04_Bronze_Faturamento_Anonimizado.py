# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Faturamento
# MAGIC
# MAGIC Este notebook será destinado ao tratamento dos dados de **faturamento** no processo de transformação da camada Bronze para a camada Silver.
# MAGIC
# MAGIC Os dados atualmente disponíveis na camada Bronze serão avaliados quanto à sua estrutura, qualidade e adequação às necessidades do MVP. A partir dessa análise serão definidos os atributos que permanecerão na camada Silver e os tratamentos necessários para sua padronização, conversão de tipos, limpeza e organização.
# MAGIC
# MAGIC Os dados de faturamento serão utilizados posteriormente nas análises financeiras e gerenciais previstas no MVP, incluindo a evolução do faturamento ao longo do tempo, a participação dos clientes na receita e a comparação entre receitas e custos.
# MAGIC
# MAGIC O processamento seguirá a metodologia adotada nos notebooks anteriores: inicialmente será identificada a estrutura efetivamente existente na camada Bronze e definido o mapeamento dos atributos relevantes. Em seguida, serão realizadas as verificações de qualidade necessárias para orientar os tratamentos e a construção da tabela Silver.
# MAGIC
# MAGIC ## 1.1 Identificação das colunas e tipos de dados de Faturamento
# MAGIC
# MAGIC Como primeira etapa do tratamento Bronze → Silver, serão identificadas todas as colunas existentes em `workspace.bronze.faturamento_anonimizado` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Essa identificação permitirá compreender a estrutura efetivamente carregada na camada Bronze e servirá de base para a definição dos atributos que serão mantidos, descartados ou transformados na camada Silver.
# MAGIC
# MAGIC Nesta etapa inicial nenhuma alteração será realizada nos dados.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.faturamento_anonimizado;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1 Resultado da análise da identificação das colunas e tipos de dados de Faturamento**
# MAGIC
# MAGIC A tabela `workspace.bronze.faturamento_anonimizado` possui **48 colunas**, contemplando informações relacionadas à identificação do faturamento, cliente, datas de emissão, competência e vencimento, valores financeiros, tributos e retenções, além de campos administrativos e auxiliares existentes na fonte de origem.
# MAGIC
# MAGIC Os atributos apresentam diferentes tipos de dados na camada Bronze, incluindo `STRING`, `TIMESTAMP`, `BIGINT`, `DOUBLE` e `DECIMAL`.
# MAGIC
# MAGIC A partir dessa estrutura será realizada a seleção dos atributos necessários para o MVP. Para cada coluna será definido seu destino no processo Bronze → Silver, identificando os campos que serão mantidos, seus respectivos nomes e tipos na camada Silver e aqueles que não serão utilizados.
# MAGIC
# MAGIC Essa definição servirá de base para as verificações de qualidade e para os tratamentos posteriores dos dados de faturamento.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 Mapeamento dos atributos de Faturamento para a camada Silver
# MAGIC
# MAGIC Após a identificação da estrutura da tabela Bronze, foram selecionados os atributos de faturamento necessários para as análises previstas no MVP.
# MAGIC
# MAGIC O mapeamento abaixo define o destino de cada uma das 48 colunas existentes em `workspace.bronze.faturamento_anonimizado`. Para os atributos selecionados são definidos o nome e o tipo de dados pretendidos na camada Silver. Os demais campos não serão utilizados no escopo do MVP.
# MAGIC
# MAGIC Nesta etapa, o mapeamento representa a estrutura desejada para a camada Silver. As conversões de tipos, padronizações e demais tratamentos somente serão implementados após as verificações de qualidade dos dados.
# MAGIC
# MAGIC | Coluna Bronze | Tipo Bronze | Destino | Coluna Silver | Tipo Silver | Observação |
# MAGIC |---|---|---|---|---|---|
# MAGIC | `_c0` | STRING | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `NF` | DECIMAL(33,13) | FATURAMENTO | `nf` | STRING | Identificação da nota fiscal |
# MAGIC | `CR1` | STRING | FATURAMENTO | `cr1` | STRING | Componente da classificação CR - Departamento|
# MAGIC | `CR2` | STRING | FATURAMENTO | `cr2` | STRING | Componente da classificação CR - Cliente|
# MAGIC | `CR3` | STRING | FATURAMENTO | `cr3` | STRING | Componente da classificação CR - Alocação|
# MAGIC | `CR4` | STRING | FATURAMENTO | `cr4` | STRING | Componente da classificação CR - Sequencial|
# MAGIC | `Emissão` | TIMESTAMP | FATURAMENTO | `data_emissao` | DATE | Data de emissão |
# MAGIC | `Competência` | TIMESTAMP | FATURAMENTO | `data_competencia` | DATE | Competência do faturamento |
# MAGIC | `Cliente` | STRING | FATURAMENTO | `cliente` | STRING | Nome do cliente associado ao faturamento |
# MAGIC | `Valor` | DECIMAL(34,14) | FATURAMENTO | `valor` | DECIMAL(15,2) | Valor do faturamento |
# MAGIC | `Vencimento` | TIMESTAMP | FATURAMENTO | `data_vencimento` | DATE | Data de vencimento |
# MAGIC | `QTD` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `MunicípioISS` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `ISS` | DECIMAL(22,2) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `VALOR ISS 2` | DECIMAL(36,16) | FATURAMENTO | `valor_iss_2` | DECIMAL(15,2) | Valor do ISS calculado com alíquota de 2% |
# MAGIC | `VALOR ISS 5` | DECIMAL(35,15) | FATURAMENTO | `valor_iss_5` | DECIMAL(15,2) | Valor do ISS calculado com alíquota de 5% |
# MAGIC | `ISS RETIDO` | BIGINT | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `IR` | DECIMAL(38,18) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `PIS` | DOUBLE | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `COFINS` | DECIMAL(22,2) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `CSSL` | DECIMAL(22,2) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `INSS` | DECIMAL(38,18) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Outros` | BIGINT | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Líquido` | DECIMAL(34,14) | FATURAMENTO | `valor_liquido` | DECIMAL(15,2) | Valor líquido registrado na fonte |
# MAGIC | `Boleto` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Gerente` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Coordenador` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `CRCompleto` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Competência Contábil` | TIMESTAMP | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `AAAAMM EMISSÃO` | BIGINT | Não utilizada | — | — | Campo auxiliar/derivado da fonte |
# MAGIC | `AAAAMM COMPETÊNCIA` | BIGINT | Não utilizada | — | — | Campo auxiliar/derivado da fonte |
# MAGIC | `AAAAMM OFICIAL` | BIGINT | Não utilizada | — | — | Campo auxiliar/derivado da fonte |
# MAGIC | `AAAAMM            ISS` | BIGINT | Não utilizada | — | — | Campo auxiliar/derivado da fonte |
# MAGIC | `_c33` | BIGINT | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `EM ABERTO` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `_c35` | STRING | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `_c36` | STRING | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `_c37` | STRING | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `_c38` | BIGINT | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `DATA_RECEBIMENTO` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `VALOR_GLOSA` | STRING | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `_c41` | STRING | Não utilizada | — | — | Campo auxiliar da fonte |
# MAGIC | `Retenção IR` | DECIMAL(35,15) | FATURAMENTO | `retencao_ir` | DECIMAL(15,2) | Valor da retenção de IR |
# MAGIC | `Retenção PIS` | DECIMAL(36,16) | FATURAMENTO | `retencao_pis` | DECIMAL(15,2) | Valor da retenção de PIS |
# MAGIC | `Retenção COFINS` | DECIMAL(35,15) | FATURAMENTO | `retencao_cofins` | DECIMAL(15,2) | Valor da retenção de COFINS |
# MAGIC | `Retenção CSSL` | DECIMAL(36,16) | FATURAMENTO | `retencao_cssl` | DECIMAL(15,2) | Valor da retenção de CSSL |
# MAGIC | `Retenção INSS` | DECIMAL(35,15) | Não utilizada | — | — | Fora do escopo do MVP |
# MAGIC | `Retenção Outros` | BIGINT | Não utilizada | — | — | Fora do escopo do MVP |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.3 Diagnóstico dos registros de Faturamento
# MAGIC
# MAGIC Após a definição dos atributos que serão utilizados na camada Silver, serão realizadas verificações de qualidade nos registros de faturamento antes da aplicação das transformações Bronze → Silver.
# MAGIC
# MAGIC A `NF` será utilizada como principal referência para identificação dos registros de faturamento, exercendo nesta base função semelhante à desempenhada pelo `DRT` nas tabelas relacionadas aos vínculos empregatícios.
# MAGIC
# MAGIC As verificações compreenderão:
# MAGIC
# MAGIC - quantidade total de registros e quantidade de NFs;
# MAGIC - existência de NFs repetidas;
# MAGIC - existência de repetições do CR completo dentro do mesmo período;
# MAGIC - presença de valores nulos nos 17 atributos selecionados para a camada Silver.
# MAGIC
# MAGIC ### 1.3.1 Quantidade de registros e NFs
# MAGIC
# MAGIC Inicialmente será analisada a `NF`, utilizada como referência para identificação dos registros de Faturamento.
# MAGIC
# MAGIC A verificação permitirá identificar a quantidade total de registros, a quantidade de registros com `NF`, a existência de registros sem `NF`, a quantidade de NFs distintas e quantas NFs aparecem mais de uma vez na base.
# MAGIC
# MAGIC A existência de NFs repetidas não será interpretada automaticamente como duplicidade. Caso sejam encontradas ocorrências, os respectivos registros serão analisados antes de qualquer conclusão.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH contagem_nf AS (
# MAGIC     SELECT
# MAGIC         `NF`,
# MAGIC         COUNT(*) AS qtd_registros
# MAGIC     FROM workspace.bronze.faturamento_anonimizado
# MAGIC     WHERE `NF` IS NOT NULL
# MAGIC     GROUP BY `NF`
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     (SELECT COUNT(*)
# MAGIC      FROM workspace.bronze.faturamento_anonimizado) AS total_registros,
# MAGIC
# MAGIC     (SELECT COUNT(`NF`)
# MAGIC      FROM workspace.bronze.faturamento_anonimizado) AS registros_com_nf,
# MAGIC
# MAGIC     (SELECT COUNT(*)
# MAGIC      FROM workspace.bronze.faturamento_anonimizado
# MAGIC      WHERE `NF` IS NULL) AS registros_sem_nf,
# MAGIC
# MAGIC     COUNT(*) AS nfs_distintas,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE WHEN qtd_registros > 1 THEN 1 ELSE 0 END
# MAGIC     ) AS nfs_repetidas,
# MAGIC
# MAGIC     COALESCE(
# MAGIC         SUM(
# MAGIC             CASE WHEN qtd_registros > 1 THEN qtd_registros ELSE 0 END
# MAGIC         ), 0
# MAGIC     ) AS registros_com_nf_repetida
# MAGIC
# MAGIC FROM contagem_nf;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.3.1 Resultado da análise da quantidade de registros e NFs**
# MAGIC
# MAGIC A tabela de Faturamento possui **5.128 registros**, dos quais **4.157 possuem `NF` preenchida** e **971 não possuem número de NF**.
# MAGIC
# MAGIC Entre os registros com NF foram identificadas **4.147 NFs distintas**. Destas, **8 aparecem mais de uma vez**, correspondendo a **18 registros**.
# MAGIC
# MAGIC A análise da origem dos dados indica que as repetições de NF estão associadas a **notas fiscais canceladas**, justificando a existência de mais de um registro relacionado ao mesmo número de NF. Dessa forma, essas ocorrências não serão interpretadas automaticamente como duplicidades de registros válidos.
# MAGIC
# MAGIC Os **971 registros sem `NF` serão considerados inválidos para a tabela de Faturamento**, uma vez que os registros desta base representam faturamentos realizados por meio de nota fiscal e, portanto, devem possuir o respectivo número de NF.
# MAGIC
# MAGIC Como regra de tratamento Bronze → Silver, **somente registros com `NF` preenchida poderão compor a tabela Silver de Faturamento**. As ocorrências relacionadas a NFs canceladas serão consideradas de acordo com as informações disponíveis na fonte, sem exclusão baseada exclusivamente na repetição do número da NF.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3.2 Verificação de CRs repetidos na mesma competência
# MAGIC
# MAGIC Após a análise das NFs, será verificada a existência de mais de uma nota fiscal associada ao mesmo CR dentro da mesma competência.
# MAGIC
# MAGIC Para essa verificação, o CR será representado pela combinação dos atributos `CR1`, `CR2`, `CR3` e `CR4`.
# MAGIC
# MAGIC De acordo com a regra de negócio adotada para o Faturamento neste MVP, **cada CR deve possuir no máximo uma nota fiscal em uma mesma competência**. Dessa forma, a existência de mais de uma NF para a mesma combinação de `CR1`, `CR2`, `CR3` e `CR4` na mesma `Competência` representa uma ocorrência que deverá ser analisada.
# MAGIC
# MAGIC Caso sejam encontradas ocorrências, os respectivos registros serão avaliados antes da definição de qualquer tratamento para a camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     `Competência`,
# MAGIC     `CR1`,
# MAGIC     `CR2`,
# MAGIC     `CR3`,
# MAGIC     `CR4`,
# MAGIC     COUNT(*) AS qtd_registros,
# MAGIC     COUNT(DISTINCT `NF`) AS qtd_nfs
# MAGIC FROM workspace.bronze.faturamento_anonimizado
# MAGIC WHERE `NF` IS NOT NULL
# MAGIC GROUP BY
# MAGIC     `Competência`,
# MAGIC     `CR1`,
# MAGIC     `CR2`,
# MAGIC     `CR3`,
# MAGIC     `CR4`
# MAGIC HAVING COUNT(DISTINCT `NF`) > 1
# MAGIC ORDER BY
# MAGIC     `Competência`,
# MAGIC     `CR1`,
# MAGIC     `CR2`,
# MAGIC     `CR3`,
# MAGIC     `CR4`;

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH ocorrencias AS (
# MAGIC     SELECT
# MAGIC         YEAR(`Competência`) AS ano,
# MAGIC         `Competência`,
# MAGIC         `Cliente`,
# MAGIC         `CR1`,
# MAGIC         `CR2`,
# MAGIC         `CR3`,
# MAGIC         `CR4`,
# MAGIC         COUNT(DISTINCT `NF`) AS qtd_nfs
# MAGIC     FROM workspace.bronze.faturamento_anonimizado
# MAGIC     WHERE `NF` IS NOT NULL
# MAGIC     GROUP BY
# MAGIC         YEAR(`Competência`),
# MAGIC         `Competência`,
# MAGIC         `Cliente`,
# MAGIC         `CR1`,
# MAGIC         `CR2`,
# MAGIC         `CR3`,
# MAGIC         `CR4`
# MAGIC     HAVING COUNT(DISTINCT `NF`) > 1
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     ano,
# MAGIC     `Cliente`,
# MAGIC     COUNT(*) AS qtd_ocorrencias
# MAGIC FROM ocorrencias
# MAGIC GROUP BY
# MAGIC     ano,
# MAGIC     `Cliente`
# MAGIC ORDER BY
# MAGIC     ano,
# MAGIC     qtd_ocorrencias DESC,
# MAGIC     `Cliente`;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.3.2 Resultado da análise da verificação de CRs repetidos na mesma competência**
# MAGIC
# MAGIC A primeira verificação identificou **434 ocorrências em que uma mesma combinação de `CR1`, `CR2`, `CR3` e `CR4` apresenta mais de uma NF distinta na mesma competência**.
# MAGIC
# MAGIC Como essa situação contrariava uma **regra simplificadora inicialmente adotada para o MVP**, segundo a qual cada CR deveria estar associado a no máximo uma NF por competência, foi realizada uma segunda análise para verificar a distribuição dessas ocorrências por ano e cliente.
# MAGIC
# MAGIC O agrupamento demonstrou que essas ocorrências não estão restritas a poucos registros ou a uma situação pontual. Elas estão distribuídas ao longo de diferentes anos e entre diferentes clientes da base, indicando que a existência de múltiplas NFs para um mesmo CR em uma mesma competência faz parte do comportamento histórico dos dados de Faturamento.
# MAGIC
# MAGIC Dessa forma, a **regra simplificadora inicialmente adotada para o MVP**, de uma única NF por CR em cada competência, **não se mostrou compatível com o comportamento observado nos dados históricos** e não será utilizada como regra de validação ou de exclusão de registros na transformação Bronze → Silver.
# MAGIC
# MAGIC Também não será realizada qualquer manipulação destinada a eliminar essas ocorrências concomitantes. Os dados disponíveis não fornecem um critério objetivo e imparcial que permita determinar quais dessas NFs deveriam ser preservadas ou descartadas. A exclusão arbitrária de registros alteraria a informação existente na fonte e poderia produzir distorções nas análises posteriores.
# MAGIC
# MAGIC Assim, as diferentes NFs associadas ao mesmo CR e à mesma competência serão preservadas na camada Silver, desde que atendam aos demais critérios de qualidade definidos para os registros de Faturamento.
# MAGIC
# MAGIC Essa constatação também deverá ser considerada na revisão da modelagem do MVP. Como o modelo conceitual e lógico foram construídos pressupondo que a combinação entre CR e competência determina uma única NF, essa restrição será revista para permitir a representação de múltiplas notas fiscais associadas ao mesmo CR em uma mesma competência.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.3.4 Verificação de valores nulos nos atributos selecionados
# MAGIC
# MAGIC Após as verificações relacionadas às NFs e à ocorrência de múltiplas notas fiscais para o mesmo CR e competência, será analisada a presença de valores nulos nos **17 atributos selecionados para a camada Silver**.
# MAGIC
# MAGIC A análise será realizada somente sobre os registros que possuem `NF` preenchida, uma vez que os registros sem número de nota fiscal foram considerados inválidos para a tabela de Faturamento e não serão encaminhados para a camada Silver.
# MAGIC
# MAGIC O objetivo é identificar quais atributos apresentam ausência de informação e a quantidade de registros afetados, permitindo avaliar posteriormente se os valores nulos são compatíveis com a natureza de cada campo ou se exigem algum tratamento adicional.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros_validos,
# MAGIC
# MAGIC     SUM(CASE WHEN `NF` IS NULL THEN 1 ELSE 0 END) AS nulos_nf,
# MAGIC     SUM(CASE WHEN `CR1` IS NULL THEN 1 ELSE 0 END) AS nulos_cr1,
# MAGIC     SUM(CASE WHEN `CR2` IS NULL THEN 1 ELSE 0 END) AS nulos_cr2,
# MAGIC     SUM(CASE WHEN `CR3` IS NULL THEN 1 ELSE 0 END) AS nulos_cr3,
# MAGIC     SUM(CASE WHEN `CR4` IS NULL THEN 1 ELSE 0 END) AS nulos_cr4,
# MAGIC     SUM(CASE WHEN `Emissão` IS NULL THEN 1 ELSE 0 END) AS nulos_emissao,
# MAGIC     SUM(CASE WHEN `Competência` IS NULL THEN 1 ELSE 0 END) AS nulos_competencia,
# MAGIC     SUM(CASE WHEN `Cliente` IS NULL THEN 1 ELSE 0 END) AS nulos_cliente,
# MAGIC     SUM(CASE WHEN `Valor` IS NULL THEN 1 ELSE 0 END) AS nulos_valor,
# MAGIC     SUM(CASE WHEN `Vencimento` IS NULL THEN 1 ELSE 0 END) AS nulos_vencimento,
# MAGIC     SUM(CASE WHEN `VALOR ISS 2` IS NULL THEN 1 ELSE 0 END) AS nulos_valor_iss_2,
# MAGIC     SUM(CASE WHEN `VALOR ISS 5` IS NULL THEN 1 ELSE 0 END) AS nulos_valor_iss_5,
# MAGIC     SUM(CASE WHEN `Líquido` IS NULL THEN 1 ELSE 0 END) AS nulos_valor_liquido,
# MAGIC     SUM(CASE WHEN `Retenção IR` IS NULL THEN 1 ELSE 0 END) AS nulos_retencao_ir,
# MAGIC     SUM(CASE WHEN `Retenção PIS` IS NULL THEN 1 ELSE 0 END) AS nulos_retencao_pis,
# MAGIC     SUM(CASE WHEN `Retenção COFINS` IS NULL THEN 1 ELSE 0 END) AS nulos_retencao_cofins,
# MAGIC     SUM(CASE WHEN `Retenção CSSL` IS NULL THEN 1 ELSE 0 END) AS nulos_retencao_cssl
# MAGIC
# MAGIC FROM workspace.bronze.faturamento_anonimizado
# MAGIC WHERE `NF` IS NOT NULL;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.3.4 Resultado da verificação de valores nulos nos atributos selecionados**
# MAGIC
# MAGIC A verificação foi realizada sobre os **4.157 registros com `NF` preenchida**, correspondentes aos registros considerados válidos para continuidade no processo Bronze → Silver.
# MAGIC
# MAGIC Não foram identificados valores nulos em nenhum dos **17 atributos selecionados para a camada Silver**: `NF`, `CR1`, `CR2`, `CR3`, `CR4`, `Emissão`, `Competência`, `Cliente`, `Valor`, `Vencimento`, `VALOR ISS 2`, `VALOR ISS 5`, `Líquido`, `Retenção IR`, `Retenção PIS`, `Retenção COFINS` e `Retenção CSSL`.
# MAGIC
# MAGIC Dessa forma, não será necessário realizar tratamento de valores nulos nesses atributos durante a construção da camada Silver.
# MAGIC
# MAGIC Com essa verificação, ficam concluídas as análises de qualidade dos dados de Faturamento necessárias antes das transformações Bronze → Silver.