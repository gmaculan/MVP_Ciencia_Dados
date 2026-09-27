# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Definição da Fato_Faturamento
# MAGIC
# MAGIC A `Fato_Faturamento` tem como objetivo representar os eventos históricos de faturamento da empresa em granularidade adequada às análises financeiras e gerenciais do MVP.
# MAGIC
# MAGIC A fonte será `workspace.silver.faturamento_anonimizado`, preservando nas camadas Bronze e Silver os dados recebidos da origem e realizando na Gold os tratamentos necessários à representação analítica do faturamento.
# MAGIC
# MAGIC ## Granularidade
# MAGIC
# MAGIC A granularidade da `Fato_Faturamento` será de **uma linha por nota fiscal efetiva de faturamento**.
# MAGIC
# MAGIC A análise da fonte identificou situações em que uma mesma NF foi registrada em múltiplas linhas. Esse comportamento não representa a existência de diferentes notas fiscais.
# MAGIC
# MAGIC Na operação anterior, uma única NF podia ser artificialmente distribuída entre diferentes competências e, em alguns casos, entre diferentes CRs, com o objetivo de representar gerencialmente em quais períodos o serviço correspondente havia sido realizado.
# MAGIC
# MAGIC Esse procedimento constituía um controle gerencial incorporado à planilha de faturamento e não uma divisão do evento financeiro representado pela NF.
# MAGIC
# MAGIC Na Gold, esse artifício não será preservado. Quando uma NF possuir múltiplos registros:
# MAGIC
# MAGIC - será criada uma única ocorrência da NF;
# MAGIC - o valor da NF corresponderá à soma dos valores registrados em seus diferentes desdobramentos;
# MAGIC - a competência será aquela registrada na primeira ocorrência da NF na fonte;
# MAGIC - os desdobramentos artificiais entre competências ou CRs não serão transportados para a Gold.
# MAGIC
# MAGIC Dessa forma, a `Fato_Faturamento` representará o evento financeiro efetivo, enquanto eventuais necessidades futuras de apropriação gerencial por período deverão ser modeladas separadamente, sem alterar a identidade da nota fiscal.
# MAGIC
# MAGIC ## Registros de cancelamento
# MAGIC
# MAGIC Os registros identificados como `CANCELAMENTO` serão excluídos da `Fato_Faturamento`.
# MAGIC
# MAGIC No processo de origem, o cancelamento implicava a anulação do CR e não era registrada informação suficiente para identificar sua causa, como erro interno, solicitação do cliente ou outro motivo.
# MAGIC
# MAGIC Como esses registros não oferecem conteúdo analítico confiável para as perguntas do MVP, eles permanecerão preservados nas camadas anteriores, mas não serão transportados para a Gold.
# MAGIC
# MAGIC ## Estrutura dos CRs
# MAGIC
# MAGIC Os campos `CR1`, `CR2`, `CR3` e `CR4` representam a estrutura utilizada para identificação das alocações relacionadas ao faturamento.
# MAGIC
# MAGIC Embora o preenchimento completo dos quatro componentes seja o padrão usual, existem registros legítimos com `CR4` nulo. Essa condição não caracteriza erro de qualidade.
# MAGIC
# MAGIC Consequentemente:
# MAGIC
# MAGIC - `CR4` nulo será aceito;
# MAGIC - não será realizada imputação de valor;
# MAGIC - nenhum registro será descartado exclusivamente pela ausência de `CR4`.
# MAGIC
# MAGIC ## Datas
# MAGIC
# MAGIC A fonte possui diferentes referências temporais, entre elas:
# MAGIC
# MAGIC - data de emissão;
# MAGIC - data de competência;
# MAGIC - data de vencimento.
# MAGIC
# MAGIC Essas datas possuem significados distintos e serão preservadas para permitir diferentes perspectivas temporais nas análises.
# MAGIC
# MAGIC A `Dim_Tempo`, já construída na camada Gold, poderá atuar como dimensão conformada para esses diferentes papéis de data.
# MAGIC
# MAGIC ## Valores financeiros
# MAGIC
# MAGIC A fato deverá preservar os valores financeiros necessários às análises do faturamento, incluindo o valor faturado e os componentes tributários e de retenção disponíveis na Silver.
# MAGIC
# MAGIC Nos casos de NFs artificialmente desdobradas na origem, os valores serão consolidados de acordo com a regra definida para a granularidade da Gold.
# MAGIC
# MAGIC ## Objetivos analíticos
# MAGIC
# MAGIC A `Fato_Faturamento` deverá permitir análises como:
# MAGIC
# MAGIC - faturamento total mensal e anual;
# MAGIC - faturamento por cliente;
# MAGIC - faturamento por alocação;
# MAGIC - evolução histórica do faturamento;
# MAGIC - concentração do faturamento por cliente;
# MAGIC - participação dos clientes no faturamento total;
# MAGIC - evolução da participação dos clientes;
# MAGIC - identificação de clientes com aumento ou redução de participação;
# MAGIC - ticket médio das notas fiscais;
# MAGIC - ticket médio por cliente;
# MAGIC - integração posterior entre faturamento, custos e margens nas análises gerenciais.
# MAGIC
# MAGIC A construção da Gold reorganizará os dados para consumo analítico sem reproduzir mecanismos manuais de controle gerencial que não correspondam à natureza financeira dos eventos representados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC WITH faturamento_base AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY nf
# MAGIC             ORDER BY
# MAGIC                 data_emissao,
# MAGIC                 CASE WHEN valor = 0 THEN 0 ELSE 1 END,
# MAGIC                 data_competencia,
# MAGIC                 cr1,
# MAGIC                 cr2,
# MAGIC                 cr3,
# MAGIC                 cr4
# MAGIC         ) AS ordem_nf
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC     WHERE cliente <> 'CANCELAMENTO'
# MAGIC ),
# MAGIC
# MAGIC referencia_nf AS (
# MAGIC     SELECT
# MAGIC         nf,
# MAGIC         cr1,
# MAGIC         cr2,
# MAGIC         cr3,
# MAGIC         cr4,
# MAGIC         data_emissao,
# MAGIC         data_competencia,
# MAGIC         cliente,
# MAGIC         data_vencimento
# MAGIC     FROM faturamento_base
# MAGIC     WHERE ordem_nf = 1
# MAGIC ),
# MAGIC
# MAGIC valores_nf AS (
# MAGIC     SELECT
# MAGIC         nf,
# MAGIC         SUM(valor) AS valor,
# MAGIC         SUM(valor_iss_2) AS valor_iss_2,
# MAGIC         SUM(valor_iss_5) AS valor_iss_5,
# MAGIC         SUM(valor_liquido) AS valor_liquido,
# MAGIC         SUM(retencao_ir) AS retencao_ir,
# MAGIC         SUM(retencao_pis) AS retencao_pis,
# MAGIC         SUM(retencao_cssl) AS retencao_cssl
# MAGIC     FROM faturamento_base
# MAGIC     GROUP BY nf
# MAGIC ),
# MAGIC
# MAGIC fato_faturamento AS (
# MAGIC     SELECT
# MAGIC         r.nf,
# MAGIC         r.cr1,
# MAGIC         r.cr2,
# MAGIC         r.cr3,
# MAGIC         r.cr4,
# MAGIC         r.data_emissao,
# MAGIC         r.data_competencia,
# MAGIC         r.data_vencimento,
# MAGIC         r.cliente,
# MAGIC         v.valor,
# MAGIC         v.valor_iss_2,
# MAGIC         v.valor_iss_5,
# MAGIC         v.valor_liquido,
# MAGIC         v.retencao_ir,
# MAGIC         v.retencao_pis,
# MAGIC         v.retencao_cssl
# MAGIC     FROM referencia_nf r
# MAGIC     INNER JOIN valores_nf v
# MAGIC         ON r.nf = v.nf
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     *
# MAGIC FROM fato_faturamento
# MAGIC ORDER BY
# MAGIC     data_competencia,
# MAGIC     nf;

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Conclusão da Construção da Fato_Faturamento
# MAGIC
# MAGIC A construção da `Fato_Faturamento` resultou em **3.907 registros**, correspondentes a **3.907 notas fiscais distintas**, confirmando a granularidade definida de uma linha por NF.
# MAGIC
# MAGIC Os registros identificados como `CANCELAMENTO` foram excluídos da Gold, pois o processo de origem não preservava informação suficiente para determinar a natureza do cancelamento e, consequentemente, esses registros não possuem conteúdo analítico confiável para as perguntas do MVP.
# MAGIC
# MAGIC As NFs que haviam sido artificialmente desdobradas na origem para representar apropriações gerenciais em diferentes competências ou CRs foram consolidadas novamente em uma única ocorrência.
# MAGIC
# MAGIC Nesses casos:
# MAGIC
# MAGIC - os valores dos diferentes registros da mesma NF foram somados;
# MAGIC - a competência da ocorrência de referência foi preservada;
# MAGIC - os demais dados de identificação foram obtidos dessa mesma ocorrência;
# MAGIC - os desdobramentos utilizados no controle gerencial anterior não foram transportados para a Gold.
# MAGIC
# MAGIC Como exemplo de validação da regra, a NF 2761, anteriormente distribuída entre diferentes competências, passou a ser representada por uma única ocorrência, com competência `06/08/2019` e valor consolidado de **R$ 30.016,00**.
# MAGIC
# MAGIC A transformação também preservou os registros legítimos com `CR4` nulo. Foram mantidas **223 NFs nessa condição**, uma vez que a ausência de `CR4`, embora não corresponda ao padrão usual de preenchimento, não representa erro na origem.
# MAGIC
# MAGIC Após os tratamentos realizados:
# MAGIC
# MAGIC - total de registros: **3.907**;
# MAGIC - total de NFs distintas: **3.907**;
# MAGIC - NFs nulas: **0**;
# MAGIC - NFs duplicadas: **0**;
# MAGIC - registros de cancelamento: **0**;
# MAGIC - registros com `CR4` nulo: **223**.
# MAGIC
# MAGIC O resultado confirma que a transformação representa cada NF como um único evento financeiro, sem transportar para a Gold os artifícios de apropriação gerencial existentes no controle anterior.
# MAGIC
# MAGIC Com a estrutura validada, a próxima etapa consiste na persistência da `Fato_Faturamento` na camada Gold.

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Persistência da Fato_Faturamento
# MAGIC
# MAGIC Após a validação da transformação, a `Fato_Faturamento` será persistida na camada Gold como `workspace.gold.fato_faturamento`, utilizando formato Delta.
# MAGIC
# MAGIC A persistência manterá as regras definidas e validadas na etapa anterior:
# MAGIC
# MAGIC - granularidade de uma linha por NF;
# MAGIC - exclusão dos registros identificados como `CANCELAMENTO`;
# MAGIC - consolidação dos desdobramentos artificiais de uma mesma NF existentes na origem;
# MAGIC - soma dos valores financeiros dos registros pertencentes à mesma NF;
# MAGIC - utilização da ocorrência de referência para preservação das informações de CR, cliente e datas;
# MAGIC - preservação dos registros legítimos com `CR4` nulo;
# MAGIC - manutenção das datas de emissão, competência e vencimento como referências temporais distintas;
# MAGIC - preservação dos componentes financeiros disponíveis na Silver.
# MAGIC
# MAGIC A consolidação realizada na Gold elimina o mecanismo manual utilizado na origem para distribuir gerencialmente uma mesma NF entre diferentes competências ou CRs, mantendo nas camadas anteriores os registros recebidos da fonte.
# MAGIC
# MAGIC A tabela resultante representará cada nota fiscal como um único evento financeiro e servirá de base para as análises de faturamento e para sua posterior integração com custos e margens.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.fato_faturamento
# MAGIC USING DELTA
# MAGIC AS
# MAGIC
# MAGIC WITH faturamento_base AS (
# MAGIC     SELECT
# MAGIC         *,
# MAGIC         ROW_NUMBER() OVER (
# MAGIC             PARTITION BY nf
# MAGIC             ORDER BY
# MAGIC                 data_emissao,
# MAGIC                 CASE WHEN valor = 0 THEN 0 ELSE 1 END,
# MAGIC                 data_competencia,
# MAGIC                 cr1,
# MAGIC                 cr2,
# MAGIC                 cr3,
# MAGIC                 cr4
# MAGIC         ) AS ordem_nf
# MAGIC     FROM workspace.silver.faturamento_anonimizado
# MAGIC     WHERE cliente <> 'CANCELAMENTO'
# MAGIC ),
# MAGIC
# MAGIC referencia_nf AS (
# MAGIC     SELECT
# MAGIC         nf,
# MAGIC         cr1,
# MAGIC         cr2,
# MAGIC         cr3,
# MAGIC         cr4,
# MAGIC         data_emissao,
# MAGIC         data_competencia,
# MAGIC         cliente,
# MAGIC         data_vencimento
# MAGIC     FROM faturamento_base
# MAGIC     WHERE ordem_nf = 1
# MAGIC ),
# MAGIC
# MAGIC valores_nf AS (
# MAGIC     SELECT
# MAGIC         nf,
# MAGIC         SUM(valor) AS valor,
# MAGIC         SUM(valor_iss_2) AS valor_iss_2,
# MAGIC         SUM(valor_iss_5) AS valor_iss_5,
# MAGIC         SUM(valor_liquido) AS valor_liquido,
# MAGIC         SUM(retencao_ir) AS retencao_ir,
# MAGIC         SUM(retencao_pis) AS retencao_pis,
# MAGIC         SUM(retencao_cssl) AS retencao_cssl
# MAGIC     FROM faturamento_base
# MAGIC     GROUP BY nf
# MAGIC ),
# MAGIC
# MAGIC fato_faturamento AS (
# MAGIC     SELECT
# MAGIC         r.nf,
# MAGIC         r.cr1,
# MAGIC         r.cr2,
# MAGIC         r.cr3,
# MAGIC         r.cr4,
# MAGIC         r.data_emissao,
# MAGIC         r.data_competencia,
# MAGIC         r.data_vencimento,
# MAGIC         r.cliente,
# MAGIC         v.valor,
# MAGIC         v.valor_iss_2,
# MAGIC         v.valor_iss_5,
# MAGIC         v.valor_liquido,
# MAGIC         v.retencao_ir,
# MAGIC         v.retencao_pis,
# MAGIC         v.retencao_cssl
# MAGIC     FROM referencia_nf r
# MAGIC     INNER JOIN valores_nf v
# MAGIC         ON r.nf = v.nf
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC     nf,
# MAGIC     cr1,
# MAGIC     cr2,
# MAGIC     cr3,
# MAGIC     cr4,
# MAGIC     data_emissao,
# MAGIC     data_competencia,
# MAGIC     data_vencimento,
# MAGIC     cliente,
# MAGIC     valor,
# MAGIC     valor_iss_2,
# MAGIC     valor_iss_5,
# MAGIC     valor_liquido,
# MAGIC     retencao_ir,
# MAGIC     retencao_pis,
# MAGIC     retencao_cssl
# MAGIC
# MAGIC FROM fato_faturamento;

