import os
import zipfile
import pandas as pd
import openpyxl

RAW_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/raw"

def analyze_infobras():
    xlsx_path = os.path.join(RAW_DIR, "DataSet-Obras-Publicas 24-10-2026.xlsx")
    print(f"\n==========================================")
    print(f"1. ANALIZANDO INFOBRAS: {xlsx_path}")
    print(f"==========================================")
    if not os.path.exists(xlsx_path):
        print("No existe el archivo.")
        return None
    
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    sheets = wb.sheetnames
    print(f"Hojas en Excel: {sheets}")
    
    # Read first sheet with read_only or with pandas
    # Since it's 57MB, reading with pandas or read_only openpyxl
    df = pd.read_excel(xlsx_path, sheet_name=0, nrows=100)
    print(f"Total columnas ({len(df.columns)}): {list(df.columns)}")
    print(f"Primeras 3 filas:")
    print(df.head(3).T)
    
    # Check total rows efficiently
    ws = wb[sheets[0]]
    total_rows = ws.max_row
    print(f"Total aproximado de filas en INFOBRAS: {total_rows}")
    wb.close()
    return list(df.columns)

def analyze_estado_situacional():
    csv_path = os.path.join(RAW_DIR, "ESTADO_SITUACIONAL.csv")
    print(f"\n==========================================")
    print(f"2. ANALIZANDO ESTADO SITUACIONAL (MEF): {csv_path}")
    print(f"==========================================")
    if not os.path.exists(csv_path):
        print("No existe el archivo.")
        return None
    
    df = pd.read_csv(csv_path, nrows=50)
    print(f"Columnas ({len(df.columns)}): {list(df.columns)}")
    print(f"Muestra de datos:")
    print(df.head(3))
    
    # Check sample counts & unique CODIGO_UNICO in first 100k rows
    df_sample = pd.read_csv(csv_path, usecols=["CODIGO_UNICO", "TIP_REGISTRO", "PERIODO"], nrows=200000, dtype=str)
    print(f"En muestra de 200,000 registros de ESTADO_SITUACIONAL:")
    print(f" - CODIGO_UNICO unicos: {df_sample['CODIGO_UNICO'].nunique():,}")
    print(f" - Distribucion TIP_REGISTRO:\n{df_sample['TIP_REGISTRO'].value_counts()}")

def analyze_seace_zips():
    print(f"\n==========================================")
    print(f"3. ANALIZANDO ARCHIVOS SEACE v3 ZIP (2026)")
    print(f"==========================================")
    zips = [f for f in sorted(os.listdir(RAW_DIR)) if f.endswith(".zip") and "seace" in f]
    print(f"Encontrados {len(zips)} paquetes mensuales de SEACE:")
    for z in zips:
        size_mb = os.path.getsize(os.path.join(RAW_DIR, z)) / (1024 * 1024)
        print(f" - {z} ({size_mb:.2f} MB)")
        
    # Analyze one zip in detail
    sample_zip = os.path.join(RAW_DIR, zips[0])
    with zipfile.ZipFile(sample_zip, 'r') as zf:
        print(f"\nTablas dentro de {zips[0]}:")
        for info in zf.infolist():
            print(f"   * {info.filename:35s} {info.file_size/1024:8.1f} KB")
            
        # Inspect Ent_Contratos.csv
        if "Ent_Contratos.csv" in zf.namelist():
            with zf.open("Ent_Contratos.csv") as f:
                df_con = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Ent_Contratos.csv] Columnas:")
                print(list(df_con.columns))
                print("\n[Ent_Contratos.csv] Muestra:")
                print(df_con.head(2).T)
                
        # Inspect Ent_PartesInvolucradas.csv
        if "Ent_PartesInvolucradas.csv" in zf.namelist():
            with zf.open("Ent_PartesInvolucradas.csv") as f:
                df_part = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Ent_PartesInvolucradas.csv] Columnas:")
                print(list(df_part.columns))
                print("\n[Ent_PartesInvolucradas.csv] Muestra:")
                print(df_part.head(2).T)

        # Inspect Ent_Adj_Proveedores.csv
        if "Ent_Adj_Proveedores.csv" in zf.namelist():
            with zf.open("Ent_Adj_Proveedores.csv") as f:
                df_prov = pd.read_csv(f, nrows=5, encoding="utf-8", encoding_errors="replace")
                print("\n[Ent_Adj_Proveedores.csv] Columnas:")
                print(list(df_prov.columns))
                print("\n[Ent_Adj_Proveedores.csv] Muestra:")
                print(df_prov.head(2).T)

if __name__ == "__main__":
    analyze_infobras()
    analyze_estado_situacional()
    analyze_seace_zips()

