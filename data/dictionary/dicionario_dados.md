# Dicionário de Dados — Analytics em Saúde Pública: Mortalidade no Brasil (DATASUS/SIM)

Documento mantido pelo P2 (Limpeza e Tratamento de Dados) e P5 (Documentação).
Atualizado incrementalmente conforme cada categoria do SIM é processada.

## Categoria: Mortalidade Geral (piloto)

**Fonte:** DATASUS/SIM, extraído via TabNet.
**Arquivos brutos:** `data/raw/datasus_sim/mortalidade_geral/` (45 CSVs).
**Base tratada:** `data/processed/mortalidade_geral/{capitulo_cid10, faixa_etaria, sexo, local_ocorrencia}.csv` (363 linhas cada = 33 regiões/UFs × 11 anos).
**Período:** 2016–2026 (2025 = dado preliminar; 2026 = 1ª prévia, ambos sujeitos a revisão pelo DATASUS).

### Estrutura dos arquivos brutos
- Encoding: ISO-8859-1 (latin1); separador: `;`.
- 3 linhas de metadado (título, subtítulo, período) antes do cabeçalho de dados.
- Linha "Total" encerra o bloco de dados; linhas seguintes são rodapé (fonte/notas), descartado na leitura.
- Caractere `"-"` representa zero — ver Etapa 4 abaixo.

### Dimensões disponíveis (4 por ano, 2016–2026)
| Dimensão | Coluna identificadora | Conteúdo |
|---|---|---|
| `capitulo_cid10` | Cap I – Cap XX (+ XIX/XXII em anos pontuais) | Óbitos por capítulo da CID-10 (causa básica) |
| `faixa_etaria` | Menor 1 ano – 80 anos e mais | Óbitos por faixa etária |
| `sexo` | Masc / Fem / Ign | Óbitos por sexo |
| `local_ocorrencia` | Hospital / Domicílio / Via pública / Outros | Óbitos por local de ocorrência |

**Nota sobre capítulos CID-10 (corrigida na Etapa 4):** o TabNet omite, por ano, qualquer coluna de capítulo cuja soma seja zero em todas as UFs naquele ano — não é ausência permanente do capítulo na classificação. Constatado que:
- **Cap XXI** nunca teve ocorrência em nenhum dos 11 anos (2016–2026) — genuinamente sem uso nesta série.
- **Cap XIX** apareceu apenas em **2023** (0 nos demais 10 anos).
- **Cap XXII** apareceu apenas em **2026** (0 nos demais 10 anos).
- Ao consolidar todos os anos, essas colunas recebem `0` para os anos sem ocorrência (mesma regra da Etapa 4).

### Registro atípico: Região × Região (2016)
Um arquivo do ano de 2016 (`sim_cnv_obt10uf185444138_0_146_204.csv`) cruza Região de residência × Região de ocorrência, fora do padrão das outras 4 dimensões — e existe **somente para 2016**, sem equivalente nos demais anos.

**Decisão do grupo (P2, validada em 20/09/2026): tratar como dataset complementar/exploratório.**
- Não entra na base consolidada principal (`data/processed/mortalidade_geral/`).
- Não é comparável entre períodos (dado de ano único).
- Preservado em `data/raw/` para uso exploratório futuro (ex.: mobilidade de óbitos entre regiões).
- Já isolado automaticamente pelo código: `leitura_tabnet.py` o identifica como `dimensao="regiao_x_regiao"`, e `app.py` o exclui da lista de dimensões do dashboard principal.

### Duplicidade (Etapa 3)
Verificação por hash MD5 nos 45 arquivos: **nenhuma duplicata exata encontrada** nesta categoria.

### Tratamento de nulos (Etapa 4)
O caractere `"-"` (e colunas ausentes por ano, ver acima) representa **zero real**, não dado suprimido por sigilo estatístico.

**Evidência:** validado comparando a soma das colunas de cada linha (tratando `"-"`/`NaN` como `0`) contra a coluna "Total", em **1.408 linhas** de Região/UF nas 4 dimensões principais — **100% de correspondência exata, 0 divergências**.

**Regra aplicada:** `NaN → 0` (script: `src/cleaning/limpeza_mortalidade_geral.py`). Resultado final: **0 valores nulos** na base tratada, com validação automática (`soma(colunas) == Total`) embutida no script — o script lança erro se qualquer linha divergir.

---

## Categorias pendentes (ainda não enviadas ao repositório)
As 6 categorias abaixo existem no dataset original do DATASUS/SIM, mas seus CSVs **ainda não foram enviados ao GitHub** — apenas Mortalidade Geral está disponível no repositório até o momento:
- Óbitos Infantis
- Óbitos Fetais
- Óbitos por Causas Externas
- Óbitos de Mulheres em Idade Fértil e Óbitos Maternos
- Causas Evitáveis
- Mortalidade de Residentes no Exterior

**Pendências já identificadas no material original (zip), a resolver quando essas categorias forem enviadas e processadas:**
- 3 arquivos duplicados com sufixo `(1).csv` — em Causas Evitáveis, Óbitos Infantis e Óbitos por Causas Externas.
- 1 arquivo de Causas Externas classificado incorretamente dentro da pasta de Óbitos Fetais.
- Verificar, para cada categoria, se o mesmo padrão de colunas de capítulo CID-10 "aparecem só em anos com ocorrência" se repete (provável, dado o comportamento do TabNet).

### Padronização de categorias (Etapa 5)
Script: `src/cleaning/padronizacao_categorias.py`. **Depende da Etapa 4 já ter rodado** (recria os arquivos processados a partir dos brutos, depois padroniza por cima — rodar limpeza antes, sempre).

**Região/UF → 4 colunas explícitas:**
| Coluna nova | Conteúdo |
|---|---|
| `nivel` | `"Regiao"` ou `"Estado"` |
| `regiao` | Nome da região (preenchido em ambos os níveis) |
| `uf` | Nome do estado, sem o prefixo `".. "` (vazio para linhas de região) |
| `sigla` | Sigla de 2 letras do estado (ex: `SP`, `RJ`) — vazio para linhas de região |

A linha "Total" (Brasil) foi **removida** — é recalculável a qualquer momento somando todos os registros de `nivel="Estado"`, não precisa ser armazenada.

**CID-10 → descrição:** tabela de referência oficial (22 capítulos, OMS) salva em `data/processed/mortalidade_geral/referencia_cid10.csv` (colunas: `capitulo`, `intervalo_codigos`, `descricao`), reaproveitável pelas outras 6 categorias.

**Formato longo/tidy:** `capitulo_cid10_long.csv` (7.392 linhas) — uma linha por combinação (ano, UF/Região, capítulo), já com a descrição do capítulo. Este é o formato recomendado para o P4 consumir no Power BI (dimensões `faixa_etaria`, `sexo`, `local_ocorrencia` continuam em formato largo, pois já têm poucas colunas e nomes autoexplicativos — não precisam de melt).