"""Mide la cobertura del enlace por CUI entre SSI (Invierte.pe), SEACE e INFOBRAS.

Uso:
    python src/etl/01_check_linkage.py --ssi data/raw/ssi.csv \
        --seace data/raw/seace_contratos.csv --infobras data/raw/infobras.csv \
        --ssi-col CODIGO_UNICO --seace-col CUI --infobras-col CUI

Los nombres de columna cambian entre versiones de los portales: revisa el
diccionario de datos de cada fuente y ajusta los argumentos *-col.
"""
import argparse

import pandas as pd


def load_keys(path: str, col: str) -> set[str]:
    df = pd.read_csv(path, usecols=[col], dtype=str, encoding="utf-8",
                     encoding_errors="replace", low_memory=False)
    keys = df[col].str.strip().str.replace(r"\.0$", "", regex=True).dropna()
    return set(keys[keys != ""])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssi", required=True)
    ap.add_argument("--seace", required=True)
    ap.add_argument("--infobras", required=True)
    ap.add_argument("--ssi-col", default="CODIGO_UNICO")
    ap.add_argument("--seace-col", default="CUI")
    ap.add_argument("--infobras-col", default="CUI")
    a = ap.parse_args()

    ssi = load_keys(a.ssi, a.ssi_col)
    seace = load_keys(a.seace, a.seace_col)
    inf = load_keys(a.infobras, a.infobras_col)

    print(f"CUI únicos  SSI={len(ssi):,}  SEACE={len(seace):,}  INFOBRAS={len(inf):,}")
    print(f"INFOBRAS ∩ SSI    : {len(inf & ssi) / max(len(inf), 1):.1%} de INFOBRAS")
    print(f"INFOBRAS ∩ SEACE  : {len(inf & seace) / max(len(inf), 1):.1%} de INFOBRAS")
    print(f"Triple intersección: {len(inf & ssi & seace):,} obras utilizables")


if __name__ == "__main__":
    main()

