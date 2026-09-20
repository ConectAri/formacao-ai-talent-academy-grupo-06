"""
Validação final + entrega — categoria Mortalidade Geral (DATASUS/SIM).

Etapa 7 do cronograma P2 (última etapa da limpeza): roda a pipeline
completa do zero (Etapas 4, 5 e 6) e confere, ao final, os critérios de
qualidade que o grupo definiu ao longo do processo. Serve como o
"checklist automático" antes de entregar a base tratada.

Uso: python src/cleaning/validacao_final.py
Sai com código de erro != 0 se qualquer checagem falhar.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cleaning.limpeza_mortalidade_geral import limpar_categoria_mortalidade_geral
from src.cleaning.padronizacao_categorias import (
    gerar_tabela_referencia_cid10,
    padronizar_regiao_uf,
    transformar_cid10_para_formato_longo,
)
from src.cleaning.consolidacao_base import consolidar_categoria_mortalidade_geral

PASTA_RAW = Path("data/raw/datasus_sim/mortalidade_geral")
PASTA_PROCESSED = Path("data/processed/mortalidade_geral")
DIMENSOES = ["capitulo_cid10", "faixa_etaria", "sexo", "local_ocorrencia"]

checagens: list[tuple[str, bool, str]] = []


def checar(nome: str, condicao: bool, detalhe: str = ""):
    checagens.append((nome, condicao, detalhe))
    marca = "OK" if condicao else "FALHOU"
    print(f"[{marca}] {nome}" + (f" — {detalhe}" if detalhe else ""))


if __name__ == "__main__":
    print("=== Rodando pipeline completa (Etapas 4 -> 5 -> 6) ===\n")

    # --- Etapa 4: limpeza + tratamento de nulos ---
    resultado_limpeza = limpar_categoria_mortalidade_geral(PASTA_RAW)
    checar(
        "Etapa 4 — todas as 4 dimensões principais foram lidas",
        set(resultado_limpeza.keys()) == set(DIMENSOES),
        f"encontradas: {sorted(resultado_limpeza.keys())}",
    )
    for dim, df in resultado_limpeza.items():
        checar(f"Etapa 4 — {dim}: zero valores nulos", df.isna().sum().sum() == 0)

    PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)
    for dim, df in resultado_limpeza.items():
        df.to_csv(PASTA_PROCESSED / f"{dim}.csv", index=False, encoding="utf-8")

    # --- Etapa 5: padronização ---
    ref_cid10 = gerar_tabela_referencia_cid10()
    checar("Etapa 5 — referência CID-10 tem 22 capítulos", len(ref_cid10) == 22)

    tabelas_padronizadas = {}
    for dim in DIMENSOES:
        df = pd.read_csv(PASTA_PROCESSED / f"{dim}.csv")
        df_pad = padronizar_regiao_uf(df)
        checar(f"Etapa 5 — {dim}: linha 'Total' removida", "Total" not in df_pad.get("uf", pd.Series(dtype=str)).values)
        checar(f"Etapa 5 — {dim}: sem sigla nula em nivel=Estado", df_pad[df_pad["nivel"] == "Estado"]["sigla"].isna().sum() == 0)
        df_pad.to_csv(PASTA_PROCESSED / f"{dim}.csv", index=False, encoding="utf-8")
        tabelas_padronizadas[dim] = df_pad

    df_cid10 = pd.read_csv(PASTA_PROCESSED / "capitulo_cid10.csv")
    df_cid10["dimensao"] = "capitulo_cid10"
    df_longo = transformar_cid10_para_formato_longo(df_cid10)
    df_longo.to_csv(PASTA_PROCESSED / "capitulo_cid10_long.csv", index=False, encoding="utf-8")
    checar("Etapa 5 — capitulo_cid10_long sem descrição nula", df_longo["descricao"].isna().sum() == 0)
    ref_cid10.to_csv(PASTA_PROCESSED / "referencia_cid10.csv", index=False, encoding="utf-8")

    # --- Etapa 6: consolidação ---
    fato_obitos = consolidar_categoria_mortalidade_geral(PASTA_PROCESSED)
    fato_obitos.to_csv(PASTA_PROCESSED / "fato_obitos.csv", index=False, encoding="utf-8")
    checar("Etapa 6 — fato_obitos: 352 linhas (32 UFs/Regiões x 11 anos)", len(fato_obitos) == 352)

    # --- Checagens finais de entrega ---
    total_2020 = fato_obitos[(fato_obitos["ano"] == 2020) & (fato_obitos["nivel"] == "Estado")]["total_obitos"].sum()
    checar(
        "Entrega — série histórica preserva o pico da pandemia (2020 > 2019)",
        total_2020 > fato_obitos[(fato_obitos["ano"] == 2019) & (fato_obitos["nivel"] == "Estado")]["total_obitos"].sum(),
    )

    arquivos_esperados = [
        "capitulo_cid10.csv", "faixa_etaria.csv", "sexo.csv", "local_ocorrencia.csv",
        "capitulo_cid10_long.csv", "referencia_cid10.csv", "fato_obitos.csv",
    ]
    for nome in arquivos_esperados:
        checar(f"Entrega — arquivo final existe: {nome}", (PASTA_PROCESSED / nome).exists())

    # --- Resumo ---
    print("\n=== Resumo ===")
    total = len(checagens)
    passou = sum(1 for _, ok, _ in checagens if ok)
    print(f"{passou}/{total} checagens passaram.")

    if passou != total:
        print("\nFALHAS:")
        for nome, ok, detalhe in checagens:
            if not ok:
                print(f"  - {nome}: {detalhe}")
        sys.exit(1)

    print("\n✅ Base de Mortalidade Geral validada e pronta para entrega ao grupo.")