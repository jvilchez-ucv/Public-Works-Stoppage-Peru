import os
import zipfile
import pandas as pd

RAW_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/raw"

def inspect_infobras():
    xlsx_path = os.path.join(RAW_DIR, "DataSet-Obras-Publicas 24-10-2026.xlsx")
    print("--- DETALLE DE INFOBRAS ---")
    # Read with header=2 (the 3rd row contains real headers)
    df = pd.read_excel(xlsx_path, header=2, nrows=10)
    cols = list(df.columns)
    print(f"Total columnas: {len(cols)}")
    for i, c in enumerate(cols):
        print(f"[{i:2d}] {c}")
        
    print("\nColumnas clave de estado / avance / CUI:")
    for c in cols:
        cl = str(c).lower()
        if any(k in cl for k in ['cui', 'codigo', 'snip', 'estado', 'avance', 'costo', 'monto', 'paraliz', 'fech']):
            print(f"  -> {c} (ejemplo: {df[c].iloc[0] if len(df) > 0 else 'N/A'})")

def inspect_seace_contracts():
    print("\n--- DETALLE DE CONTRATOS Y ARTICULOS EN SEACE ---")
    z = os.path.join(RAW_DIR, "2026-01_seace_v3_csv_es.zip")
    with zipfile.ZipFile(z, 'r') as zf:
        if "Ent_Contratos.csv" in zf.namelist():
            with zf.open("Ent_Contratos.csv") as f:
                df = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Ent_Contratos.csv] Columnas:")
                for i, col in enumerate(df.columns):
                    print(f"  [{i:2d}] {col}")
                    
        if "Ent_Lic_ArticulosQueSeAdquirira.csv" in zf.namelist():
            with zf.open("Ent_Lic_ArticulosQueSeAdquirira.csv") as f:
                df_art = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Ent_Lic_ArticulosQueSeAdquirira.csv] Columnas:")
                for i, col in enumerate(df_art.columns):
                    print(f"  [{i:2d}] {col}")

        if "Registros.csv" in zf.namelist():
            with zf.open("Registros.csv") as f:
                df_reg = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Registros.csv] Columnas:")
                for i, col in enumerate(df_reg.columns):
                    print(f"  [{i:2d}] {col}")

if __name__ == "__main__":
    inspect_infobras()
    inspect_seace_contracts()

