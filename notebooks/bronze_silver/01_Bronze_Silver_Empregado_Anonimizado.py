# Databricks notebook source
# MAGIC %md
# MAGIC # Tratamento da entidade EMPREGADO — Bronze → Silver
# MAGIC
# MAGIC ## Objetivo
# MAGIC
# MAGIC Este notebook tem como objetivo analisar os dados da entidade EMPREGADO armazenados na camada Bronze, identificar problemas de qualidade e definir os tratamentos necessários para sua transformação para a camada Silver.
# MAGIC
# MAGIC A transformação deverá considerar o modelo lógico definido para a entidade EMPREGADO e preservar a rastreabilidade das decisões de tratamento adotadas.
# MAGIC
# MAGIC **Fonte:** `workspace.bronze.empregados_animizados`  
# MAGIC **Destino:** `workspace.silver.empregados_anonimizados`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Diagnóstico da camada Bronze
# MAGIC
# MAGIC Nesta etapa será analisada a estrutura e a qualidade dos dados presentes na tabela `workspace.bronze.empregados_anonimizados`, antes da aplicação de transformações.
# MAGIC
# MAGIC ### 1.1 Identificação das colunas e tipos de dados
# MAGIC
# MAGIC A tabela empregado foi carregada na camada Bronze a partir do arquivo de origem por meio da funcionalidade Create Table. Nesta etapa, será verificado se as colunas foram carregadas corretamente e se os tipos de dados atribuídos pelo Databricks durante a ingestão são adequados.
# MAGIC
# MAGIC ### 1.1.1 Consulta 01 - Identificação das colunas
# MAGIC
# MAGIC A consulta a seguir tem como objetivo identificar as colunas existentes na tabela workspace.bronze.empregados_anonimizados e os respectivos tipos de dados atribuídos pelo Databricks durante a ingestão.

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE workspace.bronze.Empregados_Anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC ### Mapeamento de atributos — EMPREGADO: Bronze → Silver
# MAGIC
# MAGIC A tabela `workspace.bronze.empregados_anonimizados` possui **155 colunas**. A fonte de origem concentra informações de diferentes naturezas em uma única estrutura, incluindo dados cadastrais, vínculo empregatício, remuneração, férias, alocação, documentos, informações sindicais e bancárias, benefícios e controles administrativos.
# MAGIC
# MAGIC Na transformação Bronze → Silver, cada atributo é avaliado quanto ao seu destino. A existência de uma coluna na Bronze não implica sua permanência em `EMPREGADO`.
# MAGIC
# MAGIC A coluna **Observação / destino** registra se o atributo:
# MAGIC
# MAGIC - será **utilizado em EMPREGADO**;
# MAGIC - será **tratado em outra entidade/tabela**;
# MAGIC - será **derivado/recalculado**;
# MAGIC - **não será utilizado** no escopo do MVP; ou
# MAGIC - permanece **a definir**, quando a decisão depende da análise de seu conteúdo.
# MAGIC
# MAGIC Quando o atributo não fizer parte de `EMPREGADO`, o cabeçalho e o tipo Silver são representados por `—`. Quando ainda não houver elementos suficientes para determinar o tratamento, utiliza-se `A definir`.
# MAGIC
# MAGIC | # | Cabeçalho Bronze | Tipo Bronze | Cabeçalho Silver | Tipo Silver | Observação / destino |
# MAGIC |---:|---|---|---|---|---|
# MAGIC | 1 | `UNIDADE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 2 | `DRT` | BIGINT | `drt` | STRING | **Utilizado em EMPREGADO.** Identifica o vínculo empregatício. Convertido para STRING por possuir natureza de identificador. |
# MAGIC | 3 | `LIVRO` | BIGINT | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 4 | `_c3` | BIGINT | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 5 | `NOME REDUZIDO ANONIMIZADO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 6 | `NOME ANONIMIZADO` | STRING | `nome` | STRING | **Utilizado em EMPREGADO.** Nome anonimizado do empregado. |
# MAGIC | 7 | `GÊNERO` | STRING | `genero` | STRING | **Utilizado em EMPREGADO.** Atributo cadastral. |
# MAGIC | 8 | `CPF ANONIMIZADO` | STRING | `cpf` | STRING | **Utilizado em EMPREGADO.** Permite reconhecer a mesma pessoa em diferentes vínculos/DRTs. |
# MAGIC | 9 | `REGIME` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 10 | `COMPLEMENTO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 11 | `ADMISSÃO` | STRING | `data_admissao` | DATE | **Utilizado em EMPREGADO.** Converter STRING → DATE. |
# MAGIC | 12 | `DESLIGAMENTO11` | STRING | — | — | **Tratado em DESLIGAMENTO.** Representa informação de desligamento e deverá ser tipado adequadamente nessa entidade. |
# MAGIC | 13 | `DURAÇÃO DOS ATIVOS (ANOS)` | STRING | — | — | **Derivado/recalculado.** Não transportar o valor diretamente. Duração pode ser calculada a partir da admissão e da data de referência. |
# MAGIC | 14 | `DURAÇÃO DOS DESLIGADOS (ANOS)` | STRING | — | — | **Derivado/recalculado.** Pode ser obtido a partir das datas de admissão e desligamento. |
# MAGIC | 15 | `MOTIVO PRINCIPAL` | STRING | — | — | **Tratado em DESLIGAMENTO.** Motivo associado ao encerramento do vínculo. |
# MAGIC | 16 | `AFASTAMENTO` | TIMESTAMP | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 17 | `STATUS` | STRING | — | — | **Derivado.** A condição do vínculo pode ser determinada pela existência/data de desligamento em relação ao período analisado. |
# MAGIC | 18 | `ULT. EXAME MÉDICO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 19 | `PRÓXIMO EXAME` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 20 | `CARGO` | STRING | — | — | **Tratado em SALÁRIO.** O cargo faz parte do histórico profissional/remuneratório do empregado. |
# MAGIC | 21 | `ALOCAÇÃO` | STRING | — | — | **Tratado em ALOCAÇÃO.** Não permanecerá em EMPREGADO. |
# MAGIC | 22 | `ESTADO CIVIL` | STRING | `estado_civil` | STRING | **Utilizado em EMPREGADO.** Atributo cadastral. |
# MAGIC | 23 | `HORÁRIO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 24 | `ÚLT. SALÁRIO` | DECIMAL(33,13) | — | — | **Tratado em SALÁRIO.** Informação remuneratória. |
# MAGIC | 25 | `SALÁRIO INICIAL` | DECIMAL(22,2) | — | — | **Tratado em SALÁRIO.** Informação remuneratória. |
# MAGIC | 26 | `REMUNERAÇÃO TOTAL` | DECIMAL(33,13) | — | — | **Tratado em SALÁRIO, conforme composição do campo.** Não pertence diretamente a EMPREGADO. |
# MAGIC | 27 | `HORAS MENSAIS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 28 | `FORMA REMUN.` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 29 | `PRÓX. PERÍODO   FÉRIAS` | STRING | — | — | **Tratado em FÉRIAS.** |
# MAGIC | 30 | `ALOCAÇÃO ATUAL` | STRING | — | — | **Tratado em ALOCAÇÃO.** |
# MAGIC | 31 | `GERENTE ATUAL` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação relacionada à estrutura de gestão/alocação. |
# MAGIC | 32 | `PREVISÃO PROX. FÉRIAS` | STRING | — | — | **Tratado em FÉRIAS.** |
# MAGIC | 33 | `DIAS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 34 | `OBSERVAÇÕES DA GERÊNCIA` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo textual operacional sem necessidade analítica identificada. |
# MAGIC | 35 | `CBO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 36 | `# CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Documento cadastral sem necessidade analítica identificada. |
# MAGIC | 37 | `SÉRIE CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Documento cadastral. |
# MAGIC | 38 | `UF CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Documento cadastral. |
# MAGIC | 39 | `EXPEDIÇÃO CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Documento cadastral. |
# MAGIC | 40 | `VALIDADE CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Documento cadastral. |
# MAGIC | 41 | `NASCIMENTO` | STRING | `data_nascimento` | DATE | **Utilizado em EMPREGADO.** Converter STRING → DATE. |
# MAGIC | 42 | `NOME DA MÃE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação cadastral sem necessidade analítica para o MVP. |
# MAGIC | 43 | `NOME DO PAI` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação cadastral sem necessidade analítica para o MVP. |
# MAGIC | 44 | `NACIONALIDADE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 45 | `NATURALIZADO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 46 | `NATURALIDADE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 47 | `UF46` | STRING | — | — | **Não utilizado em EMPREGADO.** Corresponde à UF da naturalidade. |
# MAGIC | 48 | `GRAU DE INSTRUÇÃO` | STRING | `grau_instrucao` | STRING | **Utilizado em EMPREGADO.** Permite análise do perfil educacional. |
# MAGIC | 49 | `FORMAÇÃO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação sem necessidade analítica identificada para o MVP. |
# MAGIC | 50 | `# RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 51 | `TIPO RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 52 | `EXPEDITOR RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 53 | `UF RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 54 | `EXPEDIÇÃO RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 55 | `VALIDADE RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 56 | `# PIS/PASEP` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 57 | `CADASTRO PIS/PASEP` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 58 | `FUNÇÃO CONSELHO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação de conselho profissional sem necessidade analítica identificada para o MVP. |
# MAGIC | 59 | `CONSELHO58` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo `CONSELHO` associado aos dados profissionais, sem necessidade analítica identificada para o MVP. |
# MAGIC | 60 | `# CONSELHO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 61 | `EMISSÃO CONSELHO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 62 | `VALIDADE CONSELHO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 63 | `# TÍTULO DE ELEITOR` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 64 | `UF TÍTULO  ELEITOR` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 65 | `ZONA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 66 | `SEÇÃO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 67 | `MUNICÍPIO66` | STRING | — | — | **Não utilizado em EMPREGADO.** Corresponde ao município associado ao título de eleitor e não possui necessidade analítica identificada para o MVP. |
# MAGIC | 68 | `# / SÉRIE CERTIFICADO RESERVISTA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 69 | `EMISSOR` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 70 | `CATEGORIA69` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 71 | `# CNH` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 72 | `CATEGORIA71` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 73 | `VALIDADE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 74 | `ENDEREÇO` | STRING | `logradouro` | STRING | **Utilizado em EMPREGADO.** Mantido como endereço/logradouro conforme estrutura disponível na origem. |
# MAGIC | 75 | `BAIRRO` | STRING | `bairro` | STRING | **Utilizado em EMPREGADO.** |
# MAGIC | 76 | `MUNICÍPIO75` | STRING | `cidade` | STRING | **Utilizado em EMPREGADO.** Corresponde ao município do endereço. |
# MAGIC | 77 | `UF76` | STRING | `estado` | STRING | **Utilizado em EMPREGADO.** Corresponde à UF do endereço, distinguindo-se de `UF46`, que se refere à naturalidade. |
# MAGIC | 78 | `CEP` | STRING | `cep` | STRING | **Utilizado em EMPREGADO.** Mantido como STRING para preservar sua natureza de identificador postal e eventuais zeros à esquerda. |
# MAGIC | 79 | `PAÍS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 80 | `NÍVEL` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 81 | `CÓD NÍVEL` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 82 | `_c81` | STRING |  — |  — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 83 | `OPTANTE FGTS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 84 | `EM:` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 85 | `SINDICATO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 86 | `SIGLA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 87 | `DATA BASE` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 88 | `SINDICALIZADO?` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 89 | `DESCONTO EM FOLHA?` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 90 | `ÚLT. CONTRIB.` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 91 | `VALOR` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 92 | `BANCO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 93 | `AGÊNCIA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 94 | `C/C` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 95 | `ÚLT. ALOCAÇÃO` | STRING | — | — | **Tratado em ALOCAÇÃO.** |
# MAGIC | 96 | `OBS.` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 97 | `ÚLTIMA ATUALIZAÇÃO` | STRING |  — |  — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 98 | `POR ANONIMIZADO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 99 | `_c98` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP.|
# MAGIC | 100 | `MODELO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 101 | `UTILIDADES` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 102 | `PI/DA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 103 | `TRANSPORTE` | DECIMAL(35,15) | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 104 | `ALIMENTAÇÃO` | BIGINT | — | — | **Tratado em BENEFÍCIO.** |
# MAGIC | 105 | `REFEIÇÃO` | DECIMAL(34,14) | — | — | **Tratado em BENEFÍCIO.** |
# MAGIC | 106 | `VT` | STRING | — | — | **Tratado em BENEFÍCIO.** Informação relacionada a vale-transporte. |
# MAGIC | 107 | `BENEFÍCIOS` | DECIMAL(6,2) | — | — | **Tratado em BENEFÍCIO.** |
# MAGIC | 108 | `FOTO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 109 | `CV` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 110 | `CONTRATO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 111 | `CPF` | STRING | — | — | **Não utilizado como CPF analítico de EMPREGADO.** O `CPF ANONIMIZADO` é o campo previsto para identificação da pessoa. |
# MAGIC | 112 | `EXAME MÉDICO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 113 | `CTPS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 114 | `DIPLOMA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 115 | `RG` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 116 | `PIS` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 117 | `CONSELHO116` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 118 | `TÍTULO ELEITOR` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 119 | `RESERVISTA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 120 | `COMPROVANTE RESIDÊNCIA` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 121 | `SINDICALIZADO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 122 | `TIPO SANGUÍNEO121` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 123 | `DOC1` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 124 | `DOC2` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 125 | `DOC3` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 126 | `DOC4` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 127 | `DOC5` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 128 | `DOC6` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 129 | `_c128` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 130 | `TIPO SANGUÍNEO129` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 131 | `TIME / MUNIC[IPIO / UF` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 132 | `MANEQUIM` | BIGINT | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 133 | `SAPATO` | BIGINT | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 134 | `_c133` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 135 | `_c134` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 136 | `IDADE` | STRING | — | — | **Derivado/recalculado.** Não transportar diretamente. Idade pode ser calculada a partir de `data_nascimento` e da data de referência. |
# MAGIC | 137 | `FAIXA` | STRING | — | — | **Derivado/recalculado**, caso represente faixa etária. Deve ser obtida a partir da idade/data de nascimento conforme regra definida. |
# MAGIC | 138 | `_c137` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 139 | `_c138` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 140 | `_c139` | BIGINT | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 141 | `_c140` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 142 | `13o. ADIANTADO (R$)` | DECIMAL(4,1) | — | — | **Não utilizado em EMPREGADO.** Informação administrativa/remuneratória sem necessidade analítica identificada para EMPREGADO. |
# MAGIC | 143 | `MOTIVO142` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 144 | `ADMISSÃO REAL` | TIMESTAMP | — | — | **Não utilizado em EMPREGADO.** Campo auxiliar da planilha de origem. Para o modelo analítico, a data de admissão será obtida de `ADMISSÃO`, evitando a manutenção de duas informações com a mesma finalidade.  |
# MAGIC | 145 | `DESLIGAMENTO144` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo auxiliar da planilha de origem. A informação de desligamento considerada no modelo será proveniente de `DESLIGAMENTO11` e tratada na entidade `DESLIGAMENTO`, evitando duplicidade da informação.|
# MAGIC | 146 | `MOTIVO145` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo auxiliar associado ao bloco final da planilha. O motivo de desligamento considerado no modelo será proveniente de `MOTIVO PRINCIPAL` e tratado na entidade `DESLIGAMENTO`. |
# MAGIC | 147 | `_c146` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 148 | `_c147` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 149 | `_c148` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 150 | `_c149` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 151 | `POSIÇÃO` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 152 | `_c151` | STRING | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC | 153 | `AAAAMM ENTRA` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo auxiliar no formato ano/mês. A informação temporal necessária pode ser derivada de `data_admissao`, não sendo necessário manter o atributo na Silver. |
# MAGIC | 154 | `AAAAMM SAI` | STRING | — | — | **Não utilizado em EMPREGADO.** Campo auxiliar no formato ano/mês. A informação temporal necessária pode ser derivada da data de desligamento tratada em `DESLIGAMENTO`, não sendo necessário manter o atributo na Silver.  |
# MAGIC | 155 | `_c154` | DECIMAL(36,16) | — | — | **Não utilizado em EMPREGADO.** Informação administrativa da origem sem necessidade analítica identificada para o MVP. |
# MAGIC
# MAGIC #### Observações sobre a transformação
# MAGIC
# MAGIC A estrutura acima constitui a matriz inicial de rastreabilidade entre a tabela Bronze e a futura camada Silver. 
# MAGIC
# MAGIC A entidade `EMPREGADO` da Silver não reproduzirá as 155 colunas da Bronze. Informações pertencentes a outros domínios serão direcionadas às respectivas entidades quando aplicável, especialmente `SALÁRIO`, `BENEFÍCIO`, `FÉRIAS`, `ALOCAÇÃO` e `DESLIGAMENTO`.
# MAGIC
# MAGIC Campos calculáveis, como duração do vínculo e idade, não precisam ser transportados diretamente da origem quando puderem ser obtidos de atributos básicos e de uma data de referência.
# MAGIC
# MAGIC O `DRT` representa o **vínculo empregatício** e será tratado como identificador textual na Silver. Uma mesma pessoa pode possuir diferentes DRTs ao longo do tempo em situações de recontratação. O `CPF ANONIMIZADO` permite identificar esses diferentes vínculos como pertencentes à mesma pessoa.
# MAGIC
# MAGIC Os nomes com sufixos numéricos devem ser interpretados de acordo com sua posição e contexto na planilha de origem. Assim, por exemplo, `UF46` corresponde à UF associada à naturalidade, enquanto `UF76` corresponde à UF associada ao endereço. Da mesma forma, `MUNICÍPIO66` está associado ao bloco eleitoral e `MUNICÍPIO75` ao endereço.
# MAGIC
# MAGIC As colunas `_c...`, provenientes de posições sem cabeçalho na estrutura de origem, são utilizadas como campos auxiliares para cálculos. Para o contexto do MVP, as informações resultantes desses cálculos já estão contempladas nos atributos correspondentes ou foram descartadas conforme o escopo analítico definido, não sendo necessária a manutenção dessas colunas na Silver.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2 Análise da qualidade dos dados
# MAGIC
# MAGIC Após a análise das colunas e dos tipos de dados, é necessário avaliar a qualidade dos registros presentes na camada Bronze, buscando identificar valores nulos, duplicidades e possíveis inconsistências. Essa análise também deverá verificar a consistência dos identificadores, das datas e a coerência entre campos relacionados.
# MAGIC
# MAGIC Como a tabela Bronze contém atributos que serão utilizados diretamente em `EMPREGADO`, atributos destinados a outras entidades e campos que não fazem parte do escopo analítico do MVP, os diagnósticos de qualidade serão utilizados principalmente para avaliar os dados necessários à construção da tabela Silver e apoiar as decisões de tratamento.
# MAGIC
# MAGIC ### 1.2.1 Consulta 02 — Identificação da quantidade de registros e valores nulos
# MAGIC
# MAGIC A consulta tem como objetivo identificar a quantidade total de registros da tabela `workspace.bronze.empregados_anonimizados` e a ocorrência de valores nulos nos atributos relevantes para a transformação Bronze → Silver. A comparação entre a quantidade de valores nulos e o total de registros permitirá avaliar a representatividade dos dados ausentes e identificar atributos que possam exigir tratamento antes da construção da tabela Silver.
# MAGIC
# MAGIC ### 1.2.1.1 Identificação da quantidade de registros
# MAGIC
# MAGIC Inicialmente, será verificada a quantidade total de registros existentes na tabela Bronze. Esse valor servirá como referência para as análises subsequentes de valores nulos, duplicidades e demais verificações de qualidade.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) AS total_registros
# MAGIC FROM workspace.bronze.empregados_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC **Resultado:** a tabela `workspace.bronze.empregados_anonimizados` possui **734 registros**. Esse total será utilizado como referência para as análises subsequentes de qualidade dos dados, especialmente na avaliação da proporção de valores nulos.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.1.2 Resultado da quantidade de registros
# MAGIC
# MAGIC A tabela `workspace.bronze.empregados_anonimizados` possui **734 registros** na camada Bronze. Esse valor será utilizado como referência para avaliar a representatividade dos valores nulos identificados em cada atributo.
# MAGIC
# MAGIC ### 1.2.1.3 Resultado da quantidade de nulos
# MAGIC
# MAGIC Nesta etapa será identificada a quantidade de valores nulos em cada atributo da tabela. Os resultados serão comparados com o total de **734 registros**, permitindo avaliar a proporção de dados ausentes e sua relevância para a utilização de cada atributo na camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(CASE WHEN DRT IS NULL THEN 1 END) AS nulos_drt,
# MAGIC     COUNT(CASE WHEN `NOME ANONIMIZADO` IS NULL THEN 1 END) AS nulos_nome,
# MAGIC     COUNT(CASE WHEN `GÊNERO` IS NULL THEN 1 END) AS nulos_genero,
# MAGIC     COUNT(CASE WHEN `CPF ANONIMIZADO` IS NULL THEN 1 END) AS nulos_cpf,
# MAGIC     COUNT(CASE WHEN `ADMISSÃO` IS NULL THEN 1 END) AS nulos_admissao,
# MAGIC     COUNT(CASE WHEN `ESTADO CIVIL` IS NULL THEN 1 END) AS nulos_estado_civil,
# MAGIC     COUNT(CASE WHEN `NASCIMENTO` IS NULL THEN 1 END) AS nulos_nascimento,
# MAGIC     COUNT(CASE WHEN `GRAU DE INSTRUÇÃO` IS NULL THEN 1 END) AS nulos_grau_instrucao,
# MAGIC     COUNT(CASE WHEN `ENDEREÇO` IS NULL THEN 1 END) AS nulos_endereco,
# MAGIC     COUNT(CASE WHEN `BAIRRO` IS NULL THEN 1 END) AS nulos_bairro,
# MAGIC     COUNT(CASE WHEN `MUNICÍPIO75` IS NULL THEN 1 END) AS nulos_cidade,
# MAGIC     COUNT(CASE WHEN `UF76` IS NULL THEN 1 END) AS nulos_estado,
# MAGIC     COUNT(CASE WHEN `CEP` IS NULL THEN 1 END) AS nulos_cep
# MAGIC FROM workspace.bronze.empregados_anonimizados;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.1.4 Definição dos registros válidos para a análise de EMPREGADO
# MAGIC
# MAGIC A consulta inicial identificou 734 registros na tabela Bronze. Entretanto, a análise de valores nulos mostrou que 387 desses registros não possuem `DRT` preenchido, resultando em 347 registros com esse identificador.
# MAGIC
# MAGIC No modelo adotado para o MVP, o `DRT` identifica o vínculo empregatício. Cada admissão gera um DRT e, em caso de uma nova admissão da mesma pessoa, um novo DRT é atribuído ao novo vínculo. Dessa forma, uma linha sem `DRT` não permite identificar um vínculo empregatício válido e, consequentemente, não poderá compor a tabela `EMPREGADO` da camada Silver.
# MAGIC
# MAGIC Por esse motivo, os 387 registros sem `DRT` serão desconsiderados na transformação de `EMPREGADO`, e as análises de qualidade subsequentes utilizarão como universo de referência os **347 registros com `DRT` preenchido**.
# MAGIC
# MAGIC A análise de valores nulos será, portanto, refeita considerando somente esses 347 registros. Dessa forma, será possível avaliar a qualidade dos demais atributos apenas entre os registros que efetivamente poderão compor `EMPREGADO` na camada Silver, evitando que as linhas sem identificação de vínculo distorçam a avaliação da completude dos dados.
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     COUNT(*) AS total_registros_validos,
# MAGIC     COUNT(CASE WHEN `NOME ANONIMIZADO` IS NULL THEN 1 END) AS nulos_nome,
# MAGIC     COUNT(CASE WHEN `GÊNERO` IS NULL THEN 1 END) AS nulos_genero,
# MAGIC     COUNT(CASE WHEN `CPF ANONIMIZADO` IS NULL THEN 1 END) AS nulos_cpf,
# MAGIC     COUNT(CASE WHEN `ADMISSÃO` IS NULL THEN 1 END) AS nulos_admissao,
# MAGIC     COUNT(CASE WHEN `ESTADO CIVIL` IS NULL THEN 1 END) AS nulos_estado_civil,
# MAGIC     COUNT(CASE WHEN `NASCIMENTO` IS NULL THEN 1 END) AS nulos_nascimento,
# MAGIC     COUNT(CASE WHEN `GRAU DE INSTRUÇÃO` IS NULL THEN 1 END) AS nulos_grau_instrucao,
# MAGIC     COUNT(CASE WHEN `ENDEREÇO` IS NULL THEN 1 END) AS nulos_endereco,
# MAGIC     COUNT(CASE WHEN `BAIRRO` IS NULL THEN 1 END) AS nulos_bairro,
# MAGIC     COUNT(CASE WHEN `MUNICÍPIO75` IS NULL THEN 1 END) AS nulos_cidade,
# MAGIC     COUNT(CASE WHEN `UF76` IS NULL THEN 1 END) AS nulos_estado,
# MAGIC     COUNT(CASE WHEN `CEP` IS NULL THEN 1 END) AS nulos_cep
# MAGIC FROM workspace.bronze.empregados_anonimizados
# MAGIC WHERE DRT IS NOT NULL;
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.1.4 Resultado da análise de valores nulos nos registros válidos**
# MAGIC
# MAGIC Considerando apenas os **347 registros com `DRT` preenchido**, os atributos `NOME ANONIMIZADO`, `GÊNERO`, `CPF ANONIMIZADO`, `ADMISSÃO`, `ESTADO CIVIL`, `NASCIMENTO` e `GRAU DE INSTRUÇÃO` não apresentaram valores nulos.
# MAGIC
# MAGIC Entre os atributos relacionados ao endereço, foram identificados **1 valor nulo** em `ENDEREÇO`, `BAIRRO`, `MUNICÍPIO75` e `UF76`, correspondendo a aproximadamente **0,29%** dos registros válidos. No atributo `CEP`, foram identificados **3 valores nulos**, correspondendo a aproximadamente **0,86%** dos registros.
# MAGIC
# MAGIC A ocorrência de valores nulos entre os registros válidos é, portanto, reduzida e não inviabiliza a utilização dos atributos selecionados para `EMPREGADO` na camada Silver. Nos casos em que a informação não estiver disponível na origem, o valor nulo será preservado, evitando a criação ou inferência de dados sem fundamento na fonte.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.2 Análise da consistência do identificador DRT
# MAGIC
# MAGIC Após a definição dos registros válidos, é necessário verificar a consistência do `DRT`, utilizado no modelo como identificador do vínculo empregatício.
# MAGIC
# MAGIC Como cada admissão gera um DRT e cada DRT deve representar um único vínculo, inicialmente será verificado se existem valores de `DRT` repetidos entre os 347 registros considerados válidos. A existência de repetições poderá indicar registros duplicados ou inconsistências que deverão ser analisadas antes da construção da camada Silver.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT DRT, COUNT(*) AS quantidade
# MAGIC FROM workspace.bronze.empregados_anonimizados
# MAGIC WHERE DRT IS NOT NULL
# MAGIC GROUP BY DRT
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY quantidade DESC, DRT;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.2 Resultado da análise de consistência do identificador DRT**
# MAGIC
# MAGIC A consulta não retornou registros, indicando que não existem valores de `DRT` duplicados entre os **347 registros válidos**.
# MAGIC
# MAGIC O resultado confirma que cada `DRT` ocorre uma única vez na base analisada, sendo consistente com a regra de negócio adotada no MVP, segundo a qual o `DRT` identifica individualmente cada vínculo empregatício.
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.3 Análise da relação entre CPF e DRT
# MAGIC
# MAGIC Após confirmar a unicidade do `DRT`, será analisada sua relação com o `CPF ANONIMIZADO`.
# MAGIC
# MAGIC Enquanto o `DRT` identifica cada vínculo empregatício, o `CPF ANONIMIZADO` identifica a pessoa. Dessa forma, uma mesma pessoa poderá estar associada a mais de um DRT caso tenha sido admitida em momentos distintos.
# MAGIC
# MAGIC A consulta a seguir verificará a existência de CPFs associados a mais de um DRT. A ocorrência desses casos não será considerada automaticamente uma inconsistência, pois poderá representar situações de readmissão que deverão ser avaliadas a partir dos dados disponíveis.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     `CPF ANONIMIZADO` AS cpf,
# MAGIC     `NOME ANONIMIZADO` AS nome,
# MAGIC     COUNT(DISTINCT DRT) AS quantidade_drts
# MAGIC FROM workspace.bronze.empregados_anonimizados
# MAGIC WHERE DRT IS NOT NULL
# MAGIC GROUP BY `CPF ANONIMIZADO`,
# MAGIC         `NOME ANONIMIZADO`        
# MAGIC HAVING COUNT(DISTINCT DRT) > 1
# MAGIC ORDER BY quantidade_drts DESC, nome ASC;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.3 Resultado da análise da relação entre CPF e DRT**
# MAGIC
# MAGIC A consulta identificou **14 pessoas com mais de um DRT associado ao mesmo `CPF ANONIMIZADO`**. Destas, 11 possuem dois DRTs distintos e 3 possuem três DRTs distintos.
# MAGIC
# MAGIC Esse resultado não caracteriza, isoladamente, uma inconsistência. No modelo adotado, o `CPF ANONIMIZADO` identifica a pessoa, enquanto o `DRT` identifica cada vínculo empregatício. Assim, uma mesma pessoa pode possuir diferentes DRTs caso tenha sido admitida mais de uma vez pela empresa.
# MAGIC
# MAGIC Para verificar se os casos identificados são compatíveis com essa regra de negócio, será analisada a relação entre CPF, DRT e data de admissão.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC     `CPF ANONIMIZADO` AS cpf,
# MAGIC     `NOME ANONIMIZADO` AS nome,
# MAGIC     DRT AS drt,
# MAGIC     `ADMISSÃO` AS data_admissao
# MAGIC FROM workspace.bronze.empregados_anonimizados
# MAGIC WHERE DRT IS NOT NULL
# MAGIC   AND `CPF ANONIMIZADO` IN (
# MAGIC       SELECT `CPF ANONIMIZADO`
# MAGIC       FROM workspace.bronze.empregados_anonimizados
# MAGIC       WHERE DRT IS NOT NULL
# MAGIC       GROUP BY `CPF ANONIMIZADO`
# MAGIC       HAVING COUNT(DISTINCT DRT) > 1
# MAGIC   )
# MAGIC ORDER BY cpf, data_admissao, drt;

