"""
Padronização de categorias — categoria Mortalidade Geral (DATASUS/SIM).

Etapa 5 do cronograma P2: padronizar categorias.

Duas frentes:
1. Região/UF: a coluna bruta mistura região e estado na mesma coluna,
   com estados prefixados por ".." (ex: ".. Rondônia") e a linha "Total"
   misturada no meio dos dados. Aqui isso é separado em colunas
   explícitas (nivel, uf, sigla, regiao), prontas para uso em BI/Power BI
   sem exigir tratamento de texto do lado do analista.
2. Capítulo CID-10: os códigos brutos ("Cap I", "Cap II"...) são
   traduzidos para descrição legível, usando o documento de referência
   oficial (Capítulos da CID-10, OMS), e a tabela é transformada de
   formato largo (uma coluna por capítulo) para formato longo/tidy
   (uma linha por combinação ano/UF/capítulo), o formato que o Power BI
   e a maioria das ferramentas de BI esperam para montar visualizações.
"""
from pathlib import Path

import pandas as pd

# --- Referência oficial: 22 capítulos da CID-10 (OMS) ---
# Fonte: docs/referencia/capitulos_cid-10.pdf
CID10_CAPITULOS = {
    "Cap I": ("A00–B99", "Algumas doenças infecciosas e parasitárias"),
    "Cap II": ("C00–D48", "Neoplasias (tumores e cânceres)"),
    "Cap III": ("D50–D89", "Doenças do sangue e dos órgãos hematopoéticos e transtornos imunitários"),
    "Cap IV": ("E00–E90", "Doenças endócrinas, nutricionais e metabólicas (ex: Diabetes)"),
    "Cap V": ("F00–F99", "Transtornos mentais e de comportamento"),
    "Cap VI": ("G00–G99", "Doenças do sistema nervoso"),
    "Cap VII": ("H00–H59", "Doenças do olho e anexos"),
    "Cap VIII": ("H60–H95", "Doenças do ouvido e da apófise mastóide"),
    "Cap IX": ("I00–I99", "Doenças do aparelho circulatório (ex: Infarto, Hipertensão)"),
    "Cap X": ("J00–J99", "Doenças do aparelho respiratório (ex: Pneumonia, Asma)"),
    "Cap XI": ("K00–K93", "Doenças do aparelho digestivo"),
    "Cap XII": ("L00–L99", "Doenças da pele e do tecido subcutâneo"),
    "Cap XIII": ("M00–M99", "Doenças do sistema osteomuscular e do tecido conjuntivo"),
    "Cap XIV": ("N00–N99", "Doenças do aparelho geniturinário"),
    "Cap XV": ("O00–O99", "Gravidez, parto e puerpério"),
    "Cap XVI": ("P00–P96", "Algumas afecções originadas no período perinatal"),
    "Cap XVII": ("Q00–Q99", "Malformações congênitas, deformidades e anomalias cromossômicas"),
    "Cap XVIII": ("R00–R99", "Sintomas, sinais e achados anormais de exames clínicos e laboratoriais"),
    "Cap XIX": ("S00–T98", "Lesões, envenenamento e outras consequências de causas externas"),
    "Cap XX": ("V01–Y98", "Causas externas de morbidade e mortalidade (ex: acidentes, violência)"),
    "Cap XXI": ("Z00–Z99", "Fatores que influenciam o estado de saúde e o contato com serviços de saúde"),
    "Cap XXII": ("U00–U99", "Códigos para fins especiais (ex: novos vírus como a COVID-19)"),
}

# --- Referência: Região de cada UF (para padronizar Região/UF) ---
UF_PARA_REGIAO = {
    "Rondônia": "Região Norte", "Acre": "Região Norte", "Amazonas": "Região Norte",
    "Roraima": "Região Norte", "Pará": "Região Norte", "Amapá": "Região Norte",
    "Tocantins": "Região Norte",
    "Maranhão": "Região Nordeste", "Piauí": "Região Nordeste", "Ceará": "Região Nordeste",
    "Rio Grande do Norte": "Região Nordeste", "Paraíba": "Região Nordeste",
    "Pernambuco": "Região Nordeste", "Alagoas": "Região Nordeste", "Sergipe": "Região Nordeste",
    "Bahia": "Região Nordeste",
    "Minas Gerais": "Região Sudeste", "Espírito Santo": "Região Sudeste",
    "Rio de Janeiro": "Região Sudeste", "São Paulo": "Região Sudeste",
    "Paraná": "Região Sul", "Santa Catarina": "Região Sul", "Rio Grande do Sul": "Região Sul",
    "Mato Grosso do Sul": "Região Centro-Oeste", "Mato Grosso": "Região Centro-Oeste",
    "Goiás": "Região Centro-Oeste", "Distrito Federal": "Região Centro-Oeste",
}

