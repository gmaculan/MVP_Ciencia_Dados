# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Salários e Benefícios
# MAGIC
# MAGIC Este notebook será destinado à análise e à transformação dos dados relacionados a **salários e benefícios** dos empregados, dando continuidade ao processo de construção da camada Silver.
# MAGIC
# MAGIC As duas informações serão tratadas no mesmo notebook por representarem componentes diretamente relacionados ao custo dos empregados e permitirem, posteriormente, análises integradas sobre remuneração, benefícios e evolução dos custos de pessoal.
# MAGIC
# MAGIC O processamento seguirá a mesma metodologia adotada para `EMPREGADO`: inicialmente será analisada a estrutura disponível na camada Bronze, identificando os atributos relevantes e definindo seu destino na camada Silver. Em seguida, serão realizadas as análises de qualidade necessárias e, posteriormente, os tratamentos de padronização, conversão de tipos e demais transformações necessárias para a construção das tabelas Silver.
# MAGIC
# MAGIC Embora salários e benefícios sejam tratados no mesmo notebook, suas estruturas serão analisadas separadamente, respeitando as características e regras de negócio de cada conjunto de dados.
# MAGIC
# MAGIC ## 1.1 Salários
# MAGIC
# MAGIC A análise será iniciada pelos dados de **salários**, com o objetivo de compreender a estrutura disponível na camada Bronze e definir os atributos necessários para representar o histórico salarial dos vínculos empregatícios na camada Silver.
# MAGIC
# MAGIC Nesta etapa, serão avaliados os campos existentes, seus tipos de dados e sua relação com o `DRT`, que identifica o vínculo empregatício. A partir dessa análise será definido o mapeamento dos atributos da origem para a estrutura de `SALÁRIO` na camada Silver.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.1 Identificação das colunas e tipos de dados
# MAGIC
# MAGIC O primeiro passo da análise consiste em identificar todas as colunas existentes na tabela `workspace.bronze.salario_anonimizado` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Essa verificação permite conhecer a estrutura efetivamente carregada na camada Bronze antes da definição das transformações para a camada Silver. A partir desse resultado, cada atributo será analisado quanto ao seu significado, tipo de dado, necessidade analítica e destino na estrutura de `SALÁRIO`.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações ou exclusões de atributos. O objetivo é identificar e documentar a estrutura atual da tabela Bronze.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.salario_anonimizado;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.2 Mapeamento de atributos — SALÁRIO: Bronze → Silver
# MAGIC
# MAGIC A tabela `workspace.bronze.salario_anonimizado` possui **26 colunas**. A estrutura de origem contém informações relacionadas ao histórico salarial dos vínculos empregatícios, incluindo valores de salário e remuneração, datas de alteração, cargos, motivos de alteração e campos auxiliares utilizados na origem.
# MAGIC
# MAGIC Na transformação Bronze → Silver, cada atributo será avaliado quanto ao seu significado, necessidade analítica e destino. A existência de uma coluna na Bronze não implica sua permanência em `SALÁRIO`.
# MAGIC
# MAGIC A coluna **Observação / destino** registrará se o atributo:
# MAGIC
# MAGIC - será **utilizado em SALÁRIO**;
# MAGIC - será **tratado em outra entidade/tabela**;
# MAGIC - será **derivado/recalculado**;
# MAGIC - **não será utilizado** no escopo do MVP; ou
# MAGIC - permanecerá **a definir**, enquanto sua utilização estiver sendo analisada.
# MAGIC
# MAGIC Quando o atributo não fizer parte de `SALÁRIO`, o cabeçalho e o tipo Silver serão representados por `—`. Enquanto ainda não houver elementos suficientes para determinar seu tratamento, será utilizado `A definir`.
# MAGIC
# MAGIC | # | Cabeçalho Bronze | Tipo Bronze | Cabeçalho Silver | Tipo Silver | Observação / destino |
# MAGIC |---:|---|---|---|---|---|
# MAGIC | 1 | `UNIDADE` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 2 | `DRT` | BIGINT | `drt` | STRING | **Utilizado em SALÁRIO.** Identifica o vínculo empregatício. Convertido para STRING por possuir natureza de identificador. |
# MAGIC | 3 | `NOME REDUZIDO` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 4 | `DATA DA ALTERAÇÃO` | STRING | `data_alteracao` | DATE | **Utilizado em SALÁRIO.** Representa a data de vigência da alteração registrada no histórico salarial. Será convertida de STRING para DATE. |
# MAGIC | 5 | `HORAS (REM. TOTAL)4` | DECIMAL(35,15) | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 6 | `SALÁRIO` | DECIMAL(34,14) | — | — | **Não utilizado em SALÁRIO.** Informação redundante em relação ao valor salarial selecionado para a camada Silver.|
# MAGIC | 7 | `REMUNERAÇÃO TOTAL` | DECIMAL(34,14) | salario | DECIMAL(15,2) | **Utilizado em SALÁRIO.** Representa o valor da remuneração associado ao vínculo na respectiva data de alteração. Padronizado como DECIMAL(15,2) para representação monetária na camada Silver. |
# MAGIC | 8 | `MOTIVO` | STRING | `motivo` | STRING | **Utilizado em SALÁRIO.** Registra o motivo associado à alteração salarial. |
# MAGIC | 9 | `OBSERVAÇÕES` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 10 | `ÍNDICE` | DECIMAL(38,18) | indice_alteracao | DECIMAL(3,2) | **Utilizado em SALÁRIO.** Registra o índice da alteração salarial. |
# MAGIC | 11 | `COMPENSARÁ NA DATA BASE?` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 12 | `STATUS` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 13 | `OBS.2` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 14 | `CARGO` | STRING | `cargo` | STRING | **Utilizado em SALÁRIO.** Registra o cargo associado ao empregado no momento da alteração salarial. |
# MAGIC | 15 | `_c14` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 16 | `ÚLTIMA ATUALIZAÇÃO` | TIMESTAMP | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 17 | `POR` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 18 | `LINHA` | BIGINT | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 19 | `CONT.SES` | BIGINT | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 20 | `ÚLTIMA LINHA` | STRING | — | — | **Não utilizado em SALÁRIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 21 | `ENDEREÇO SALÁRIO` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 22 | `ÚLTIMO SALÁRIO` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 23 | `ENDEREÇO COMPLEMENTAR` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 24 | `ÚLTIMO COMPLEMENTAR` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 25 | `ENDEREÇO HORAS (REM. TOTAL)` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 26 | `HORAS (REM. TOTAL)25` | STRING | — | — | **Não utilizado em SALÁRIO.** Campo auxiliar da estrutura de origem sem necessidade analítica identificada para o MVP. |

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.3 Análise da quantidade de registros salariais por DRT
# MAGIC
# MAGIC Diferentemente de `EMPREGADO`, em que cada `DRT` corresponde a um único registro do vínculo empregatício, a tabela de salários possui natureza histórica. Dessa forma, um mesmo `DRT` pode possuir múltiplos registros, correspondentes às diferentes ocorrências registradas ao longo do vínculo.
# MAGIC
# MAGIC A repetição do `DRT` em `SALÁRIO`, portanto, não caracteriza por si só uma duplicidade.
# MAGIC
# MAGIC Nesta etapa será identificada a quantidade de registros salariais existente para cada `DRT` na camada Bronze. O resultado permitirá compreender a distribuição do histórico salarial entre os vínculos empregatícios e servirá de base para as análises posteriores de consistência desses registros.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT AS drt,
# MAGIC     COUNT(*) AS quantidade_registros_salariais
# MAGIC FROM workspace.bronze.salario_anonimizado
# MAGIC WHERE DRT IS NOT NULL
# MAGIC GROUP BY DRT
# MAGIC ORDER BY DRT, quantidade_registros_salariais DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.3  Resultado da análise da quantidade de registros salariais por DRT**
# MAGIC
# MAGIC A consulta identificou **347 DRTs distintos**, correspondentes aos 347 vínculos empregatícios considerados válidos na análise de `EMPREGADO`.
# MAGIC
# MAGIC Esses vínculos estão associados a um total de **1.512 registros salariais**. Entre os 347 DRTs, **76 possuem apenas um registro salarial**, enquanto **271 possuem dois ou mais registros**. A quantidade de registros por vínculo varia entre **1 e 29**.
# MAGIC
# MAGIC O resultado confirma a natureza histórica da tabela de salários. A ocorrência de múltiplos registros para um mesmo `DRT` é esperada e representa as diferentes ocorrências salariais registradas ao longo do vínculo empregatício, não caracterizando, por si só, duplicidade.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.1.4 Análise da consistência do histórico salarial
# MAGIC
# MAGIC Após identificar a quantidade de registros salariais existente para cada `DRT`, será analisada a consistência do histórico salarial de cada vínculo empregatício.
# MAGIC
# MAGIC A análise buscará identificar:
# MAGIC
# MAGIC - possíveis registros duplicados no histórico salarial;
# MAGIC - ocorrências em que uma alteração salarial posterior apresenta valor inferior ao registro imediatamente anterior.
# MAGIC
# MAGIC Para realizar a comparação cronológica, `DATA DA ALTERAÇÃO` será interpretada temporariamente como data durante a consulta de diagnóstico, uma vez que o atributo foi classificado como `STRING` na camada Bronze, apesar de representar uma data. Esse procedimento será utilizado exclusivamente para permitir a ordenação cronológica dos registros e não representa uma transformação definitiva do atributo na camada Bronze.
# MAGIC
# MAGIC A padronização de `DATA DA ALTERAÇÃO` e sua conversão definitiva para o tipo `DATE` serão realizadas posteriormente durante a transformação Bronze → Silver.
# MAGIC
# MAGIC A consulta apresentará somente os registros que atendam a pelo menos uma das condições analisadas, permitindo investigar eventuais inconsistências antes da construção da tabela `SALÁRIO` na camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC WITH base AS (
# MAGIC     SELECT
# MAGIC         DRT AS drt,
# MAGIC         `DATA DA ALTERAÇÃO` AS data_alteracao_original,
# MAGIC
# MAGIC         COALESCE(
# MAGIC             TRY_TO_DATE(`DATA DA ALTERAÇÃO`, 'd/M/yy'),
# MAGIC             TRY_TO_DATE(`DATA DA ALTERAÇÃO`, 'd/M/yyyy')
# MAGIC         ) AS data_alteracao,
# MAGIC
# MAGIC         `REMUNERAÇÃO TOTAL` AS salario,
# MAGIC         MOTIVO AS motivo
# MAGIC
# MAGIC     FROM workspace.bronze.salario_anonimizado
# MAGIC     WHERE DRT IS NOT NULL
# MAGIC ),
# MAGIC
# MAGIC historico AS (
# MAGIC     SELECT
# MAGIC         drt,
# MAGIC         data_alteracao_original,
# MAGIC         data_alteracao,
# MAGIC         salario,
# MAGIC         motivo,
# MAGIC
# MAGIC         LAG(salario) OVER (
# MAGIC             PARTITION BY drt
# MAGIC             ORDER BY data_alteracao
# MAGIC         ) AS salario_anterior,
# MAGIC
# MAGIC         COUNT(*) OVER (
# MAGIC             PARTITION BY
# MAGIC                 drt,
# MAGIC                 data_alteracao_original,
# MAGIC                 salario,
# MAGIC                 motivo
# MAGIC         ) AS quantidade_ocorrencias
# MAGIC
# MAGIC     FROM base
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     drt,
# MAGIC     data_alteracao_original AS data_alteracao,
# MAGIC     salario,
# MAGIC     motivo
# MAGIC FROM historico
# MAGIC WHERE
# MAGIC       quantidade_ocorrencias > 1
# MAGIC    OR salario < salario_anterior
# MAGIC ORDER BY
# MAGIC     drt,
# MAGIC     data_alteracao;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.1.4 Resultado da análise da consistência do histórico salarial**
# MAGIC
# MAGIC A análise identificou ocorrências em que um mesmo `DRT` apresenta valores salariais repetidos ao longo de seu histórico. Entretanto, esses registros não constituem necessariamente tuplas duplicadas, pois podem apresentar diferenças em `DATA DA ALTERAÇÃO`, `MOTIVO` ou em ambos os atributos.
# MAGIC
# MAGIC Dessa forma, a repetição do valor salarial pode representar diferentes ocorrências dentro do histórico do vínculo e não deve ser eliminada apenas com base na igualdade do valor de `REMUNERAÇÃO TOTAL`.
# MAGIC
# MAGIC A análise também evidenciou limitações na estrutura e na tipagem dos dados de origem. Embora `DATA DA ALTERAÇÃO` represente uma informação temporal, o atributo foi carregado como `STRING`, além de apresentar diferentes formatos de representação de data. Essas características indicam que os dados de origem não estão estruturados e padronizados de forma adequada para utilização analítica direta.
# MAGIC
# MAGIC Essas limitações serão tratadas na transformação para a camada Silver, na qual os atributos selecionados serão tipados e padronizados de acordo com sua natureza e finalidade analítica.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 Benefícios
# MAGIC
# MAGIC Concluída a análise dos dados de salários, inicia-se a análise dos dados de **benefícios** dos empregados.
# MAGIC
# MAGIC Diferentemente das estruturas analisadas anteriormente, as informações necessárias para representar os benefícios não estão concentradas em uma única tabela na camada Bronze.
# MAGIC
# MAGIC A tabela `workspace.bronze.beneficio_anonimizado` contém informações relacionadas aos benefícios associados aos vínculos empregatícios, porém não registra os valores históricos necessários para a análise dos benefícios de ticket e plano de saúde. Esses valores serão obtidos a partir de três fontes complementares existentes na camada Bronze:
# MAGIC
# MAGIC - `workspace.bronze.valor_ticket_2010_2025`;
# MAGIC - `workspace.bronze.plano_saude_ate_2022`;
# MAGIC - `workspace.bronze.plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC Dessa forma, a construção das informações de benefícios na camada Silver exigirá a integração dos dados provenientes dessas diferentes fontes.
# MAGIC
# MAGIC Inicialmente, será analisada a estrutura de `workspace.bronze.beneficio_anonimizado`, identificando as informações efetivamente disponíveis nessa tabela e sua utilidade para o modelo. Posteriormente, serão analisadas as três fontes complementares responsáveis pelos valores históricos de ticket e plano de saúde.
# MAGIC
# MAGIC ### 1.2.1 Identificação das colunas e tipos de dados de BENEFÍCIO
# MAGIC
# MAGIC O primeiro passo consiste em identificar todas as colunas existentes na tabela `workspace.bronze.beneficio_anonimizado` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações ou exclusões de atributos. O objetivo é documentar a estrutura atual da tabela e identificar quais informações poderão ser aproveitadas na construção da camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.beneficio_anonimizado;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.2 Mapeamento de atributos — BENEFÍCIO: Bronze → Silver
# MAGIC
# MAGIC A tabela `workspace.bronze.beneficio_anonimizado` possui **22 colunas**. Embora a estrutura contenha atributos relacionados a diferentes benefícios, os valores históricos de ticket e plano de saúde que serão utilizados no MVP não estão adequadamente registrados nessa tabela e serão obtidos a partir das fontes complementares identificadas anteriormente.
# MAGIC
# MAGIC Na transformação Bronze → Silver, cada atributo será avaliado quanto ao seu significado, necessidade analítica e destino. A existência de uma coluna na Bronze não implica sua permanência em `BENEFÍCIO`.
# MAGIC
# MAGIC A coluna **Observação / destino** registrará se o atributo:
# MAGIC
# MAGIC - será **utilizado em BENEFÍCIO**;
# MAGIC - terá sua informação **obtida a partir de outra fonte Bronze**;
# MAGIC - será **derivado/recalculado**;
# MAGIC - **não será utilizado** no escopo do MVP; ou
# MAGIC - permanecerá **a definir**, enquanto sua utilização estiver sendo analisada.
# MAGIC
# MAGIC Quando o atributo não fizer parte de `BENEFÍCIO`, o cabeçalho e o tipo Silver serão representados por `—`. Enquanto ainda não houver elementos suficientes para determinar seu tratamento, será utilizado `A definir`.
# MAGIC
# MAGIC | # | Cabeçalho Bronze | Tipo Bronze | Cabeçalho Silver | Tipo Silver | Observação / destino |
# MAGIC |---:|---|---|---|---|---|
# MAGIC | 1 | `UNIDADE` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 2 | `DRT` | BIGINT | `drt` | STRING | **Utilizado em BENEFÍCIO.** Identifica o vínculo empregatício. Convertido para STRING por possuir natureza de identificador. |
# MAGIC | 3 | `NOME REDUZIDO` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 4 | `SEQUÊNCIA` | BIGINT | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 5 | `INÍCIO` | STRING | — | — | **Não utilizado em BENEFÍCIO.** A tabela de origem não será utilizada como fonte do histórico temporal dos valores dos benefícios. |
# MAGIC | 6 | `TÉRMINO` | STRING | — | — | **Não utilizado em BENEFÍCIO.** A tabela de origem não será utilizada como fonte do histórico temporal dos valores dos benefícios. |
# MAGIC | 7 | `VALOR BENEFÍCIOS` | DECIMAL(22,2) | `total_beneficios` | DECIMAL(15,2) |  **Derivado/recalculado.** O valor registrado na origem não será utilizado. Na camada Silver, `total_beneficios` será calculado a partir da soma dos valores dos benefícios considerados no escopo do MVP. |
# MAGIC | 8 | `TICKET REFEIÇÃO` | DECIMAL(22,2) | `ticket_refeicao` | DECIMAL(15,2) | **Obtido a partir de outra fonte Bronze.** O valor histórico utilizado no MVP será obtido a partir da fonte específica de valores de ticket. |
# MAGIC | 9 | `TICKET ALIMENTAÇÃO` | STRING | `ticket_alimentacao` | DECIMAL(15,2) | **Obtido a partir de outra fonte Bronze.** O valor histórico utilizado no MVP será obtido a partir da fonte específica de valores de ticket. |
# MAGIC | 10 | `SAÚDE` | DECIMAL(5,2) | `plano_saude` | DECIMAL(15,2) | **Obtido a partir de outra fonte Bronze.** O valor histórico utilizado no MVP será obtido a partir das fontes específicas de valores de plano de saúde. |
# MAGIC | 11 | `VT` | STRING | — | — | **Não utilizado em BENEFÍCIO.** O vale-transporte não será considerado no escopo do MVP. |
# MAGIC | 12 | `DENTAL` | DECIMAL(3,1) | — | — | **Não utilizado em BENEFÍCIO.** Informação da origem que não será utilizada como fonte para determinação dos valores históricos dos benefícios na camada Silver. |
# MAGIC | 13 | `BENEFÍCIO INDIRETO TR` | DECIMAL(22,2) | — | — | **Não utilizado em BENEFÍCIO.** Informação da origem que não será utilizada como fonte para determinação dos valores históricos dos benefícios na camada Silver. |
# MAGIC | 14 | `BENEFÍCIO 6` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 15 | `BENEFÍCIO 7` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 16 | `BENEFÍCIO 8` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 17 | `BENEFÍCIO 9` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 18 | `BENEFÍCIO 10` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 19 | `BENEFÍCIO 11` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 20 | `BENEFÍCIO 12` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 21 | `ÚLTIMA ATUALIZAÇÃO` | TIMESTAMP | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 22 | `POR` | STRING | — | — | **Não utilizado em BENEFÍCIO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC
# MAGIC #### Limitações identificadas na fonte
# MAGIC
# MAGIC A análise da estrutura de `workspace.bronze.beneficio_anonimizado` evidencia limitações importantes para sua utilização como fonte histórica dos valores dos benefícios.
# MAGIC
# MAGIC Na estrutura de origem, `TICKET REFEIÇÃO` corresponde ao benefício direto e `TICKET ALIMENTAÇÃO` ao benefício indireto. Esses valores estão registrados para alguns empregados, enquanto outros não possuem valores informados. Além disso, a tabela não preserva de forma consistente a evolução histórica dos valores dos benefícios ao longo do vínculo empregatício.
# MAGIC
# MAGIC A ausência de informações não está restrita aos registros históricos. Mesmo para empregados ativos, a tabela não contém de forma adequada os valores correspondentes a plano de saúde, plano dental e vale-transporte.
# MAGIC
# MAGIC Dessa forma, `beneficio_anonimizado` não será considerada fonte suficiente para a determinação dos valores históricos dos benefícios na camada Silver. Para os benefícios contemplados no escopo do MVP, os valores serão obtidos a partir das fontes específicas disponíveis na camada Bronze:
# MAGIC
# MAGIC - `workspace.bronze.valor_ticket_2010_2025`;
# MAGIC - `workspace.bronze.plano_saude_ate_2022`;
# MAGIC - `workspace.bronze.plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC Os atributos cujo tratamento depende dessas fontes permanecerão sujeitos à validação até que suas respectivas estruturas e conteúdos sejam analisados. Somente após essa análise será definida a composição definitiva dos benefícios e do atributo `total_beneficios` na camada Silver.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.3 Limitações dos dados de benefícios na origem
# MAGIC
# MAGIC A análise da estrutura de `workspace.bronze.beneficio_anonimizado` evidencia limitações importantes para sua utilização como fonte histórica dos valores dos benefícios.
# MAGIC
# MAGIC Na estrutura de origem, `TICKET REFEIÇÃO` corresponde ao benefício direto e `TICKET ALIMENTAÇÃO` ao benefício indireto. Esses valores aparecem registrados para alguns empregados, enquanto outros não possuem valores informados. Além disso, a tabela não preserva de forma consistente a evolução histórica dos valores dos benefícios ao longo do vínculo empregatício.
# MAGIC
# MAGIC A ausência de informações não está restrita aos registros históricos. Mesmo para empregados ativos, a tabela não contém de forma adequada os valores correspondentes a plano de saúde, plano dental e vale-transporte.
# MAGIC
# MAGIC Dessa forma, `beneficio_anonimizado` não será considerada fonte suficiente para a determinação dos valores históricos dos benefícios na camada Silver. Para os benefícios contemplados no escopo do MVP, os valores serão obtidos a partir das fontes específicas disponíveis na camada Bronze, especialmente `valor_ticket_2010_2025`, `plano_saude_ate_2022` e `plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC A tabela `beneficio_anonimizado` será utilizada somente para as informações que possam ser consideradas válidas e necessárias para caracterizar os benefícios associados aos vínculos, sem inferir valores ausentes a partir de seus registros.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.4 Análise dos registros de benefícios por DRT
# MAGIC
# MAGIC Após o mapeamento dos atributos e a identificação das limitações da fonte, será analisada a distribuição dos registros de benefícios entre os vínculos empregatícios.
# MAGIC
# MAGIC A consulta permitirá identificar os `DRT` existentes na tabela e visualizar os dados de benefícios registrados para cada vínculo. Como a fonte apresenta limitações de preenchimento e não constitui um histórico completo dos valores dos benefícios, o objetivo desta etapa é compreender como essas informações estão distribuídas na origem antes da integração com as fontes complementares.
# MAGIC
# MAGIC Serão apresentados o `DRT` e os campos relacionados aos benefícios considerados relevantes para esta análise, preservando os valores existentes na camada Bronze.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     DRT AS drt,
# MAGIC     `VALOR BENEFÍCIOS` AS valor_beneficios,
# MAGIC     `TICKET REFEIÇÃO` AS ticket_refeicao,
# MAGIC     `TICKET ALIMENTAÇÃO` AS ticket_alimentacao,
# MAGIC     `SAÚDE` AS saude
# MAGIC     FROM workspace.bronze.beneficio_anonimizado
# MAGIC WHERE DRT IS NOT NULL
# MAGIC ORDER BY DRT;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **Resultado da análise**
# MAGIC
# MAGIC A consulta retornou **342 DRTs**, sem repetição do identificador entre os registros apresentados.
# MAGIC
# MAGIC Diferentemente das bases de `EMPREGADO`, `SALÁRIO` e `FÉRIAS`, que preservam informações acumuladas ou históricas dos vínculos empregatícios, `beneficio_anonimizado` apresenta características de uma **fotografia de determinado momento da empresa**. Dessa forma, os DRTs existentes nessa tabela correspondem aos vínculos contemplados naquele momento, não representando necessariamente o conjunto histórico de empregados que passaram pela empresa.
# MAGIC
# MAGIC Essa característica também explica por que a quantidade de DRTs da tabela não deve ser diretamente comparada à quantidade total de vínculos históricos identificados em `EMPREGADO`.
# MAGIC
# MAGIC A análise dos campos de benefícios evidencia elevado grau de ausência de informações. Embora `VALOR BENEFÍCIOS` esteja preenchido nos 342 registros, **312 apresentam valor igual a zero**, enquanto apenas **30 apresentam valor diferente de zero**.
# MAGIC
# MAGIC O atributo `TICKET REFEIÇÃO` possui informação em apenas **34 registros**, sendo 308 valores nulos. `TICKET ALIMENTAÇÃO` não apresenta nenhum valor preenchido nos 342 registros analisados, enquanto `SAÚDE` apresenta valor em apenas **1 registro**.
# MAGIC
# MAGIC Além de representar uma fotografia de determinado momento, e não um histórico acumulado, os resultados confirmam que `beneficio_anonimizado` não possui informações suficientemente completas para reconstruir os valores dos benefícios dos vínculos empregatícios ao longo do tempo.
# MAGIC
# MAGIC Dessa forma, os valores históricos de ticket e plano de saúde utilizados na camada Silver serão obtidos a partir das respectivas fontes específicas. O atributo `total_beneficios` será recalculado a partir dos componentes considerados no escopo do MVP, não sendo utilizado o valor existente em `VALOR BENEFÍCIOS` como fonte para sua determinação.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.5 Análise da fonte histórica de valores de ticket
# MAGIC
# MAGIC Como identificado anteriormente, `beneficio_anonimizado` não preserva adequadamente o histórico dos valores dos benefícios. Para a construção das informações de ticket na camada Silver, será utilizada a fonte específica `workspace.bronze.valor_ticket_2010_2025`.
# MAGIC
# MAGIC Essa fonte será analisada inicialmente quanto à sua estrutura, permitindo identificar os atributos disponíveis, seus tipos de dados e a forma como os valores de ticket estão organizados ao longo do período contemplado.
# MAGIC
# MAGIC #### 1.2.5.1 Identificação das colunas e tipos de dados
# MAGIC
# MAGIC O primeiro passo consiste em identificar todas as colunas existentes em `workspace.bronze.valor_ticket_2010_2025` e seus respectivos tipos de dados.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações ou exclusões de atributos. O objetivo é documentar a estrutura atual da fonte antes de definir seu tratamento e sua utilização na camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.valor_ticket_2010_2025;