# COMMAND ----------

# MAGIC %md
# MAGIC **1.2.3 Resultado da análise da relação entre CPF, DRT e Data de Admissão**
# MAGIC
# MAGIC A análise dos casos em que um mesmo `CPF ANONIMIZADO` está associado a mais de um `DRT` identificou **14 pessoas**, correspondentes a **31 vínculos empregatícios**.
# MAGIC
# MAGIC A consulta detalhada mostrou que os diferentes DRTs associados a uma mesma pessoa possuem datas de admissão distintas, sendo compatíveis com situações de novas admissões ao longo do tempo.
# MAGIC
# MAGIC Dessa forma, a existência de múltiplos DRTs para um mesmo CPF não caracteriza duplicidade ou inconsistência nos dados. O resultado confirma a regra adotada no modelo: o `CPF ANONIMIZADO` identifica a pessoa, enquanto o `DRT` identifica cada vínculo empregatício individualmente.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2.2 Análise de duplicidades
# MAGIC
# MAGIC Uma vez estabelecida a quantidade de registros válidos, é necessário verificar a existência de registros duplicados. Para essa análise, será utilizado inicialmente o atributo DRT, que identifica a matrícula do empregado e, portanto, deve apresentar um único registro para cada empregado na tabela. A consulta a seguir tem como objetivo verificar a existência de valores de DRT repetidos entre os registros válidos.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1.2.4 Conclusão da análise de qualidade dos dados
# MAGIC
# MAGIC A análise de qualidade permitiu definir o conjunto de registros que será utilizado na construção de `EMPREGADO` na camada Silver e verificar a consistência dos principais identificadores.
# MAGIC
# MAGIC Dos 734 registros existentes na tabela Bronze, 347 possuem `DRT` preenchido e serão considerados registros válidos para `EMPREGADO`. Não foram identificados DRTs duplicados nesse conjunto.
# MAGIC
# MAGIC A análise da relação entre `CPF ANONIMIZADO` e `DRT` identificou pessoas associadas a mais de um DRT. A verificação das respectivas datas de admissão mostrou que esses registros correspondem a vínculos distintos, sendo compatíveis com situações de novas admissões. Dessa forma, mantém-se a regra de negócio segundo a qual o `CPF ANONIMIZADO` identifica a pessoa e o `DRT` identifica cada vínculo empregatício.
# MAGIC
# MAGIC Nos 347 registros válidos, os atributos selecionados para `EMPREGADO` apresentaram elevada completude. As ocorrências de valores nulos ficaram restritas a poucos registros nos atributos relacionados ao endereço, não inviabilizando sua utilização.
# MAGIC
# MAGIC Com essas verificações, a análise de qualidade da tabela Bronze para `EMPREGADO` é considerada concluída. Os tratamentos relacionados à padronização, conversão de tipos de dados e demais adequações dos atributos selecionados serão realizados na transformação para a camada Silver.