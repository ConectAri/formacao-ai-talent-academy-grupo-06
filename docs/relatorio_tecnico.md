# Relatório Técnico — Analytics em Saúde Pública: Mortalidade no Brasil (DATASUS/SIM)

**Projeto Final — AI Talent Academy (White Cube), Grupo 6**
**Trilha:** Analytics
**Última atualização:** 20/09/2026, por Ariane (P5 — Documentação)

> Este documento é colaborativo e **vivo** — cada seção pertence a um papel do grupo (P1 a P4) e deve ser atualizada pela pessoa responsável conforme sua etapa avança. P5 consolida e mantém a coerência geral. O README do repositório traz uma versão resumida e sem atribuição de responsáveis; este relatório é a fonte de verdade para o detalhamento técnico completo.

---

## 1. Visão geral do projeto

O grupo desenvolve um projeto de Analytics sobre **mortalidade no Brasil**, usando dados públicos do **DATASUS/SIM (Sistema de Informações sobre Mortalidade)**, cobrindo o período de **2016 a 2026** (2025 preliminar, 2026 em 1ª prévia).

**Nota de escopo:** o projeto pivotou da proposta original registrada no Forms 01 (internações hospitalares via SIH/SUS) para mortalidade (SIM), já que o material de trabalho do grupo — os 7 relatórios estruturais e os dados brutos — é de mortalidade. Essa mudança foi validada com a equipe em 20/09/2026.

O SIM está organizado em 7 categorias temáticas. **As 7 já foram extraídas e estão disponíveis no repositório** (`data/raw/datasus_sim/`). Até o momento, apenas **Mortalidade Geral** (categoria piloto) foi processada de ponta a ponta pela pipeline de limpeza:

| Categoria | Arquivos brutos | Status |
|---|---|---|
| Mortalidade Geral | 45 CSVs | ✅ Extraída, limpa, padronizada e consolidada |
| Óbitos Infantis | 56 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |
| Óbitos Fetais | 45 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |
| Óbitos por Causas Externas | 45 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |
| Óbitos de Mulheres em Idade Fértil e Maternos | 44 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |
| Causas Evitáveis | 55 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |
| Mortalidade de Residentes no Exterior | 47 CSVs | ✅ Extraída e disponível no repositório; limpeza pendente |

---

## 2. P1 — Extração de Dados

**Responsável:** Roboaldo
**Status:** ✅ extração das 7 categorias concluída e disponível no repositório (`data/raw/datasus_sim/`). Documentação do processo ainda parcial — seção a ser complementada pelo responsável.

### O que está confirmado
- Fonte: TabNet/DATASUS, sistema SIM.
- Formato de extração observado nos arquivos: **exportação manual via interface web do TabNet**, gerando CSVs no padrão `sim_cnv_<código>.csv` (encoding ISO-8859-1, separador `;`, com cabeçalho de metadados nas 3 primeiras linhas).
- Cada categoria foi extraída com 4 cortes/dimensões (Capítulo CID-10, Faixa Etária, Sexo, Local de Ocorrência) por ano, resultando em ~4 arquivos por ano por categoria (2016 tem um 5º arquivo atípico em Mortalidade Geral — ver seção P2).
- Período coberto: 2016–2026.

### ⚠️ Divergência a esclarecer com o P1
O plano registrado no Alinhamento do Grupo 6 previa extração via **PySUS** (biblioteca Python que acessa o FTP do DATASUS programaticamente). O padrão observado nos arquivos reais, no entanto, é de **exportação manual via TabNet** (não há rastro de uso do PySUS nos arquivos brutos). Isso não é um problema — o dado é válido de qualquer forma — mas o P1 deveria confirmar e documentar qual método foi de fato usado, para o relatório final refletir a realidade.

### Pendências confirmadas no repositório (a resolver antes da limpeza de cada categoria)
Conferidas em 20/09/2026, após o envio das 7 categorias — seguem presentes:
- 3 arquivos duplicados com sufixo `(1).csv`:
  - `data/raw/datasus_sim/causas_evitaveis/sim_cnv_evita10uf180517138_0_146_204 (1).csv`
  - `data/raw/datasus_sim/obitos_infantis/sim_cnv_inf10uf190033138_0_146_204 (1).csv`
  - `data/raw/datasus_sim/obitos_causas_externas/sim_cnv_ext10uf193744138_0_146_204 (1).csv`
- 1 arquivo de Causas Externas classificado incorretamente dentro de Óbitos Fetais:
  - `data/raw/datasus_sim/obitos_fetais/sim_cnv_ext10uf193101138_0_146_204.csv`

**[Espaço para o P1 preencher: processo de extração, scripts usados (se houver), decisões sobre recorte de dados, dificuldades encontradas.]**

