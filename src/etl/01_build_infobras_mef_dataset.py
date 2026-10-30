"""
01_build_infobras_mef_dataset.py
--------------------------------
Integra los datos de INFOBRAS (Contraloría) con el historial situacional del MEF (Invierte.pe).
Genera la matriz integrada en formato Parquet: data/interim/infobras_mef_integrated.parquet
"""

import os
import re
import time
import openpyxl
import numpy as np
import pandas as pd

RAW_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/raw"
INTERIM_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/interim"
INFOBRAS_FILE = os.path.join(RAW_DIR, "DataSet-Obras-Publicas 24-10-2026.xlsx")
MEF_FILE = os.path.join(RAW_DIR, "ESTADO_SITUACIONAL.csv")
OUTPUT_PARQUET = os.path.join(INTERIM_DIR, "infobras_mef_integrated.parquet")

os.makedirs(INTERIM_DIR, exist_ok=True)

def clean_num(val):
    if val is None or val == "" or str(val).lower() in ["nan", "none"]:
        return np.nan
    s = str(val).strip().replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

def clean_str(val):
    if val is None or str(val).lower() in ["nan", "none"]:
        return ""
    s = str(val).strip()
    return re.sub(r"\.0$", "", s)

def parse_date_year(val):
    if val is None:
        return np.nan
    s = str(val).strip()
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3 and len(parts[2]) >= 4:
            try:
                return int(parts[2][:4])
            except ValueError:
                pass
    elif "-" in s:
        parts = s.split("-")
        if len(parts) >= 1 and len(parts[0]) == 4:
            try:
                return int(parts[0])
            except ValueError:
                pass
    return np.nan

