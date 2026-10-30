"""
02_build_seace_network.py
-------------------------
Procesa de forma masiva los 106 paquetes mensuales de SEACE v3 (2018 - 2026)
almacenados en data/raw/.

Extrae el grafo relacional de contratación pública:
1. Registros de procesos (OCID -> CUI / Entidad / Monto / Licitantes)
2. Adjudicaciones a proveedores (OCID -> RUC Proveedor / Consorcio)
3. Contratos formalizados (OCID -> Monto contratado / Monto ejecutado)
4. Perfil histórico longitudinal del contratista (2018-2026):
   - Volumen de contratos
   - Monto total acumulado
   - Diversificación institucional
   - Años de actividad en el mercado público
"""

import os
import re
import time
import zipfile
import pandas as pd
import numpy as np

RAW_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/raw"
INTERIM_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/interim"
OUTPUT_NODES_DIR = os.path.join(INTERIM_DIR, "network_nodes")
OUTPUT_EDGES_DIR = os.path.join(INTERIM_DIR, "network_edges")

os.makedirs(OUTPUT_NODES_DIR, exist_ok=True)
os.makedirs(OUTPUT_EDGES_DIR, exist_ok=True)

def clean_id(val):
    if val is None or str(val).lower() in ["nan", "none", ""]:
        return ""
    s = str(val).strip()
    return re.sub(r"\.0$", "", s)

def clean_ruc(val):
    s = clean_id(val)
    if "PE-RUC-" in s:
        s = s.replace("PE-RUC-", "")
    return s.strip()

