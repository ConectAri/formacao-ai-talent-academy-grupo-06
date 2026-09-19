"""
Leitura padronizada de arquivos exportados do TabNet/DATASUS (SIM).

Cada arquivo segue o padrão:
    linha 0: título
    linha 1: subtítulo (indica a dimensão cruzada com Região/UF)
    linha 2: "Período:AAAA"
    linha 3: cabeçalho das colunas
    linhas 4..N: dados (Região > Estados indentados, + linha "Total")
    linhas seguintes: rodapé (Fonte/Notas) — descartado
"""
import pandas as pd
import re

# Mapeia o SUFIXO do subtítulo (após "...Região/Unidade da Federação e ") para
# um nome de dimensão padronizado. Todos os subtítulos seguem o padrão
# "Óbitos p/Residênc por Região/Unidade da Federação e <Dimensão>", então
# não dá pra usar "Região" como palavra-chave livre (aparece em TODOS eles).
DIMENSOES = {
    "Capítulo CID-10": "capitulo_cid10",
    "Faixa Etária": "faixa_etaria",
    "Local ocorrência": "local_ocorrencia",
    "Sexo": "sexo",
    "Região": "regiao_x_regiao",  # caso atípico de 2016
}

def identificar_dimensao(subtitulo: str) -> str:
    """Identifica a dimensão a partir do SUFIXO do subtítulo (depois de ' e ')."""
    sufixo = subtitulo.rsplit(" e ", maxsplit=1)[-1].strip()
    return DIMENSOES.get(sufixo, "desconhecida")

def ler_arquivo_tabnet(caminho: str) -> pd.DataFrame:
    """Lê um arquivo CSV do TabNet/SIM e retorna um DataFrame tratado (leitura crua,
    sem tratamento de nulos/categorias — isso é etapa posterior)."""

    with open(caminho, encoding="latin1") as f:
        linhas = f.readlines()

    titulo = linhas[0].strip().strip('"')
    subtitulo = linhas[1].strip().strip('"')
    periodo_raw = linhas[2].strip()
    ano = int(re.search(r"\d{4}", periodo_raw).group())
    dimensao = identificar_dimensao(subtitulo)

    # Localiza a linha "Total" (fim da tabela de dados) para saber onde cortar o rodapé
    linha_total_idx = next(
        i for i, l in enumerate(linhas) if l.strip().startswith('"Total"')
    )

    # Lê apenas o bloco de dados: cabeçalho (linha 3) até a linha "Total" (inclusive)
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        skiprows=3,
        nrows=(linha_total_idx - 3),
        na_values=["-"],   # converte "-" em NaN nesta leitura crua
    )

    df.insert(0, "ano", ano)
    df.insert(1, "dimensao", dimensao)

    return df, titulo, subtitulo

if __name__ == "__main__":
    import glob
    from pathlib import Path

    # Caminho relativo à raiz do projeto (rode com: python src/io/leitura_tabnet.py)
    pasta = Path(__file__).resolve().parents[2] / "data" / "raw" / "datasus_sim" / "mortalidade_geral"
    arquivos = sorted(glob.glob(str(pasta / "*.csv")))
    print(f"Testando em {len(arquivos)} arquivos...\n")

    resumo = []
    erros = []
    for caminho in arquivos:
        try:
            df, titulo, subtitulo = ler_arquivo_tabnet(caminho)
            resumo.append((caminho.split("/")[-1], df["ano"].iloc[0], df["dimensao"].iloc[0], df.shape))
        except Exception as e:
            erros.append((caminho.split("/")[-1], str(e)))

    print("--- Amostra de resultados (10 primeiros) ---")
    for r in resumo[:10]:
        print(r)

    print(f"\nTotal lidos com sucesso: {len(resumo)}")
    print(f"Total com erro: {len(erros)}")
    for e in erros:
        print("  ERRO:", e)

    # conferir se todas as dimensões foram identificadas corretamente
    from collections import Counter
    dims = Counter(r[2] for r in resumo)
    print("\n--- Distribuição de dimensões identificadas ---")
    for d, c in dims.items():
        print(f"  {d}: {c}")