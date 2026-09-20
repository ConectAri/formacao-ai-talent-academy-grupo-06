"""
Consolidação da base — categoria Mortalidade Geral (DATASUS/SIM).

Etapa 6 do cronograma P2: consolidação da base.

Gera a tabela-fato única (fato_obitos.csv): uma linha por (ano, UF/Região),
com o total de óbitos — a âncora do modelo em estrela para o Power BI.
As 4 tabelas de detalhe (capitulo_cid10, faixa_etaria, sexo, local_ocorrencia)
seguem existindo como tabelas de "quebra" por dimensão, todas relacionáveis
a fato_obitos por (ano, uf, sigla).

Validação embutida: antes de consolidar, confirma que a coluna "Total" bate
entre as 4 dimensões para cada (ano, UF/Região) — se não bater, o script para
com erro, porque significaria que as dimensões descrevem populações diferentes.
"""
from pathlib import Path

import pandas as pd

DIMENSOES = ["capitulo_cid10", "faixa_etaria", "sexo", "local_ocorrencia"]
CHAVES = ["ano", "nivel", "regiao", "uf", "sigla"]


def validar_totais_entre_dimensoes(tabelas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Confere se a coluna Total é idêntica entre as 4 dimensões, para cada
    combinação de chave (ano, nivel, regiao, uf, sigla). Levanta erro se não bater.
    Retorna a base combinada com um único total_obitos por linha.
    """
    base = tabelas[DIMENSOES[0]][CHAVES + ["Total"]].rename(columns={"Total": f"total_{DIMENSOES[0]}"})

    for dim in DIMENSOES[1:]:
        outra = tabelas[dim][CHAVES + ["Total"]].rename(columns={"Total": f"total_{dim}"})
        base = base.merge(outra, on=CHAVES, how="outer")

    colunas_total = [c for c in base.columns if c.startswith("total_")]
    if base[colunas_total].isna().any().any():
        raise ValueError("Combinação (ano, UF/Região) presente em uma dimensão e ausente em outra.")

    divergentes = base[colunas_total].nunique(axis=1) != 1
    if divergentes.any():
        exemplos = base[divergentes].head(5)
        raise ValueError(
            f"Totais divergem entre dimensões em {divergentes.sum()} linha(s). Exemplos:\n{exemplos}"
        )

    base["total_obitos"] = base[colunas_total[0]]
    return base[CHAVES + ["total_obitos"]]


def consolidar_categoria_mortalidade_geral(pasta: Path) -> pd.DataFrame:
    """Lê as 4 tabelas de detalhe já padronizadas (Etapa 5), valida consistência
    cruzada e retorna a tabela-fato única (fato_obitos)."""
    tabelas = {dim: pd.read_csv(pasta / f"{dim}.csv") for dim in DIMENSOES}
    return validar_totais_entre_dimensoes(tabelas)


if __name__ == "__main__":
    pasta = Path("data/processed/mortalidade_geral")

    fato_obitos = consolidar_categoria_mortalidade_geral(pasta)
    fato_obitos.to_csv(pasta / "fato_obitos.csv", index=False, encoding="utf-8")

    print(f"fato_obitos.csv gerado: {fato_obitos.shape[0]} linhas")
    print("Validação: Total idêntico entre as 4 dimensões em 100% das combinações (ano, UF/Região).")
    print()
    print("Modelo em estrela pronto para Power BI:")
    print("  fato_obitos.csv           <- tabela-fato (ano, uf, sigla, total_obitos)")
    for dim in DIMENSOES:
        print(f"  {dim}.csv".ljust(28) + "<- tabela de detalhe, relacionável por (ano, uf, sigla)")
    print("  referencia_cid10.csv      <- dimensão auxiliar (descrição dos capítulos)")