---

## 3. P2 — Limpeza e Tratamento de Dados

**Responsável:** Ariane
**Status:** ✅ concluído para Mortalidade Geral (categoria piloto).

Pipeline de 4 etapas, cada uma com script próprio em `src/cleaning/`, executáveis em sequência ou via `validacao_final.py` (roda tudo e confere qualidade automaticamente):

### Etapa 4 — Tratamento de nulos
- **Achado com evidência:** o caractere `"-"` representa **zero real**, não dado suprimido por sigilo estatístico — validado comparando soma das colunas contra a coluna "Total" em 1.408 linhas (100% de correspondência).
- Regra aplicada: `NaN → 0`.
- Achado adicional: colunas de capítulo CID-10 que tiveram zero ocorrências em todas as UFs num ano específico são omitidas pelo TabNet naquele ano (ex: Cap XIX só aparece em 2023, Cap XXII só em 2026) — tratado com a mesma regra.

### Etapa 3 — Duplicados
- Verificação por hash MD5: nenhuma duplicata exata em Mortalidade Geral.
- Decisão do grupo: o arquivo atípico de 2016 (Região de residência × Região de ocorrência) foi tratado como **dataset complementar/exploratório**, fora da base consolidada principal.

### Etapa 5 — Padronização de categorias
- Coluna única "Região/UF" separada em 4 colunas explícitas: `nivel`, `regiao`, `uf`, `sigla`.
- Linha "Total" (Brasil) removida — recalculável a partir dos estados.
- Capítulos CID-10 mapeados para descrição oficial (OMS), tabela de referência reutilizável pelas outras 6 categorias.
- Tabela em formato longo/tidy (`capitulo_cid10_long.csv`) gerada para consumo direto em BI.

### Etapa 6 — Consolidação
- Tabela-fato única (`fato_obitos.csv`) construída após validar que o total de óbitos é idêntico entre as 4 dimensões em 100% das 352 combinações (ano, UF/Região) — evidência de que as dimensões descrevem a mesma população de óbitos.

### Etapa 7 — Validação final
- Script único (`validacao_final.py`) roda a pipeline inteira do zero e confere 24 critérios de qualidade automaticamente. Resultado: **24/24 OK**.

### Entregável final (Mortalidade Geral)
```
data/processed/mortalidade_geral/
├── fato_obitos.csv           (tabela-fato: 352 linhas)
├── capitulo_cid10.csv
├── capitulo_cid10_long.csv   (recomendado para BI)
├── faixa_etaria.csv
├── sexo.csv
├── local_ocorrencia.csv
└── referencia_cid10.csv
```

Detalhamento completo de cada decisão técnica: ver `data/dictionary/dicionario_dados.md`.

### Pendências para replicar nas outras 6 categorias
- As 6 categorias restantes **já estão disponíveis no repositório** (ver seção 1), mas ainda não passaram pela pipeline de limpeza.
- Antes de rodar a limpeza em cada uma, resolver as pendências herdadas do P1 (ver seção 2): remover/consolidar os 3 arquivos `(1).csv` duplicados e realocar o arquivo de Causas Externas que está dentro de Óbitos Fetais.
- Adaptar os scripts (`limpeza`, `padronizacao`, `consolidacao`, `validacao`) para a estrutura de dimensão específica de cada categoria — nem todas têm exatamente as mesmas 4 dimensões de Mortalidade Geral (ex: Óbitos Fetais provavelmente tem "Duração da Gestação" em vez de "Local de Ocorrência", conforme o relatório-esqueleto original de cada categoria).

---

## 4. P3 — Análise Exploratória (EDA)

**Responsável:** Levi Lima
**Status:** ✅ concluído (23/09/2026) para a categoria Mortalidade Geral.

**Notebook:** `notebooks/02_eda_mortalidade_geral.ipynb` (script-fonte legível em `notebooks/02_eda_mortalidade_geral.py`, formato jupytext).
**Gráficos exportados:** `reports/mortalidade_geral/fig_*.png`.
**Fonte dos dados:** exclusivamente `data/processed/mortalidade_geral/` (base já limpa e validada pelo P2 — 24/24 checagens OK). Nenhum dado bruto foi reprocessado.

### Perguntas de negócio exploradas
1. Quais são as principais causas de óbito (capítulos CID-10) no período?
2. Como o total de óbitos evoluiu ano a ano?
3. Existe tendência de crescimento/queda ao longo da série?
4. Como os óbitos variam por faixa etária e por sexo?
5. Existe diferença relevante entre regiões/UFs?

