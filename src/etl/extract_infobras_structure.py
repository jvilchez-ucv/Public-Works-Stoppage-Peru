import openpyxl
from collections import Counter

XLSX_PATH = "02_Obras_Publicas_GNN_XAI_Peru/data/raw/DataSet-Obras-Publicas 24-10-2026.xlsx"

wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
ws = wb.active

headers = []
sample_rows = []
total_count = 0
estado_counts = Counter()

# Find columns
for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
    if r_idx == 3:
        headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(row)]
    elif r_idx > 3:
        total_count += 1
        if len(sample_rows) < 5:
            sample_rows.append(row)
            
wb.close()

print(f"Total de obras en INFOBRAS: {total_count:,}")
print(f"Total columnas: {len(headers)}")
print("\nListado completo de columnas:")
for i, h in enumerate(headers):
    print(f"[{i:2d}] {h}")

print("\nBúsqueda de columnas de Estado, CUI, Monto y Fechas:")
for i, h in enumerate(headers):
    hl = h.lower()
    if any(k in hl for k in ['cui', 'snip', 'estado', 'paraliz', 'avance', 'costo', 'monto', 'plazo', 'fech', 'situacion', 'causal']):
        ej = sample_rows[0][i] if sample_rows else 'N/A'
        print(f"  -> [{i:2d}] {h:50s} | Ej: {ej}")

