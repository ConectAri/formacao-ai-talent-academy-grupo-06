# Dicionário de Dados — Analytics em Saúde Pública: Mortalidade no Brasil (DATASUS/SIM)

Documento mantido pelo P2 (Limpeza e Tratamento de Dados) e P5 (Documentação).
Atualizado incrementalmente conforme cada categoria do SIM é processada.

## Categoria: Mortalidade Geral (piloto)

**Fonte:** DATASUS/SIM, extraído via TabNet.
**Arquivos brutos:** `data/raw/datasus_sim/mortalidade_geral/` (45 CSVs).
**Período:** 2016–2026 (2025 = dado preliminar; 2026 = 1ª prévia, ambos sujeitos a revisão pelo DATASUS).

### Estrutura dos arquivos brutos
- Encoding: ISO-8859-1 (latin1); separador: `;`.
- 3 linhas de metadado (título, subtítulo, período) antes do cabeçalho de dados.
- Linha "Total" encerra o bloco de dados; linhas seguintes são rodapé (fonte/notas), descartado na leitura.
- Caractere `"-"` representa zero ou valor suprimido por sigilo estatístico — convertido para `NaN` na leitura crua (`src/io/leitura_tabnet.py`).

### Dimensões disponíveis (4 por ano, 2017–2026)
| Dimensão | Coluna identificadora | Conteúdo |
|---|---|---|
| `capitulo_cid10` | Cap I – Cap XX | Óbitos por capítulo da CID-10 (causa básica) |
| `faixa_etaria` | Menor 1 ano – 80 anos e mais | Óbitos por faixa etária |
| `sexo` | Masc / Fem / Ign | Óbitos por sexo |
| `local_ocorrencia` | Hospital / Domicílio / Via pública / Outros | Óbitos por local de ocorrência |

**Nota sobre capítulos CID-10 ausentes:** as colunas não incluem Cap XIX, XXI e XXII. Não é erro de extração — o SIM não usa esses capítulos como causa básica de óbito nesta tabulação (XIX é coberto por XX; XXI e XXII são códigos administrativos/especiais).

### Registro atípico: Região × Região (2016)
Um arquivo do ano de 2016 (`sim_cnv_obt10uf185444138_0_146_204.csv`) cruza Região de residência × Região de ocorrência, fora do padrão das outras 4 dimensões — e existe **somente para 2016**, sem equivalente nos demais anos.

**Decisão do grupo (P2, validada em 20/09/2026): tratar como dataset complementar/exploratório.**
- Não entra na base consolidada principal (`data/processed/mortalidade_geral/`).
- Não é comparável entre períodos (dado de ano único).
- Preservado em `data/raw/` para uso exploratório futuro (ex.: mobilidade de óbitos entre regiões).
- Já isolado automaticamente pelo código: `leitura_tabnet.py` o identifica como `dimensao="regiao_x_regiao"`, e `app.py` o exclui da lista de dimensões do dashboard principal.

### Duplicidade
Verificação por hash MD5 nos 45 arquivos: **nenhuma duplicata exata encontrada** nesta categoria (checado em 20/09/2026).

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