# COMMAND ----------

# MAGIC %md
# MAGIC # 3. Conclusão da Persistência da Fato_Faturamento
# MAGIC
# MAGIC A `Fato_Faturamento` foi persistida na camada Gold como `workspace.gold.fato_faturamento`, utilizando formato Delta.
# MAGIC
# MAGIC A tabela foi construída com a granularidade definida de **uma linha por nota fiscal**, incorporando os tratamentos de negócio validados anteriormente.
# MAGIC
# MAGIC Durante a persistência:
# MAGIC
# MAGIC - os registros identificados como `CANCELAMENTO` foram excluídos;
# MAGIC - as ocorrências artificiais utilizadas na origem para distribuir uma mesma NF entre diferentes competências ou CRs foram consolidadas;
# MAGIC - os valores financeiros pertencentes à mesma NF foram somados;
# MAGIC - as informações da ocorrência de referência foram utilizadas para preservar CR, cliente e datas;
# MAGIC - os registros legítimos com `CR4` nulo foram mantidos sem imputação;
# MAGIC - as datas de emissão, competência e vencimento foram preservadas como referências temporais distintas;
# MAGIC - os componentes financeiros disponíveis na Silver foram mantidos na estrutura da fato.
# MAGIC
# MAGIC Dessa forma, a tabela Gold deixa de reproduzir o mecanismo manual de apropriação gerencial existente na origem e passa a representar cada NF como um único evento financeiro.
# MAGIC
# MAGIC As camadas Bronze e Silver permanecem inalteradas, preservando os registros recebidos da origem e garantindo a rastreabilidade das transformações realizadas na Gold.
# MAGIC
# MAGIC Com a persistência concluída, a próxima etapa consiste na validação final de `workspace.gold.fato_faturamento`.

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Validação final da Fato_Faturamento
# MAGIC
# MAGIC Após a persistência, será realizada a validação final de `workspace.gold.fato_faturamento`.
# MAGIC
# MAGIC A validação verificará a granularidade definida para a fato, a aplicação das regras de tratamento e a integridade dos principais campos necessários às análises.
# MAGIC
# MAGIC Serão verificados:
# MAGIC
# MAGIC - quantidade total de registros;
# MAGIC - quantidade de NFs distintas;
# MAGIC - inexistência de NFs duplicadas;
# MAGIC - inexistência de NFs nulas;
# MAGIC - inexistência de registros de `CANCELAMENTO`;
# MAGIC - quantidade de registros com `CR4` nulo, condição válida na origem;
# MAGIC - presença de cliente;
# MAGIC - presença das datas de emissão, competência e vencimento;
# MAGIC - presença dos principais valores financeiros;
# MAGIC - coerência cronológica da cobertura temporal da fato.
# MAGIC
# MAGIC A validação permitirá confirmar que a tabela persistida representa uma única ocorrência por NF e que os tratamentos definidos para a camada Gold foram corretamente aplicados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT nf) AS total_nfs,
# MAGIC
# MAGIC     COUNT(*) - COUNT(DISTINCT nf) AS nfs_duplicadas,
# MAGIC
# MAGIC     SUM(CASE WHEN nf IS NULL THEN 1 ELSE 0 END) AS nf_nula,
# MAGIC
# MAGIC     SUM(
# MAGIC         CASE
# MAGIC             WHEN cliente = 'CANCELAMENTO' THEN 1
# MAGIC             ELSE 0
# MAGIC         END
# MAGIC     ) AS registros_cancelamento,
# MAGIC
# MAGIC     SUM(CASE WHEN cr4 IS NULL THEN 1 ELSE 0 END) AS cr4_nulo,
# MAGIC
# MAGIC     SUM(CASE WHEN cliente IS NULL THEN 1 ELSE 0 END) AS cliente_nulo,
# MAGIC
# MAGIC     SUM(CASE WHEN data_emissao IS NULL THEN 1 ELSE 0 END) AS data_emissao_nula,
# MAGIC
# MAGIC     SUM(CASE WHEN data_competencia IS NULL THEN 1 ELSE 0 END) AS data_competencia_nula,
# MAGIC
# MAGIC     SUM(CASE WHEN data_vencimento IS NULL THEN 1 ELSE 0 END) AS data_vencimento_nula,
# MAGIC
# MAGIC     SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END) AS valor_nulo,
# MAGIC
# MAGIC     SUM(CASE WHEN valor_liquido IS NULL THEN 1 ELSE 0 END) AS valor_liquido_nulo,
# MAGIC
# MAGIC     MIN(data_competencia) AS primeira_competencia,
# MAGIC
# MAGIC     MAX(data_competencia) AS ultima_competencia
# MAGIC
# MAGIC FROM workspace.gold.fato_faturamento;