# COMMAND ----------

# MAGIC %md
# MAGIC #### 1.2.5.2 Análise dos períodos e valores de ticket Refeição e Alimentação
# MAGIC
# MAGIC A fonte `valor_ticket_2010_2025` contém o histórico dos valores de ticket aplicáveis aos empregados ao longo do tempo.
# MAGIC
# MAGIC Cada registro representa um período de vigência dos valores estabelecidos pela Convenção Coletiva de Trabalho (CCT). Na Nexa, a CCT ocorre no mês de setembro, quando são definidos os novos valores dos benefícios.
# MAGIC
# MAGIC Dessa forma, os valores registrados não seguem necessariamente o ano-calendário. Cada valor permanece vigente durante o respectivo período definido pela CCT, até a entrada em vigor dos valores estabelecidos pela convenção seguinte.
# MAGIC
# MAGIC A tabela não possui `DRT`, pois sua finalidade não é registrar o benefício individual de cada empregado, mas manter os valores de referência aplicáveis aos vínculos durante cada período de vigência. Esses valores eram aplicados aos empregados com base no piso estabelecido pela Convenção Coletiva de Trabalho da categoria.
# MAGIC
# MAGIC Nesta etapa serão analisados os registros existentes para verificar a representação dos períodos e a evolução dos valores ao longo do tempo.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM workspace.bronze.valor_ticket_2010_2025
# MAGIC ORDER BY `Período (CCT)`;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.5.2 Resultado da análise dos períodos e valores de ticket Refeição e Alimentação**
# MAGIC
# MAGIC A consulta apresentou **15 registros**, abrangendo períodos de vigência iniciados entre **2010 e 2025**.
# MAGIC
# MAGIC Os registros demonstram a evolução dos valores estabelecidos pela CCT ao longo do tempo. Para cada período são informados o valor diário do benefício direto, o valor total correspondente a 21 dias fixos e o valor mínimo mensal do benefício indireto.
# MAGIC
# MAGIC Observa-se que os períodos não possuem duração uniforme em toda a série. Até `2022 / 2023`, os registros são predominantemente anuais, enquanto os períodos `2023 / 2025` e `2025 / 2027` abrangem intervalos superiores a um ano. Dessa forma, a vigência dos valores deverá ser determinada a partir dos períodos efetivamente registrados na fonte, e não pela simples associação a um ano-calendário.
# MAGIC
# MAGIC Também foi identificada uma particularidade no período `2020 / 2021`, no qual o valor diário está registrado como `R$ 25,00 (Congelado na pandemia)`. Esse conteúdo combina o valor monetário com uma observação textual, o que explica a classificação desse atributo como `STRING` na camada Bronze e exigirá tratamento para sua utilização como valor numérico na camada Silver.
# MAGIC
# MAGIC A fonte apresenta, portanto, as informações necessárias para reconstruir historicamente os valores de ticket aplicáveis em cada período de vigência. Esses valores poderão posteriormente ser associados aos vínculos empregatícios de acordo com o período correspondente.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.6 Análise das fontes históricas de valores do plano de saúde
# MAGIC
# MAGIC Os valores históricos do plano de saúde utilizados no MVP estão distribuídos em duas fontes na camada Bronze:
# MAGIC
# MAGIC - `workspace.bronze.plano_saude_ate_2022`;
# MAGIC - `workspace.bronze.plano_saude_vital_de_2022_em_diante`.
# MAGIC
# MAGIC Essas fontes serão analisadas separadamente, pois representam períodos distintos do histórico do benefício. Após a compreensão de suas estruturas e conteúdos, será avaliada a forma adequada de integração dessas informações para a construção da camada Silver.
# MAGIC
# MAGIC #### 1.2.6.1 Estrutura da fonte de plano de saúde até 2022
# MAGIC
# MAGIC Inicialmente será analisada a estrutura de `workspace.bronze.plano_saude_ate_2022`, identificando as colunas existentes e seus respectivos tipos de dados.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações. O objetivo é compreender a organização da fonte antes de definir o tratamento dos valores históricos do plano de saúde.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.plano_saude_ate_2022;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC #### 1.2.6.2 Análise dos registros da fonte de plano de saúde até 2022
# MAGIC
# MAGIC A análise da estrutura de `plano_saude_ate_2022` identificou **15 colunas**, todas classificadas como `STRING`.
# MAGIC
# MAGIC Diferentemente das fontes analisadas anteriormente, as referências temporais estão representadas nas próprias colunas da tabela. Além de `MÊS REF.`, a estrutura contém colunas correspondentes a diferentes referências entre `out-09` e `jul-22`.
# MAGIC
# MAGIC Essa organização indica que a fonte possui uma estrutura em formato largo (*wide*), na qual diferentes períodos estão distribuídos horizontalmente em colunas.
# MAGIC
# MAGIC Antes de definir qualquer transformação para a camada Silver, será necessário analisar os registros existentes para compreender o significado das linhas, a relação entre `MÊS REF.` e as referências temporais e a forma como os valores históricos do plano de saúde estão registrados.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM workspace.bronze.plano_saude_ate_2022;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.6.2 Resultado da análise dos registros da fonte de plano de saúde até 2022**
# MAGIC
# MAGIC A consulta confirmou que `plano_saude_ate_2022` possui uma estrutura matricial em formato largo (*wide*), originalmente organizada para apresentação dos valores históricos do plano de saúde.
# MAGIC
# MAGIC A fonte contempla dois tipos de plano. O **Plano Especial** era destinado à equipe, enquanto o **Plano Executivo** era destinado à diretoria. Para cada plano, os valores são diferenciados por faixa etária, com os limites das faixas registrados em `MÊS REF.`.
# MAGIC
# MAGIC As referências temporais estão distribuídas horizontalmente nas colunas, abrangendo `out-09` até `jul-22`. Dessa forma, os valores do plano variam de acordo com o tipo de plano, a faixa etária e o respectivo período de vigência.
# MAGIC
# MAGIC Nos períodos iniciais do Plano Executivo, nem todas as faixas etárias apresentam valores. Essa ausência não deve ser interpretada automaticamente como falha ou perda de dados. Nesse período, os valores registrados refletem as faixas etárias necessárias para os integrantes da diretoria existentes naquele momento. A alteração observada em 2010, por exemplo, corresponde à mudança de faixa etária de um beneficiário em decorrência de sua idade.
# MAGIC
# MAGIC A partir de 2013, a fonte passa a apresentar valores para todas as faixas etárias do Plano Executivo. O preenchimento completo da tabela, entretanto, não significa que existissem integrantes da diretoria em todas essas faixas, mas apenas que a fonte passou a registrar a grade completa de valores do plano.
# MAGIC
# MAGIC Além dos valores dos planos, a fonte contém informações auxiliares, como identificação da operadora, percentuais de reajuste e IOF. A coluna `MÊS REF.` também é utilizada para armazenar cabeçalhos e outras informações de organização da planilha, demonstrando que a estrutura de origem não foi concebida diretamente para utilização analítica.
# MAGIC
# MAGIC Para utilização na camada Silver, será necessária posteriormente uma reorganização dessa estrutura, de modo que tipo de plano, faixa etária, período de vigência e valor possam ser representados como atributos próprios e utilizados na determinação histórica do custo do plano de saúde.

