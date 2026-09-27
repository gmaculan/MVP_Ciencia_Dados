# MVP — Ciência de Dados e Analytics

MVP desenvolvido no contexto da Pós-Graduação em Ciência de Dados e Analytics, com implementação no Databricks e organização dos dados segundo a arquitetura Medalhão (**Bronze → Silver → Gold**).

O projeto integra dados de **Recursos Humanos, Financeiro e Faturamento**, estruturando um ambiente analítico para responder perguntas de negócio a partir de dados empresariais particulares devidamente anonimizados.

## Objetivo

Construir um pipeline de dados de ponta a ponta, desde a carga e preparação das fontes até a modelagem analítica e a realização de consultas de negócio, documentando as transformações, premissas, controles de qualidade e limitações das fontes.

## Arquitetura

- **Bronze:** persistência das fontes já anonimizadas.
- **Silver:** limpeza, tipagem, padronização e aplicação das regras de negócio.
- **Gold:** dimensões e fatos destinados às análises.
- **Análises:** notebooks de RH, Financeiro e Faturamento.

A implementação utiliza o catálogo `workspace` do Databricks, com schemas `bronze`, `silver` e `gold`.

## Estrutura do repositório

```text
notebooks/
├── bronze/          # notebooks de carga Bronze
├── bronze_silver/   # processos em que Bronze e Silver foram implementadas no mesmo notebook
├── silver/          # preparação e validação da camada Silver
├── gold/            # dimensões e fatos da camada Gold
└── analises/        # perguntas de negócio de RH, Financeiro e Faturamento

documentacao/
├── Documentacao_Completa_MVP.pdf
├── Dicionario_de_Dados.xlsx
├── Modelo_Conceitual.png
└── Modelo_Logico.png
```

## Camada Gold

### Dimensões

- `dim_alocacao`
- `dim_empregado`
- `dim_entidade`
- `dim_saude`
- `dim_tempo`

### Fatos

- `fato_custo_pessoal`
- `fato_dependentes`
- `fato_faturamento`
- `fato_ferias`
- `fato_fornecedor`

## Análises de negócio

Os notebooks finais estão em `notebooks/analises/` e contemplam:

- **RH:** férias, folha/custo de pessoal, turnover, desligamentos, tempo de permanência, dependentes e impacto do plano de saúde.
- **Financeiro:** custos de fornecedores e fluxo financeiro demonstrativo.
- **Faturamento:** evolução do faturamento, participação e concentração por cliente e ticket médio.

As análises de alocação originalmente previstas não foram executadas porque a fonte disponível não contém histórico completo de movimentações, horas/timesheets ou base temporal suficiente para associar de forma consistente empregado, custo e receita à alocação. A limitação e seus impactos estão documentados no relatório completo.

## Dados e privacidade

As fontes são dados empresariais particulares e foram **anonimizadas antes da persistência na camada Bronze**. Os arquivos de dados e as tabelas Bronze não são disponibilizados neste repositório. O notebook utilizado no processo de anonimização também não é publicado, evitando a exposição de referências aos dados originais.

Assim, o repositório disponibiliza o código do pipeline, as análises e a documentação necessária para compreender a solução, mas não os registros utilizados na execução.

## Documentação

A documentação detalhada do projeto está em [`documentacao/Documentacao_Completa_MVP.pdf`](documentacao/Documentacao_Completa_MVP.pdf). Ela apresenta contexto, fontes, premissas, arquitetura, pipeline, estado final das camadas Silver e Gold, qualidade dos dados, limitações, análises, evidências do Databricks, Unity Catalog, autoavaliação, dicionário de dados e modelos conceitual e lógico.

O dicionário completo também está disponível em [`documentacao/Dicionario_de_Dados.xlsx`](documentacao/Dicionario_de_Dados.xlsx).

## Tecnologias

- Databricks
- Apache Spark / PySpark
- Spark SQL / SQL
- Python
- Delta Lake
- Unity Catalog

## Observação sobre reprodutibilidade

Os notebooks são disponibilizados em formato-fonte exportado do Databricks. Como as bases empresariais não são publicadas, a execução integral depende de fontes com estruturas equivalentes às documentadas no dicionário de dados e no relatório do MVP.
