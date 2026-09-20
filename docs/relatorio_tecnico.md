# Relatório Técnico — Analytics em Saúde Pública: Mortalidade no Brasil (DATASUS/SIM)

**Projeto Final — AI Talent Academy (White Cube), Grupo 6**
**Trilha:** Analytics
**Última atualização:** 20/09/2026, por Ariane (P5 — Documentação)

> Este documento é colaborativo. Cada seção pertence a um papel do grupo (P1 a P4) e deve ser atualizada pela pessoa responsável conforme sua etapa avança. P5 consolida e mantém a coerência geral.

---

## 1. Visão geral do projeto

O grupo desenvolve um projeto de Analytics sobre **mortalidade no Brasil**, usando dados públicos do **DATASUS/SIM (Sistema de Informações sobre Mortalidade)**, cobrindo o período de **2016 a 2026** (2025 preliminar, 2026 em 1ª prévia).

**Nota de escopo:** o projeto pivotou da proposta original registrada no Forms 01 (internações hospitalares via SIH/SUS) para mortalidade (SIM), já que o material de trabalho do grupo — os 7 relatórios estruturais e os dados brutos — é de mortalidade. Essa mudança foi validada com a equipe em 20/09/2026.

O SIM está organizado em 7 categorias temáticas. Até o momento, **apenas Mortalidade Geral** (categoria piloto) foi processada de ponta a ponta e está disponível no repositório:

| Categoria | Status |
|---|---|
| Mortalidade Geral | ✅ Extraída, limpa, padronizada e consolidada |
| Óbitos Infantis | ⏳ Extraída (zip original), não enviada ao repositório |
| Óbitos Fetais | ⏳ Extraída (zip original), não enviada ao repositório |
| Óbitos por Causas Externas | ⏳ Extraída (zip original), não enviada ao repositório |
| Óbitos de Mulheres em Idade Fértil e Maternos | ⏳ Extraída (zip original), não enviada ao repositório |
| Causas Evitáveis | ⏳ Extraída (zip original), não enviada ao repositório |
| Mortalidade de Residentes no Exterior | ⏳ Extraída (zip original), não enviada ao repositório |

---

## 2. P1 — Extração de Dados

**Responsável:** Roboaldo
**Status:** parcialmente documentado — seção a ser complementada pelo responsável.

### O que está confirmado
- Fonte: TabNet/DATASUS, sistema SIM.
- Formato de extração observado nos arquivos: **exportação manual via interface web do TabNet**, gerando CSVs no padrão `sim_cnv_<código>.csv` (encoding ISO-8859-1, separador `;`, com cabeçalho de metadados nas 3 primeiras linhas).
- Cada categoria foi extraída com 4 cortes/dimensões (Capítulo CID-10, Faixa Etária, Sexo, Local de Ocorrência) por ano, resultando em ~4 arquivos por ano por categoria (2016 tem um 5º arquivo atípico em Mortalidade Geral — ver seção P2).
- Período coberto: 2016–2026.

### ⚠️ Divergência a esclarecer com o P1
O plano registrado no Alinhamento do Grupo 6 previa extração via **PySUS** (biblioteca Python que acessa o FTP do DATASUS programaticamente). O padrão observado nos arquivos reais, no entanto, é de **exportação manual via TabNet** (não há rastro de uso do PySUS nos arquivos brutos). Isso não é um problema — o dado é válido de qualquer forma — mas o P1 deveria confirmar e documentar qual método foi de fato usado, para o relatório final refletir a realidade.

### Pendências conhecidas (a validar pelo P1)
- 3 arquivos duplicados com sufixo `(1).csv`, no material original: em Causas Evitáveis, Óbitos Infantis e Óbitos por Causas Externas.
- 1 arquivo de Causas Externas classificado incorretamente dentro da pasta de Óbitos Fetais.

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
- As 6 categorias restantes ainda não foram enviadas ao repositório.
- Quando enviadas, aplicar a mesma pipeline (`limpeza` → `padronizacao` → `consolidacao` → `validacao`), adaptando os scripts para cada estrutura de dimensão específica (cada categoria tem variáveis próprias, além de Região/UF).
- Resolver, nessa hora, os 3 arquivos `(1).csv` duplicados e o arquivo mal classificado (Causas Externas dentro de Óbitos Fetais) sinalizados pelo P1.

---

## 4. P3 — Análise Exploratória (EDA)

**Responsável:** Levi Lima
**Status:** não iniciado.

**[Espaço para o P3 preencher: perguntas de negócio exploradas, principais achados, gráficos/estatísticas descritivas, hipóteses para o P4 aprofundar no dashboard.]**

---

## 5. P4 — Power BI / Dashboard

**Responsável:** Abner
**Status:** não iniciado.

O modelo de dados já está pronto para consumo direto (ver seção P2 — Entregável final). Sugestão de relacionamento no Power BI: `fato_obitos` como tabela-fato central, demais tabelas de detalhe relacionadas por `(ano, uf, sigla)`.

**[Espaço para o P4 preencher: link do dashboard, principais indicadores construídos, decisões de visualização.]**

---

## 6. Próximos passos do grupo

1. P1 confirmar o método real de extração e resolver as pendências de duplicados/classificação nas 6 categorias restantes.
2. Enviar as 6 categorias restantes ao repositório.
3. Replicar a pipeline de limpeza (P2) para cada uma.
4. P3 iniciar a EDA sobre a base de Mortalidade Geral já disponível.
5. P4 iniciar a modelagem do dashboard com o que já está pronto.