def extract_infobras():
    print(f"[{time.strftime('%H:%M:%S')}] Extrayendo datos de INFOBRAS: {INFOBRAS_FILE}")
    wb = openpyxl.load_workbook(INFOBRAS_FILE, read_only=True)
    ws = wb.active
    
    records = []
    
    for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
        if r_idx <= 3:
            continue
            
        cui = clean_str(row[21])
        snip = clean_str(row[22])
        
        # Identification
        entidad_cod = clean_str(row[0])
        entidad_nom = clean_str(row[1])
        obra_id = clean_str(row[2])
        obra_nom = clean_str(row[3])
        modalidad = clean_str(row[4])
        saldo_obra = clean_str(row[5])
        naturaleza = clean_str(row[7])
        tipo_n1 = clean_str(row[8])
        tipo_n2 = clean_str(row[9])
        tipo_n3 = clean_str(row[10])
        estado_ejecucion = clean_str(row[11])
        reconstruccion = clean_str(row[12])
        nivel_gobierno = clean_str(row[19])
        sector = clean_str(row[20])
        
        # Spatial
        departamento = clean_str(row[29]).upper()
        provincia = clean_str(row[30]).upper()
        distrito = clean_str(row[31]).upper()
        
        # Contractors
        ruc_contratista = clean_str(row[40])
        nom_contratista = clean_str(row[41])
        ruc_supervision = clean_str(row[43])
        nom_supervision = clean_str(row[44])
        
        # Financial & Dates
        costo_et = clean_num(row[38])
        monto_contrato = clean_num(row[42])
        plazo_dias = clean_num(row[54])
        
        fecha_inicio_str = clean_str(row[52])
        anio_inicio = parse_date_year(fecha_inicio_str)
        
        avance_fisico_prog = clean_num(row[61])
        avance_fisico_real = clean_num(row[62])
        monto_val_ejec = clean_num(row[64])
        pct_ejec_financiera = clean_num(row[65])
        monto_ejec_financiera = clean_num(row[66])
        
        # Target variables
        paralizada_raw = clean_str(row[67]).upper()
        target_paralizada = 1 if (paralizada_raw in ["SI", "SÍ"] or estado_ejecucion == "Paralizada") else 0
        causal_paralizacion = clean_str(row[68])
        dias_paralizado = clean_num(row[70])
        
        # Cost Overrun & Delay metrics
        mod_plazo_dias = clean_num(row[73])
        num_controversias = clean_num(row[76])
        num_adicionales_obra = clean_num(row[77])
        monto_adicionales = clean_num(row[78])
        num_deductivos_obra = clean_num(row[81])
        monto_deductivos = clean_num(row[82])
        
        adicional_neto = (monto_adicionales if not np.isnan(monto_adicionales) else 0.0) - \
                         (monto_deductivos if not np.isnan(monto_deductivos) else 0.0)
                         
        base_contrato = monto_contrato if (not np.isnan(monto_contrato) and monto_contrato > 0) else costo_et
        sobrecosto_pct = (adicional_neto / base_contrato) if (base_contrato and base_contrato > 0) else np.nan
        retraso_ratio = (mod_plazo_dias / plazo_dias) if (plazo_dias and plazo_dias > 0 and not np.isnan(mod_plazo_dias)) else np.nan
        
        records.append({
            "cui": cui,
            "snip": snip,
            "codigo_infobras": obra_id,
            "nombre_obra": obra_nom,
            "codigo_entidad": entidad_cod,
            "entidad_publica": entidad_nom,
            "modalidad_ejecucion": modalidad,
            "saldo_obra": saldo_obra,
            "naturaleza_obra": naturaleza,
            "tipo_obra_n1": tipo_n1,
            "tipo_obra_n2": tipo_n2,
            "tipo_obra_n3": tipo_n3,
            "estado_ejecucion": estado_ejecucion,
            "reconstruccion_cambios": reconstruccion,
            "nivel_gobierno": nivel_gobierno,
            "sector": sector,
            "departamento": departamento,
            "provincia": provincia,
            "distrito": distrito,
            "ruc_contratista": ruc_contratista,
            "nombre_contratista": nom_contratista,
            "ruc_supervision": ruc_supervision,
            "nombre_supervision": nom_supervision,
            "costo_et_soles": costo_et,
            "monto_contrato_soles": monto_contrato,
            "plazo_ejecucion_dias": plazo_dias,
            "fecha_inicio_obra": fecha_inicio_str,
            "anio_inicio_obra": anio_inicio,
            "avance_fisico_programado": avance_fisico_prog,
            "avance_fisico_real": avance_fisico_real,
            "monto_valorizado_ejecutado": monto_val_ejec,
            "pct_ejecucion_financiera": pct_ejec_financiera,
            "monto_ejecucion_financiera": monto_ejec_financiera,
            # Targets
            "target_paralizada": target_paralizada,
            "causal_paralizacion": causal_paralizacion,
            "dias_paralizado": dias_paralizado,
            "modificacion_plazo_dias": mod_plazo_dias,
            "retraso_ratio": retraso_ratio,
            "num_controversias": num_controversias,
            "num_adicionales_obra": num_adicionales_obra,
            "monto_adicionales_soles": monto_adicionales,
            "monto_deductivos_soles": monto_deductivos,
            "monto_adicional_neto": adicional_neto,
            "sobrecosto_pct": sobrecosto_pct,
            "target_sobrecosto_binario": 1 if (sobrecosto_pct is not None and sobrecosto_pct > 0.10) else 0,
            "target_retraso_binario": 1 if (retraso_ratio is not None and retraso_ratio > 0.20) else 0
        })
        
    wb.close()
    df_info = pd.DataFrame(records)
    print(f"[{time.strftime('%H:%M:%S')}] INFOBRAS procesado: {len(df_info):,} filas.")
    return df_info

