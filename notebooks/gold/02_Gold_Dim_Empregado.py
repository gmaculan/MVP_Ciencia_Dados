# Databricks notebook source
# MAGIC %md
# MAGIC # 1. Construção da dimensão de empregados
# MAGIC
# MAGIC A `dim_empregado` será construída a partir da tabela `workspace.silver.empregados_anonimizados`, utilizando os atributos necessários para identificação e caracterização dos empregados e de seus vínculos nas análises do MVP.
# MAGIC
# MAGIC A dimensão terá os seguintes atributos:
# MAGIC
# MAGIC - `id_empregado`: chave substituta criada na camada Gold;
# MAGIC - `drt`: identificação do vínculo empregatício;
# MAGIC - `nome`: nome anonimizado do empregado;
# MAGIC - `cpf`: CPF anonimizado, permitindo reconhecer diferentes vínculos pertencentes à mesma pessoa;
# MAGIC - `genero`: gênero do empregado;
# MAGIC - `logradouro`: logradouro anonimizado;
# MAGIC - `bairro`: bairro;
# MAGIC - `cidade`: município;
# MAGIC - `estado`: unidade da federação;
# MAGIC - `cep`: CEP anonimizado;
# MAGIC - `motivo_desligamento`: motivo associado ao encerramento do vínculo empregatício;
# MAGIC - `id_tempo_admissao`: chave de referência à `dim_tempo`, correspondente à data de admissão do vínculo;
# MAGIC - `id_tempo_desligamento`: chave de referência à `dim_tempo`, correspondente à data de desligamento do vínculo.
# MAGIC
# MAGIC O `DRT` continuará representando o vínculo empregatício. Dessa forma, uma pessoa que tenha sido desligada e posteriormente recontratada poderá possuir mais de um registro na dimensão, cada um associado ao respectivo DRT, enquanto o CPF anonimizado permitirá identificar que esses vínculos pertencem à mesma pessoa.
# MAGIC
# MAGIC As datas de admissão e desligamento caracterizam o período de vigência de cada vínculo e são necessárias para análises de RH, como admissões, desligamentos, tempo de empresa e turnover.
# MAGIC
# MAGIC Como essas datas já estão contempladas na `dim_tempo`, elas serão representadas na `dim_empregado` por meio de `id_tempo_admissao` e `id_tempo_desligamento`. A mesma dimensão de tempo será, portanto, utilizada em dois papéis distintos: data de admissão e data de desligamento.
# MAGIC
# MAGIC O atributo `motivo_desligamento` complementa a referência temporal de desligamento e permitirá analisar a distribuição e a evolução dos motivos de saída, bem como sua relação com o tempo de permanência no vínculo.
# MAGIC
# MAGIC Para vínculos ainda ativos, cuja data de desligamento é nula na tabela Silver, `id_tempo_desligamento` e `motivo_desligamento` permanecerão nulos. Esses valores nulos possuem significado de negócio e não serão preenchidos artificialmente.
# MAGIC
# MAGIC A dimensão não reproduzirá integralmente a tabela Silver de Empregados. Serão mantidos apenas os atributos definidos como necessários para identificação, caracterização do empregado, caracterização do desligamento e representação temporal do vínculo nas análises da camada Gold.
# MAGIC
# MAGIC A inclusão de `motivo_desligamento` não altera a granularidade da dimensão, que permanece definida como **um registro por vínculo empregatício (DRT)**.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC CREATE OR REPLACE TABLE workspace.gold.dim_empregado AS
# MAGIC
# MAGIC SELECT
# MAGIC     ROW_NUMBER() OVER (
# MAGIC         ORDER BY e.drt
# MAGIC     ) AS id_empregado,
# MAGIC
# MAGIC     e.drt,
# MAGIC     e.nome,
# MAGIC     e.cpf,
# MAGIC     e.genero,
# MAGIC     e.logradouro,
# MAGIC     e.bairro,
# MAGIC     e.cidade,
# MAGIC     e.estado,
# MAGIC     e.cep,
# MAGIC     e.motivo_desligamento,
# MAGIC
# MAGIC     ta.id_tempo AS id_tempo_admissao,
# MAGIC     td.id_tempo AS id_tempo_desligamento
# MAGIC
# MAGIC FROM workspace.silver.empregados_anonimizados e
# MAGIC
# MAGIC LEFT JOIN workspace.gold.dim_tempo ta
# MAGIC     ON e.data_admissao = ta.data
# MAGIC
# MAGIC LEFT JOIN workspace.gold.dim_tempo td
# MAGIC     ON e.data_desligamento = td.data;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Conclusão da Construção da dimensão de empregados
# MAGIC
# MAGIC A atualização da tabela `workspace.gold.dim_empregado` foi concluída sem erros, incorporando `motivo_desligamento` como atributo descritivo do vínculo empregatício.
# MAGIC
# MAGIC A dimensão continua sendo construída a partir de `workspace.silver.empregados_anonimizados` e mantém:
# MAGIC
# MAGIC - o DRT como identificador do vínculo empregatício;
# MAGIC - o CPF anonimizado como identificador que permite reconhecer diferentes vínculos pertencentes à mesma pessoa;
# MAGIC - `id_tempo_admissao` e `id_tempo_desligamento` como referências à `dim_tempo`;
# MAGIC - `motivo_desligamento` como atributo associado ao encerramento do vínculo.
# MAGIC
# MAGIC A inclusão de `motivo_desligamento` complementa a representação temporal já existente e permite que as análises de desligamento considerem não apenas quando o vínculo foi encerrado, mas também o motivo registrado para a saída.
# MAGIC
# MAGIC A granularidade da dimensão permanece inalterada, definida como **um registro por vínculo empregatício (DRT)**.
# MAGIC
# MAGIC A conclusão da construção, entretanto, não é suficiente para considerar a dimensão novamente validada. Na próxima etapa serão verificados o volume de registros, a unicidade das chaves, as referências temporais e a consistência de `motivo_desligamento` com a situação dos vínculos.

