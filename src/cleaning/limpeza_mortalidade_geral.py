"""
Limpeza e tratamento de dados — categoria Mortalidade Geral (DATASUS/SIM).

Etapa 4 do cronograma P2: tratamento de valores nulos/ausentes.

Decisão (validada em 20/09/2026, com evidência estatística):
    O caractere "-" nos arquivos brutos representa ZERO real, não dado
    suprimido por sigilo estatístico. Validado comparando a soma das
    colunas de cada linha (tratando "-"/NaN como 0) contra a coluna
    "Total" em todas as 1.408 linhas de Região/UF das 4 dimensões
    principais (capitulo_cid10, faixa_etaria, sexo, local_ocorrencia):
    100% de correspondência exata, 0 divergências.

    Por isso, a conversão de NaN -> 0 é segura e não introduz perda
    de informação nem viés analítico.
"""
import glob
import sys
from pathlib import Path

import pandas as pd

# Garante que a raiz do projeto está no sys.path, para o import abaixo funcionar
# tanto rodando "python3 src/cleaning/limpeza_mortalidade_geral.py" quanto
# "python3 -m src.cleaning.limpeza_mortalidade_geral" a partir da raiz do projeto.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.io.leitura_tabnet import ler_arquivo_tabnet

COL_REGIAO = "Região/Unidade da Federação"


def limpar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o tratamento de nulos a um DataFrame já lido por ler_arquivo_tabnet.

    - Converte NaN (ex-"-") para 0 nas colunas numéricas de dado.
    - Não altera 'ano', 'dimensao' ou a coluna de Região/UF.
    """
    df = df.copy()
    colunas_numericas = [c for c in df.columns if c not in ("ano", "dimensao", COL_REGIAO)]
    df[colunas_numericas] = df[colunas_numericas].fillna(0).astype(int)
    return df


def validar_consistencia(df: pd.DataFrame) -> bool:
    """Confere se soma(colunas de dado) == Total, para cada linha exceto 'Total'."""
    colunas_dado = [c for c in df.columns if c not in ("ano", "dimensao", COL_REGIAO, "Total")]
    df_sem_total = df[df[COL_REGIAO] != "Total"]
    soma_calculada = df_sem_total[colunas_dado].sum(axis=1)
    return (soma_calculada == df_sem_total["Total"]).all()


def limpar_categoria_mortalidade_geral(
    pasta_entrada: Path, excluir_dimensao: str = "regiao_x_regiao"
) -> dict[str, pd.DataFrame]:
    """Lê, limpa e valida todos os arquivos de Mortalidade Geral, agrupando por dimensão.

    Retorna um dict {dimensao: DataFrame consolidado}, um DataFrame por dimensão
    com todos os anos empilhados. A dimensão atípica (região x região, 2016) é
    excluída por padrão — tratada como dataset complementar (decisão da Etapa 3).
    """
    arquivos = sorted(glob.glob(str(pasta_entrada / "*.csv")))
    por_dimensao: dict[str, list[pd.DataFrame]] = {}

    for caminho in arquivos:
        df, _, _ = ler_arquivo_tabnet(caminho)
        dimensao = df["dimensao"].iloc[0]
        if dimensao == excluir_dimensao:
            continue

        df_limpo = limpar_dataframe(df)

        if not validar_consistencia(df_limpo):
            raise ValueError(f"Inconsistência encontrada após limpeza: {caminho}")

        por_dimensao.setdefault(dimensao, []).append(df_limpo)

    resultado = {}
    for dim, dfs in por_dimensao.items():
        df_consolidado = pd.concat(dfs, ignore_index=True)
        # Anos que não tiveram nenhuma ocorrência em um capítulo/coluna específico
        # não trazem essa coluna no arquivo bruto daquele ano (ex.: Cap XIX só
        # aparece em 2023, Cap XXII só em 2026, em Mortalidade Geral). Ao
        # consolidar todos os anos, essas colunas ficam NaN para os anos sem
        # ocorrência — valor real é 0, mesma lógica já validada por arquivo.
        colunas_dado = [c for c in df_consolidado.columns if c not in ("ano", "dimensao", COL_REGIAO)]
        df_consolidado[colunas_dado] = df_consolidado[colunas_dado].fillna(0).astype(int)
        resultado[dim] = df_consolidado

    return resultado


if __name__ == "__main__":
    pasta_entrada = Path("data/raw/datasus_sim/mortalidade_geral")
    pasta_saida = Path("data/processed/mortalidade_geral")
    pasta_saida.mkdir(parents=True, exist_ok=True)

    resultado = limpar_categoria_mortalidade_geral(pasta_entrada)

    print(f"Dimensões processadas: {list(resultado.keys())}")
    for dimensao, df in resultado.items():
        caminho_saida = pasta_saida / f"{dimensao}.csv"
        df.to_csv(caminho_saida, index=False, encoding="utf-8")
        print(f"  {dimensao}: {df.shape[0]} linhas, {df.shape[1]} colunas -> {caminho_saida}")
        print(f"    Validação (soma == Total): OK para todas as linhas")

    print("\nLimpeza concluída sem inconsistências.")