def aggregate_mef():
    print(f"[{time.strftime('%H:%M:%S')}] Agregando historial situacional del MEF: {MEF_FILE}")
    chunks = []
    usecols = ["CODIGO_UNICO", "TIP_REGISTRO", "PERIODO"]
    
    for chunk in pd.read_csv(MEF_FILE, usecols=usecols, chunksize=250000, dtype=str):
        chunk["CODIGO_UNICO"] = chunk["CODIGO_UNICO"].str.strip().str.replace(r"\.0$", "", regex=True)
        chunk = chunk[chunk["CODIGO_UNICO"].notna() & (chunk["CODIGO_UNICO"] != "")]
        chunks.append(chunk)
        
    df_all = pd.concat(chunks, ignore_index=True)
    print(f"[{time.strftime('%H:%M:%S')}] Total registros MEF cargados: {len(df_all):,}")
    
    # Feature engineering over MEF logs per CUI
    df_all["is_problema"] = df_all["TIP_REGISTRO"].str.contains("PROBLEMA", case=False, na=False).astype(int)
    df_all["is_riesgo"] = df_all["TIP_REGISTRO"].str.contains("RIESGO", case=False, na=False).astype(int)
    df_all["is_paraliz_atraso"] = (df_all["TIP_REGISTRO"] == "PROBLEMA (Atrasos y/o paralizaciones)").astype(int)
    df_all["periodo_num"] = pd.to_numeric(df_all["PERIODO"], errors="coerce")
    
    agg = df_all.groupby("CODIGO_UNICO").agg(
        mef_total_reportes=("TIP_REGISTRO", "count"),
        mef_num_problemas=("is_problema", "sum"),
        mef_num_riesgos=("is_riesgo", "sum"),
        mef_num_atrasos_paralizaciones=("is_paraliz_atraso", "sum"),
        mef_primer_periodo=("periodo_num", "min"),
        mef_ultimo_periodo=("periodo_num", "max"),
        mef_meses_seguimiento=("periodo_num", "nunique")
    ).reset_index()
    
    agg.rename(columns={"CODIGO_UNICO": "cui"}, inplace=True)
    agg["mef_ratio_problemas"] = agg["mef_num_problemas"] / agg["mef_total_reportes"]
    agg["mef_ratio_riesgos"] = agg["mef_num_riesgos"] / agg["mef_total_reportes"]
    
    print(f"[{time.strftime('%H:%M:%S')}] Agregación MEF completada: {len(agg):,} CUIs procesados.")
    return agg

def main():
    start = time.time()
    df_info = extract_infobras()
    df_mef = aggregate_mef()
    
    print(f"[{time.strftime('%H:%M:%S')}] Fusionando INFOBRAS y MEF por CUI...")
    df_merged = pd.merge(df_info, df_mef, on="cui", how="left")
    
    # Fill MEF NaNs for projects without MEF situacional log
    df_merged["mef_tiene_historial"] = df_merged["mef_total_reportes"].notna().astype(int)
    for col in ["mef_total_reportes", "mef_num_problemas", "mef_num_riesgos", 
                "mef_num_atrasos_paralizaciones", "mef_meses_seguimiento", 
                "mef_ratio_problemas", "mef_ratio_riesgos"]:
        df_merged[col] = df_merged[col].fillna(0)
        
    print(f"[{time.strftime('%H:%M:%S')}] Guardando dataset analítico en Parquet: {OUTPUT_PARQUET}")
    df_merged.to_parquet(OUTPUT_PARQUET, index=False, engine="pyarrow", compression="snappy")
    
    file_size_mb = os.path.getsize(OUTPUT_PARQUET) / (1024 * 1024)
    print(f"[{time.strftime('%H:%M:%S')}] PROCESO COMPLETADO EXITOSAMENTE en {time.time() - start:.1f}s.")
    print(f" - Filas totales: {len(df_merged):,}")
    print(f" - Columnas: {len(df_merged.columns)}")
    print(f" - Tamaño archivo Parquet: {file_size_mb:.2f} MB")
    print(f" - Obras con historial MEF: {df_merged['mef_tiene_historial'].sum():,} ({df_merged['mef_tiene_historial'].mean()*100:.2f}%)")
    print(f" - Obras con paralización confirmada: {df_merged['target_paralizada'].sum():,} ({df_merged['target_paralizada'].mean()*100:.2f}%)")

if __name__ == "__main__":
    main()