# COMMAND ----------

# MAGIC %md
# MAGIC # 2. Validação da dimensão de empregados
# MAGIC
# MAGIC Após a atualização da tabela `workspace.gold.dim_empregado`, será realizada a validação de sua estrutura e conteúdo, incluindo as referências temporais de admissão e desligamento e o atributo `motivo_desligamento`.
# MAGIC
# MAGIC A verificação tem como objetivos confirmar:
# MAGIC
# MAGIC - a existência de **347 registros**, correspondentes aos vínculos empregatícios presentes na tabela Silver;
# MAGIC - a existência de **347 DRTs distintos**;
# MAGIC - a unicidade da chave substituta `id_empregado`;
# MAGIC - a inexistência de valores nulos em `id_empregado`, `drt`, `nome`, `cpf` e `genero`;
# MAGIC - a inexistência de valores nulos em `id_tempo_admissao`, uma vez que todo vínculo possui data de admissão;
# MAGIC - a correspondência entre os valores nulos de `id_tempo_desligamento` e os vínculos ainda ativos, cuja `data_desligamento` é nula na tabela Silver;
# MAGIC - a correspondência das chaves `id_tempo_admissao` e `id_tempo_desligamento` com as respectivas datas existentes na `dim_tempo`;
# MAGIC - a existência de `motivo_desligamento` para os vínculos desligados e sua ausência para os vínculos ativos;
# MAGIC - a correspondência entre `motivo_desligamento` armazenado na dimensão e o respectivo valor existente na tabela Silver;
# MAGIC - a preservação dos valores nulos de endereço já identificados e aceitos durante o tratamento da camada Silver;
# MAGIC - a manutenção dos diferentes DRTs associados a uma mesma pessoa nos casos de recontratação.
# MAGIC
# MAGIC Os valores ausentes nos atributos de endereço não serão preenchidos artificialmente na camada Gold, uma vez que representam a disponibilidade efetiva das informações provenientes da camada Silver.
# MAGIC
# MAGIC Da mesma forma, valores nulos em `id_tempo_desligamento` e `motivo_desligamento` são esperados para vínculos ativos e possuem significado de negócio, não constituindo problema de qualidade dos dados.

# COMMAND ----------