UF_PARA_SIGLA = {
    "Rondônia": "RO", "Acre": "AC", "Amazonas": "AM", "Roraima": "RR", "Pará": "PA",
    "Amapá": "AP", "Tocantins": "TO", "Maranhão": "MA", "Piauí": "PI", "Ceará": "CE",
    "Rio Grande do Norte": "RN", "Paraíba": "PB", "Pernambuco": "PE", "Alagoas": "AL",
    "Sergipe": "SE", "Bahia": "BA", "Minas Gerais": "MG", "Espírito Santo": "ES",
    "Rio de Janeiro": "RJ", "São Paulo": "SP", "Paraná": "PR", "Santa Catarina": "SC",
    "Rio Grande do Sul": "RS", "Mato Grosso do Sul": "MS", "Mato Grosso": "MT",
    "Goiás": "GO", "Distrito Federal": "DF",
}

COL_REGIAO = "Região/Unidade da Federação"


def gerar_tabela_referencia_cid10() -> pd.DataFrame:
    """Retorna a tabela de referência dos 22 capítulos da CID-10, como DataFrame."""
    linhas = [
        {"capitulo": cod, "intervalo_codigos": intervalo, "descricao": desc}
        for cod, (intervalo, desc) in CID10_CAPITULOS.items()
    ]
    return pd.DataFrame(linhas)


def padronizar_regiao_uf(df: pd.DataFrame) -> pd.DataFrame:
    """Separa a coluna Região/UF em colunas explícitas: nivel, uf, sigla, regiao.

    - Remove a linha "Total" (fica implícita: é a soma de todos os registros
      de nivel="Estado" para aquele ano/dimensão — recalculável a qualquer
      momento, não precisa ser armazenada).
    - nivel: "Estado" ou "Regiao".
    - Para linhas de nivel="Regiao", uf e sigla ficam vazios (não se aplicam).
    """
    df = df.copy()
    df = df[df[COL_REGIAO] != "Total"].copy()

    def classificar(valor: str) -> str:
        return "Regiao" if valor.startswith("Região") else "Estado"

    df["nivel"] = df[COL_REGIAO].apply(classificar)
    df["uf"] = df[COL_REGIAO].where(df["nivel"] == "Estado", "").str.replace(
        r"^\.\.\s*", "", regex=True
    )
    df["uf"] = df["uf"].where(df["nivel"] == "Estado", None)
    df["sigla"] = df["uf"].map(UF_PARA_SIGLA)
    df["regiao"] = df.apply(
        lambda r: r[COL_REGIAO] if r["nivel"] == "Regiao" else UF_PARA_REGIAO.get(r["uf"]),
        axis=1,
    )

    df = df.drop(columns=[COL_REGIAO])
    colunas_ordem = ["ano", "dimensao", "nivel", "regiao", "uf", "sigla"] + [
        c for c in df.columns if c not in ("ano", "dimensao", "nivel", "regiao", "uf", "sigla")
    ]
    return df[colunas_ordem]


def transformar_cid10_para_formato_longo(df_capitulo_cid10: pd.DataFrame) -> pd.DataFrame:
    """Converte a tabela de capitulo_cid10 (uma coluna por capítulo) para
    formato longo/tidy: uma linha por (ano, UF/Região, capítulo), já com
    a descrição do capítulo — pronto para Power BI.
    """
    colunas_id = ["ano", "dimensao", "nivel", "regiao", "uf", "sigla"]
    colunas_capitulo = [c for c in df_capitulo_cid10.columns if c.startswith("Cap")]

    df_longo = df_capitulo_cid10.melt(
        id_vars=colunas_id,
        value_vars=colunas_capitulo,
        var_name="capitulo",
        value_name="obitos",
    )

    ref = gerar_tabela_referencia_cid10()
    df_longo = df_longo.merge(ref, on="capitulo", how="left")

    return df_longo.drop(columns=["dimensao"])


if __name__ == "__main__":
    pasta_entrada = Path("data/processed/mortalidade_geral")
    pasta_saida = Path("data/processed/mortalidade_geral")

    # --- Referência CID-10, salva à parte para reuso por outras categorias ---
    ref_cid10 = gerar_tabela_referencia_cid10()
    ref_cid10.to_csv(pasta_saida / "referencia_cid10.csv", index=False, encoding="utf-8")
    print(f"Referência CID-10 salva: {len(ref_cid10)} capítulos -> referencia_cid10.csv")

    # --- Padroniza Região/UF nas 4 dimensões ---
    for nome_arquivo in ["capitulo_cid10", "faixa_etaria", "sexo", "local_ocorrencia"]:
        df = pd.read_csv(pasta_entrada / f"{nome_arquivo}.csv")
        df_padronizado = padronizar_regiao_uf(df)
        df_padronizado.to_csv(pasta_saida / f"{nome_arquivo}.csv", index=False, encoding="utf-8")
        print(f"{nome_arquivo}: {df_padronizado.shape[0]} linhas padronizadas (Total removido, Região/UF separados)")

    # --- Formato longo/tidy só para capitulo_cid10, com descrição ---
    df_cid10 = pd.read_csv(pasta_entrada / "capitulo_cid10.csv")
    df_cid10["dimensao"] = "capitulo_cid10"  # necessário pro melt, foi removido acima
    df_longo = transformar_cid10_para_formato_longo(df_cid10)
    df_longo.to_csv(pasta_saida / "capitulo_cid10_long.csv", index=False, encoding="utf-8")
    print(f"capitulo_cid10_long: {df_longo.shape[0]} linhas (formato tidy, pronto para Power BI)")

    print("\nPadronização concluída.")