### Principais achados
1. **Causas de óbito:** doenças do aparelho circulatório (Cap IX), neoplasias (Cap II) e doenças do aparelho respiratório (Cap X) são as três maiores causas de óbito no Brasil no período, nessa ordem — concentram a maior parte dos óbitos com causa definida. Sugestão para o P4: destacar esses 3 capítulos como KPI fixo no dashboard.
2. **Série temporal:** salto atípico de óbitos em 2020-2021 (+18% em 2020 sobre 2019), coincidindo com a pandemia de COVID-19, sobre uma tendência de fundo já crescente (~2-3%/ano no período pré-pandemia). 2025 (preliminar) e 2026 (1ª prévia) ainda estão incompletos no TabNet e **não devem ser lidos como queda real** — recomenda-se que o P4 marque visualmente esses dois anos como "dado sujeito a revisão".
3. **Tendência/sazonalidade:** a base é consolidada em nível anual, então não é possível avaliar sazonalidade intra-ano; a análise de tendência foi feita ano a ano (ver item 2).
4. **Faixa etária e sexo:** óbitos concentrados nas faixas de 70+ anos (esperado numa população envelhecendo); homens são maioria dos óbitos (~55%) contra ~45% de mulheres. Ambos os recortes são bons filtros/segmentações para o dashboard.
5. **Regiões/UFs:** Sudeste e São Paulo lideram em volume absoluto de óbitos, mas isso reflete principalmente o tamanho da população de cada UF/região, não necessariamente maior risco de morte.

### Limitações e pontos de atenção identificados
- **Sem dado de população:** a base não permite calcular taxa de mortalidade (óbitos por 100 mil habitantes) — as comparações regionais feitas aqui são só em volume absoluto. Sugestão para uma próxima iteração: cruzar com dado populacional do IBGE (por UF/ano) para permitir comparação justa entre regiões.
- **2025 e 2026 são dados preliminares/prévia**, sujeitos a revisão pelo DATASUS (já documentado pelo P2 no dicionário de dados) — reforçado aqui porque afeta diretamente a leitura visual da série temporal no dashboard.
- **Granularidade anual:** impede qualquer análise de sazonalidade dentro do ano.
- Cap XIX (lesões/envenenamento) só aparece em 2023 e Cap XXII (códigos especiais, ex. COVID-19) só em 2026 nesta série — confirmado como ausência real de ocorrência nesse recorte, não erro de dado (já validado pelo P2).

### Hipóteses para o P4 aprofundar no dashboard
- Comparar a evolução do Cap IX (circulatório) e Cap II (neoplasias) ao longo dos anos — ambos crescem em termos absolutos junto com a população, vale conferir se crescem mais rápido que o total geral.
- Explorar o cruzamento causa (CID-10) × faixa etária, que a EDA não aprofundou (ficou em análises univariadas por dimensão).
- Considerar um filtro/toggle no dashboard para excluir 2025/2026 das visualizações de tendência, evitando leitura equivocada do dado ainda incompleto.

---

## 5. P4 — Power BI / Dashboard

**Responsável:** Abner
**Status:** não iniciado.

O modelo de dados já está pronto para consumo direto (ver seção P2 — Entregável final). Sugestão de relacionamento no Power BI: `fato_obitos` como tabela-fato central, demais tabelas de detalhe relacionadas por `(ano, uf, sigla)`.

**[Espaço para o P4 preencher: link do dashboard, principais indicadores construídos, decisões de visualização.]**

---

## 6. Próximos passos do grupo

1. P1 confirmar o método real de extração (TabNet manual vs. PySUS) e resolver as 4 pendências de duplicados/classificação (seção 2) nas categorias afetadas.
2. Replicar a pipeline de limpeza (P2) para as 6 categorias já disponíveis no repositório.
3. P3 iniciar a EDA sobre a base de Mortalidade Geral já disponível.
4. P4 iniciar a modelagem do dashboard com o que já está pronto.

---

## 7. Status do projeto

| Frente | Status |
|---|---|
| P1 — Extração de Dados | ✅ Extração das 7 categorias concluída; 4 pendências de qualidade a resolver (3 duplicados + 1 arquivo mal classificado) |
| P2 — Limpeza e Tratamento de Dados | Concluído para Mortalidade Geral (Etapas 3 a 7 do cronograma); pendente replicar para as 6 categorias já disponíveis |
| P3 — Análise Exploratória (EDA) | ✅ Concluído para Mortalidade Geral (ver seção 4) |
| P4 — Power BI / Dashboard | Não iniciado (dashboard exploratório em Streamlit já publicado como entrega intermediária) |
| P5 — Documentação | Em andamento — este relatório e o dicionário de dados são atualizados incrementalmente |

> **Nota:** este relatório técnico e o README do repositório são documentos vivos. Ambos devem ser atualizados à medida que o projeto avança — especialmente após a extração das demais categorias do SIM e a entrada das etapas de EDA e dashboard.