# MAGIC %sql
# MAGIC
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros,
# MAGIC
# MAGIC     COUNT(DISTINCT g.id_empregado) AS ids_distintos,
# MAGIC
# MAGIC     COUNT(DISTINCT g.drt) AS drts_distintos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.id_empregado IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS id_empregado_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.drt IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS drt_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.nome IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS nome_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.cpf IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cpf_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.genero IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS genero_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.logradouro IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS logradouro_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.bairro IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS bairro_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.cidade IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cidade_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.estado IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS estado_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.cep IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS cep_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.id_tempo_admissao IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS id_tempo_admissao_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.id_tempo_desligamento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS id_tempo_desligamento_nulos,
# MAGIC
# MAGIC     SUM(CASE WHEN g.motivo_desligamento IS NULL THEN 1 ELSE 0 END)
# MAGIC         AS motivo_desligamento_nulos,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_desligamento IS NULL
# MAGIC          AND g.id_tempo_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS vinculos_ativos,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_admissao IS NOT NULL
# MAGIC          AND g.id_tempo_admissao IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS admissoes_sem_correspondencia_tempo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_desligamento IS NOT NULL
# MAGIC          AND g.id_tempo_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS desligamentos_sem_correspondencia_tempo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_desligamento IS NOT NULL
# MAGIC          AND g.motivo_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS desligados_com_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_desligamento IS NOT NULL
# MAGIC          AND g.motivo_desligamento IS NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS desligados_sem_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN s.data_desligamento IS NULL
# MAGIC          AND g.motivo_desligamento IS NOT NULL
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS ativos_com_motivo,
# MAGIC
# MAGIC     SUM(CASE
# MAGIC         WHEN NOT (g.motivo_desligamento <=> s.motivo_desligamento)
# MAGIC         THEN 1 ELSE 0
# MAGIC     END) AS motivos_divergentes_silver
# MAGIC
# MAGIC FROM workspace.gold.dim_empregado g
# MAGIC
# MAGIC LEFT JOIN workspace.silver.empregados_anonimizados s
# MAGIC     ON g.drt = s.drt;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Conclusão da Validação da dimensão de empregados
# MAGIC
# MAGIC A validação da tabela `workspace.gold.dim_empregado` confirmou a consistência da dimensão após a incorporação de `motivo_desligamento`, preservando as referências temporais de admissão e desligamento anteriormente implementadas.
# MAGIC
# MAGIC Foram obtidos:
# MAGIC
# MAGIC - **347 registros**;
# MAGIC - **347 identificadores distintos** em `id_empregado`;
# MAGIC - **347 DRTs distintos**;
# MAGIC - **0 valores nulos** em `id_empregado`;
# MAGIC - **0 valores nulos** em `drt`;
# MAGIC - **0 valores nulos** em `nome`;
# MAGIC - **0 valores nulos** em `cpf`;
# MAGIC - **0 valores nulos** em `genero`;
# MAGIC - **0 valores nulos** em `id_tempo_admissao`;
# MAGIC - **14 valores nulos** em `id_tempo_desligamento`, correspondentes exatamente aos **14 vínculos ativos**;
# MAGIC - **14 valores nulos** em `motivo_desligamento`, também correspondentes aos **14 vínculos ativos**;
# MAGIC - **0 admissões sem correspondência** com a `dim_tempo`;
# MAGIC - **0 desligamentos sem correspondência** com a `dim_tempo`;
# MAGIC - **333 vínculos desligados com motivo de desligamento**;
# MAGIC - **0 vínculos desligados sem motivo**;
# MAGIC - **0 vínculos ativos com motivo de desligamento**;
# MAGIC - **0 divergências** entre `motivo_desligamento` na dimensão Gold e o respectivo valor na tabela Silver;
# MAGIC - **1 valor nulo** em `logradouro`;
# MAGIC - **1 valor nulo** em `bairro`;
# MAGIC - **1 valor nulo** em `cidade`;
# MAGIC - **1 valor nulo** em `estado`;
# MAGIC - **3 valores nulos** em `cep`.
# MAGIC
# MAGIC A correspondência entre o total de registros, a quantidade de identificadores distintos e a quantidade de DRTs distintos confirma a preservação da granularidade de **um registro por vínculo empregatício** e a unicidade da chave substituta `id_empregado`.
# MAGIC
# MAGIC Todos os vínculos possuem referência válida à `dim_tempo` para a data de admissão. Os 14 valores nulos em `id_tempo_desligamento` correspondem integralmente aos vínculos ainda ativos e possuem significado de negócio.
# MAGIC
# MAGIC A mesma consistência foi observada em `motivo_desligamento`: os 333 vínculos desligados possuem motivo registrado, enquanto os 14 vínculos ativos não possuem motivo. A inexistência de divergências entre Gold e Silver confirma que o atributo foi propagado corretamente para a dimensão.
# MAGIC
# MAGIC As datas de admissão e desligamento permanecem representadas por referências à mesma `dim_tempo`, utilizada em papéis temporais distintos. Em conjunto com `motivo_desligamento`, essa estrutura permite apoiar análises de admissões, desligamentos, tempo de empresa, turnover e motivos de saída sem alterar o grão da dimensão.
# MAGIC
# MAGIC Os valores nulos encontrados nos atributos de endereço já estavam presentes e haviam sido aceitos durante o tratamento da camada Silver. Esses valores foram preservados na camada Gold, sem preenchimento artificial de informações inexistentes na fonte.
# MAGIC
# MAGIC O DRT permanece como identificador do vínculo empregatício, enquanto o CPF anonimizado permite reconhecer situações em que diferentes vínculos pertencem à mesma pessoa.
# MAGIC
# MAGIC Dessa forma, a atualização e a validação da `dim_empregado` são consideradas concluídas.