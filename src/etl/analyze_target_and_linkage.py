import os
import openpyxl
import pandas as pd
from collections import Counter

RAW_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/raw"
INFOBRAS_FILE = os.path.join(RAW_DIR, "DataSet-Obras-Publicas 24-10-2026.xlsx")
ESTADO_FILE = os.path.join(RAW_DIR, "ESTADO_SITUACIONAL.csv")

print("=================================================================")
print("ANÁLISIS DE ETIQUETAS, COBERTURA Y ENLACE ENTRE DATASETS")
print("=================================================================")

# 1. Analyze INFOBRAS
wb = openpyxl.load_workbook(INFOBRAS_FILE, read_only=True)
ws = wb.active

cui_set = set()
ruc_set = set()
estado_ejecucion_counter = Counter()
existe_paralizacion_counter = Counter()
modalidad_counter = Counter()
causales_counter = Counter()
departamentos_counter = Counter()

total_rows = 0
valid_cui = 0
valid_ruc = 0
has_adicionales = 0
has_plazo_ext = 0

# Col indices based on row 3 headers
# [ 4] Modalidad de ejecución de la obra
# [11] Estado de ejecución
# [21] Codigo unico de inversión
# [29] Departamento
# [40] RUC (Ejecución)
# [42] Monto del contrato  en soles
# [67] Existe Paralización
# [68] Causal de paralización
# [73] N° días de modificaciones de plazo
# [77] N° de adicionales de obra

for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
    if r_idx <= 3:
        continue
    total_rows += 1
    
    mod = str(row[4]).strip() if row[4] is not None else "VACIO"
    est = str(row[11]).strip() if row[11] is not None else "VACIO"
    cui = str(row[21]).strip() if row[21] is not None else ""
    cui = cui.replace(".0", "")
    dep = str(row[29]).strip() if row[29] is not None else "DESCONOCIDO"
    ruc = str(row[40]).strip() if row[40] is not None else ""
    ruc = ruc.replace(".0", "")
    par = str(row[67]).strip().upper() if row[67] is not None else "VACIO"
    cau = str(row[68]).strip() if row[68] is not None else "NO_REGISTRADO"
    
    modalidad_counter[mod] += 1
    estado_ejecucion_counter[est] += 1
    existe_paralizacion_counter[par] += 1
    departamentos_counter[dep] += 1
    
    if par in ["SI", "SÍ"]:
        causales_counter[cau] += 1
        
    if cui and cui not in ["0", "None", "", "NaN"]:
        valid_cui += 1
        cui_set.add(cui)
        
    if ruc and ruc not in ["0", "None", "", "NaN"]:
        valid_ruc += 1
        ruc_set.add(ruc)

wb.close()

print(f"\n1. RESUMEN INFOBRAS (Total obras: {total_rows:,})")
print(f" - Obras con CUI válido: {valid_cui:,} ({valid_cui/total_rows*100:.2f}%) | CUIs únicos: {len(cui_set):,}")
print(f" - Obras con RUC contratista: {valid_ruc:,} ({valid_ruc/total_rows*100:.2f}%) | RUCs únicos: {len(ruc_set):,}")

print(f"\nDistribución 'Existe Paralización':")
for k, v in existe_paralizacion_counter.most_common():
    print(f"  {k:15s}: {v:8,d} ({v/total_rows*100:.2f}%)")

print(f"\nDistribución 'Estado de ejecución':")
for k, v in estado_ejecucion_counter.most_common(10):
    print(f"  {k:30s}: {v:8,d} ({v/total_rows*100:.2f}%)")

print(f"\nDistribución 'Modalidad de ejecución':")
for k, v in modalidad_counter.most_common(8):
    print(f"  {k:30s}: {v:8,d} ({v/total_rows*100:.2f}%)")

print(f"\nPrincipales Causales de Paralización (Top 10):")
for k, v in causales_counter.most_common(10):
    print(f"  {k:50s}: {v:6,d}")

# 2. Check intersection with ESTADO_SITUACIONAL
print("\n2. RESUMEN ESTADO SITUACIONAL (MEF / Invierte.pe)")
df_mef = pd.read_csv(ESTADO_FILE, usecols=["CODIGO_UNICO"], dtype=str)
df_mef["CODIGO_UNICO"] = df_mef["CODIGO_UNICO"].str.strip().str.replace(r"\.0$", "", regex=True)
mef_cuis = set(df_mef["CODIGO_UNICO"].dropna().unique())
print(f"Total registros MEF: {len(df_mef):,}")
print(f"Total CUIs únicos MEF: {len(mef_cuis):,}")

intersection = cui_set.intersection(mef_cuis)
print(f"\n>>> INTERSECCIÓN DE ENLACE POR CUI <<<")
print(f"Obras de INFOBRAS con CUI presente en MEF: {len(intersection):,} de {len(cui_set):,} ({len(intersection)/max(len(cui_set), 1)*100:.2f}%)")

# Save summary stats
with open("02_Obras_Publicas_GNN_XAI_Peru/data/interim/linkage_summary.txt", "w") as f:
    f.write(f"Total INFOBRAS: {total_rows}\n")
    f.write(f"CUIs unicos INFOBRAS: {len(cui_set)}\n")
    f.write(f"CUIs unicos MEF: {len(mef_cuis)}\n")
    f.write(f"Interseccion CUI: {len(intersection)}\n")