def process_all_seace():
    start = time.time()
    zips = sorted([os.path.join(RAW_DIR, f) for f in os.listdir(RAW_DIR) if f.endswith(".zip") and "seace" in f.lower()])
    print(f"[{time.strftime('%H:%M:%S')}] INICIANDO PROCESAMIENTO MASIVO DE {len(zips)} PAQUETES SEACE (2018-2026)...")
    
    all_registros = []
    all_adjudicaciones = []
    all_contratos = []
    
    current_year = ""
    year_count = 0
    
    for z_idx, zpath in enumerate(zips):
        zname = os.path.basename(zpath)
        year_prefix = zname[:4]
        if year_prefix != current_year:
            if current_year:
                print(f"   -> Año {current_year} procesado ({year_count} meses).")
            current_year = year_prefix
            year_count = 0
            print(f"[{time.strftime('%H:%M:%S')}] Procesando año {current_year}...")
        year_count += 1
        
        with zipfile.ZipFile(zpath, "r") as zf:
            namelist = set(zf.namelist())
            
            # 1. Registros.csv
            if "Registros.csv" in namelist:
                with zf.open("Registros.csv") as f:
                    usecols = [
                        "Open Contracting ID",
                        "Entrega compilada:Comprador:ID de Organización",
                        "Entrega compilada:Planeación:Presupuesto:Identificador de proyecto",
                        "Entrega compilada:Licitación:Valor:Monto",
                        "Entrega compilada:Licitación:Número de licitantes"
                    ]
                    try:
                        df_reg = pd.read_csv(f, usecols=usecols, dtype=str, encoding="utf-8", encoding_errors="replace")
                        df_reg.columns = ["ocid", "comprador_id", "cui", "monto_licitacion", "num_licitantes"]
                        df_reg["cui"] = df_reg["cui"].apply(clean_id)
                        df_reg["comprador_id"] = df_reg["comprador_id"].apply(clean_ruc)
                        df_reg["anio_proceso"] = current_year
                        all_registros.append(df_reg)
                    except Exception as e:
                        pass

            # 2. Ent_Adj_Proveedores.csv
            if "Ent_Adj_Proveedores.csv" in namelist:
                with zf.open("Ent_Adj_Proveedores.csv") as f:
                    usecols = [
                        "Open Contracting ID",
                        "Entrega compilada:Adjudicaciones:Proveedores:ID de Organización",
                        "Entrega compilada:Adjudicaciones:Proveedores:Nombre de la Organización"
                    ]
                    try:
                        df_adj = pd.read_csv(f, usecols=usecols, dtype=str, encoding="utf-8", encoding_errors="replace")
                        df_adj.columns = ["ocid", "proveedor_id", "proveedor_nombre"]
                        df_adj["proveedor_id"] = df_adj["proveedor_id"].apply(clean_ruc)
                        all_adjudicaciones.append(df_adj)
                    except Exception as e:
                        pass

            # 3. Ent_Contratos.csv
            if "Ent_Contratos.csv" in namelist:
                with zf.open("Ent_Contratos.csv") as f:
                    usecols = [
                        "Open Contracting ID",
                        "Entrega compilada:Contratos:Valor:Monto",
                        "Entrega compilada:Contratos:Implementación:Valor final:Monto"
                    ]
                    try:
                        df_con = pd.read_csv(f, usecols=usecols, dtype=str, encoding="utf-8", encoding_errors="replace")
                        df_con.columns = ["ocid", "monto_contratado", "monto_final"]
                        all_contratos.append(df_con)
                    except Exception as e:
                        pass

    print(f"   -> Año {current_year} procesado ({year_count} meses).")
    print(f"[{time.strftime('%H:%M:%S')}] Consolidando tablas relacionales históricas...")
    
    df_reg_all = pd.concat(all_registros, ignore_index=True).drop_duplicates(subset=["ocid"]) if all_registros else pd.DataFrame()
    df_adj_all = pd.concat(all_adjudicaciones, ignore_index=True).drop_duplicates() if all_adjudicaciones else pd.DataFrame()
    df_con_all = pd.concat(all_contratos, ignore_index=True).drop_duplicates(subset=["ocid"]) if all_contratos else pd.DataFrame()
    
    print(f" - Procesos únicos consolidados (2018-2026): {len(df_reg_all):,}")
    print(f" - Adjudicaciones a proveedores consolidadas: {len(df_adj_all):,}")
    print(f" - Contratos formalizados consolidados: {len(df_con_all):,}")
    
    # Merge Registros + Adjudicaciones + Contratos
    print(f"[{time.strftime('%H:%M:%S')}] Construyendo aristas relacionales...")
    df_edges = pd.merge(df_adj_all, df_reg_all, on="ocid", how="inner")
    if len(df_con_all) > 0:
        df_edges = pd.merge(df_edges, df_con_all, on="ocid", how="left")
        
    print(f" - Total aristas de contratación vinculadas (2018-2026): {len(df_edges):,}")
    print(f" - Aristas con CUI de inversión válido: {(df_edges['cui'] != '').sum():,}")
    print(f" - Entidades públicas únicas: {df_edges['comprador_id'].nunique():,}")
    print(f" - Proveedores / Consorcios únicos: {df_edges['proveedor_id'].nunique():,}")
    
    # Save edges
    edges_file = os.path.join(OUTPUT_EDGES_DIR, "seace_contracting_edges.parquet")
    df_edges.to_parquet(edges_file, index=False, engine="pyarrow", compression="snappy")
    print(f"[{time.strftime('%H:%M:%S')}] Aristas guardadas en: {edges_file}")

    # Build longitudinal contractor features (2018 - 2026)
    print(f"[{time.strftime('%H:%M:%S')}] Computando perfiles longitudinales de contratistas...")
    df_edges["monto_num"] = pd.to_numeric(df_edges["monto_contratado"], errors="coerce").fillna(0)
    
    prov_summary = df_edges[df_edges["proveedor_id"] != ""].groupby("proveedor_id").agg(
        seace_num_adjudicaciones=("ocid", "count"),
        seace_monto_total_adjudicado=("monto_num", "sum"),
        seace_num_entidades_distintas=("comprador_id", "nunique"),
        seace_num_cuis_distintos=("cui", lambda x: (x != "").sum()),
        seace_anios_activos=("anio_proceso", "nunique"),
        seace_primer_anio=("anio_proceso", "min"),
        seace_ultimo_anio=("anio_proceso", "max")
    ).reset_index().rename(columns={"proveedor_id": "ruc_contratista"})
    
    prov_file = os.path.join(OUTPUT_NODES_DIR, "contractor_network_features.parquet")
    prov_summary.to_parquet(prov_file, index=False, engine="pyarrow", compression="snappy")
    print(f"[{time.strftime('%H:%M:%S')}] Perfil de {len(prov_summary):,} contratistas guardado en: {prov_file}")
    print(f"[{time.strftime('%H:%M:%S')}] PROCESAMIENTO MASIVO COMPLETADO en {time.time() - start:.1f}s.")

if __name__ == "__main__":
    process_all_seace()