# COMMAND ----------

# MAGIC %md
# MAGIC #### 1.2.6.3 Estrutura da fonte de plano de saúde a partir de 2022
# MAGIC
# MAGIC Após a análise da fonte histórica de plano de saúde até 2022, será analisada `workspace.bronze.plano_saude_vital_de_2022_em_diante`, que contém os valores do plano de saúde referentes ao período posterior.
# MAGIC
# MAGIC Inicialmente serão identificadas as colunas existentes e seus respectivos tipos de dados, permitindo compreender a organização dessa nova fonte e verificar suas diferenças em relação à estrutura utilizada até 2022.
# MAGIC
# MAGIC Nesta etapa não serão realizadas transformações. A análise será utilizada posteriormente para definir a forma de integração das duas fontes históricas de plano de saúde na camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.plano_saude_vital_de_2022_em_diante;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC #### 1.2.6.4 Análise dos registros da fonte de plano de saúde a partir de 2022
# MAGIC
# MAGIC A análise da estrutura de `plano_saude_vital_de_2022_em_diante` identificou quatro colunas, todas classificadas como `STRING`.
# MAGIC
# MAGIC Diferentemente da fonte utilizada até 2022, os próprios nomes das colunas incorporam informações provenientes da organização da fonte original, como rede, região, tipo de plano e tipo de kit. Essa característica indica que a estrutura carregada na camada Bronze preserva a disposição original dos dados e não corresponde diretamente a uma estrutura tabular adequada para utilização analítica.
# MAGIC
# MAGIC Antes de definir o tratamento dessa fonte ou sua integração com o histórico anterior, serão analisados todos os registros existentes para compreender como as faixas etárias, os períodos de vigência e os respectivos valores estão efetivamente representados.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM workspace.bronze.plano_saude_vital_de_2022_em_diante;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.6.4 Resultado da análise dos registros da fonte de plano de saúde a partir de 2022**
# MAGIC
# MAGIC A consulta permitiu identificar a organização dos dados de plano de saúde a partir de 2022. A fonte está dividida em dois blocos correspondentes aos tipos de plano utilizados pela empresa.
# MAGIC
# MAGIC O **Plano Especial**, associado à Rede Nacional, era destinado à equipe, enquanto o **Plano Executivo**, associado à Rede Premium, era destinado à diretoria.
# MAGIC
# MAGIC Em ambos os casos, os valores do plano são diferenciados por faixa etária, utilizando as categorias `Até 18 anos`, `19 a 23`, `24 a 28`, `29 a 33`, `34 a 38`, `39 a 43`, `44 a 48`, `49 a 53`, `54 a 58` e `59 adiante`.
# MAGIC
# MAGIC Essa estrutura também permite compreender as faixas registradas numericamente na fonte histórica anterior, estabelecendo a correspondência entre os limites etários e as respectivas categorias.
# MAGIC
# MAGIC Para cada faixa etária, a fonte apresenta o respectivo valor unitário do plano de saúde. Embora também existam informações de quantidade de beneficiários e valor total, esses dados representam apenas uma fotografia da composição dos beneficiários em determinado momento e não são relevantes para a construção do histórico de valores do benefício.
# MAGIC
# MAGIC Dessa forma, para a construção da camada Silver serão considerados os valores unitários correspondentes a cada tipo de plano e faixa etária. As informações de quantidade de beneficiários e valor total não serão utilizadas.
# MAGIC
# MAGIC A vigência dos valores registrados nesta fonte tem início em **outubro de 2022**. Dessa forma, para a construção da camada Silver serão considerados os valores unitários correspondentes a cada tipo de plano e faixa etária, associados a essa vigência. As informações de quantidade de beneficiários e valor total não serão utilizadas, pois representam apenas uma fotografia da composição dos beneficiários em determinado momento.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Conclusão
# MAGIC
# MAGIC Neste notebook foram analisadas as fontes da camada Bronze relacionadas a **salários e benefícios**, permitindo compreender suas estruturas, características históricas e limitações antes da transformação para a camada Silver.
# MAGIC
# MAGIC A análise de `salario_anonimizado` confirmou sua natureza histórica. Um mesmo `DRT` pode possuir múltiplos registros, correspondentes às diferentes ocorrências salariais ao longo do vínculo empregatício. Também foram identificadas necessidades de padronização e tipagem que serão tratadas durante a construção da camada Silver.
# MAGIC
# MAGIC Em relação aos benefícios, verificou-se que `beneficio_anonimizado` não constitui uma fonte histórica acumulada. A tabela representa uma **fotografia de determinado momento da empresa**, contendo os vínculos e informações disponíveis naquela ocasião. Além disso, os valores nela registrados não são suficientes para reconstruir historicamente os benefícios considerados no MVP.
# MAGIC
# MAGIC Por esse motivo, foram analisadas fontes complementares para obtenção dos valores históricos de **ticket** e **plano de saúde**.
# MAGIC
# MAGIC A fonte `valor_ticket_2010_2025` registra a evolução dos valores estabelecidos pela Convenção Coletiva de Trabalho (CCT). Cada registro corresponde a um período de vigência, sendo os valores aplicáveis aos empregados de acordo com o piso estabelecido pela convenção da categoria.
# MAGIC
# MAGIC Para o plano de saúde, foram analisadas duas fontes complementares. `plano_saude_ate_2022` contém o histórico dos valores por tipo de plano, faixa etária e período de vigência até 2022. A partir de **outubro de 2022**, os valores passam a ser obtidos de `plano_saude_vital_de_2022_em_diante`. Em ambas as estruturas, o **Plano Especial** corresponde à equipe e o **Plano Executivo** à diretoria.
# MAGIC
# MAGIC As informações de quantidade de beneficiários e valores totais existentes nas fontes de plano de saúde representam fotografias de momentos específicos e não serão utilizadas para a reconstrução histórica do benefício. Para essa finalidade, serão considerados os valores unitários correspondentes ao tipo de plano, à faixa etária e ao respectivo período de vigência.
# MAGIC
# MAGIC Com essas análises, ficam estabelecidas as fontes e as principais regras de negócio necessárias para a posterior construção das estruturas de `SALÁRIO` e `BENEFÍCIO` na camada Silver. O atributo `total_beneficios` será calculado a partir dos componentes de benefícios considerados no escopo do MVP, não sendo utilizado diretamente o valor existente em `VALOR BENEFÍCIOS` na fonte original.