# COMMAND ----------

# MAGIC %md
# MAGIC # 4. Conclusão da Validação final da Fato_Faturamento
# MAGIC
# MAGIC A validação final de `workspace.gold.fato_faturamento` confirmou a consistência da estrutura persistida e dos tratamentos aplicados durante sua construção.
# MAGIC
# MAGIC A tabela apresentou:
# MAGIC
# MAGIC - **3.907 registros**;
# MAGIC - **3.907 NFs distintas**;
# MAGIC - **0 NFs duplicadas**;
# MAGIC - **0 NFs nulas**;
# MAGIC - **0 registros identificados como `CANCELAMENTO`**;
# MAGIC - **0 registros com `CR4` nulo**;
# MAGIC - **0 clientes nulos**;
# MAGIC - **0 datas de emissão nulas**;
# MAGIC - **0 datas de competência nulas**;
# MAGIC - **0 datas de vencimento nulas**;
# MAGIC - **0 valores de faturamento nulos**;
# MAGIC - **0 valores líquidos nulos**.
# MAGIC
# MAGIC A cobertura temporal das competências compreende o período de **01/11/2011 a 20/10/2025**.
# MAGIC
# MAGIC A igualdade entre a quantidade total de registros e a quantidade de NFs distintas confirma a granularidade estabelecida para a Gold: **uma linha por nota fiscal**.
# MAGIC
# MAGIC Os registros de `CANCELAMENTO` foram integralmente retirados da fato, conforme a regra de negócio definida, permanecendo preservados nas camadas anteriores.
# MAGIC
# MAGIC As NFs que haviam sido artificialmente desdobradas na origem para distribuir gerencialmente seus valores entre diferentes competências ou CRs foram consolidadas. Dessa forma, a Gold não reproduz esse mecanismo manual de controle e representa cada NF como um único evento financeiro.
# MAGIC
# MAGIC Nos casos consolidados, os valores financeiros das ocorrências pertencentes à mesma NF foram somados, enquanto as informações da ocorrência de referência foram utilizadas para representar o evento na fato.
# MAGIC
# MAGIC Embora a origem admita legitimamente situações com `CR4` não preenchido, após a exclusão dos cancelamentos e a consolidação das NFs nenhuma ocorrência persistida na Gold apresentou `CR4` nulo. Essa ausência, portanto, é resultado dos registros efetivamente selecionados pela transformação e não de imputação ou correção artificial do campo.
# MAGIC
# MAGIC A `Fato_Faturamento` encontra-se, assim, validada e concluída para utilização nas análises financeiras e para posterior integração com custos e margens do MVP.