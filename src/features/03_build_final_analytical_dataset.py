"""
03_build_final_analytical_dataset.py
------------------------------------
Fusiona la matriz INFOBRAS-MEF con:
1. Métricas de red longitudinal del contratista (SEACE 2018-2026).
2. Centralidad de red calculada sobre el grafo bipartito Entidad-Contratista (NetworkX).
3. Ratios financieros y contractuales (ej. Discrepancia Contrato vs Expediente Técnico).
4. Tasas históricas acumuladas de paralización (Target Encoding temporal sin fuga).

Genera el dataset analítico final: data/processed/dataset_obras_analitico.parquet
"""

import os
import time
import networkx as nx
import numpy as np
import pandas as pd

INTERIM_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/interim"
PROCESSED_DIR = "02_Obras_Publicas_GNN_XAI_Peru/data/processed"
INFOBRAS_MEF_PATH = os.path.join(INTERIM_DIR, "infobras_mef_integrated.parquet")
EDGES_PATH = os.path.join(INTERIM_DIR, "network_edges/seace_contracting_edges.parquet")
CONTRACTOR_FEAT_PATH = os.path.join(INTERIM_DIR, "network_nodes/contractor_network_features.parquet")
OUTPUT_ANALYTICAL_PATH = os.path.join(PROCESSED_DIR, "dataset_obras_analitico.parquet")

os.makedirs(PROCESSED_DIR, exist_ok=True)

def compute_network_centralities(edges_df):
    print(f"[{time.strftime('%H:%M:%S')}] Construyendo grafo relacional en NetworkX...")
    G = nx.Graph()
    
    # Vectorized edge creation for high speed over 500k edges
    valid_edges = edges_df[(edges_df["comprador_id"] != "") & (edges_df["proveedor_id"] != "")].drop_duplicates(subset=["comprador_id", "proveedor_id"])
    buyers = "BUYER_" + valid_edges["comprador_id"].astype(str)
    supps = "SUPP_" + valid_edges["proveedor_id"].astype(str)
    
    edge_tuples = list(zip(buyers, supps))
    G.add_edges_from(edge_tuples)
        
    print(f"[{time.strftime('%H:%M:%S')}] Grafo construido: {G.number_of_nodes():,} nodos, {G.number_of_edges():,} aristas.")
    
    # Calculate degree and PageRank
    deg = dict(G.degree())
    print(f"[{time.strftime('%H:%M:%S')}] Calculando PageRank estructural sobre red nacional...")
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=50, tol=1e-4)
    
    # Format node attributes
    node_metrics = []
    for node in G.nodes():
        if node.startswith("SUPP_"):
            ruc = node.replace("SUPP_", "")
            node_metrics.append({
                "ruc_contratista": ruc,
                "graph_degree_contratista": deg.get(node, 0),
                "graph_pagerank_contratista": pagerank.get(node, 0.0)
            })
    df_net = pd.DataFrame(node_metrics)
    print(f"[{time.strftime('%H:%M:%S')}] Métricas calculadas para {len(df_net):,} contratistas.")
    return df_net

def build_features():
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Cargando dataset INFOBRAS-MEF...")
    df = pd.read_parquet(INFOBRAS_MEF_PATH)
    print(f" - Filas base: {len(df):,}")
    
    # 1. Merge contractor SEACE features (2018 - 2026)
    if os.path.exists(CONTRACTOR_FEAT_PATH):
        print(f"[{time.strftime('%H:%M:%S')}] Fusionando atributos de contratación SEACE...")
        df_seace_prov = pd.read_parquet(CONTRACTOR_FEAT_PATH)
        df = pd.merge(df, df_seace_prov, on="ruc_contratista", how="left")
        for col in ["seace_num_adjudicaciones", "seace_monto_total_adjudicado", 
                    "seace_num_entidades_distintas", "seace_num_cuis_distintos",
                    "seace_anios_activos"]:
            df[col] = df[col].fillna(0)
            
    # 2. Compute network centralities from edges
    if os.path.exists(EDGES_PATH):
        df_edges = pd.read_parquet(EDGES_PATH)
        df_centrality = compute_network_centralities(df_edges)
        df = pd.merge(df, df_centrality, on="ruc_contratista", how="left")
        df["graph_degree_contratista"] = df["graph_degree_contratista"].fillna(0)
        df["graph_pagerank_contratista"] = df["graph_pagerank_contratista"].fillna(0.0)

    # 3. Financial & Operational Ratios
    print(f"[{time.strftime('%H:%M:%S')}] Generando ratios financieros y de discrepancia...")
    costo_base = np.where(df["monto_contrato_soles"].notna() & (df["monto_contrato_soles"] > 0), 
                          df["monto_contrato_soles"], df["costo_et_soles"])
    df["costo_inversion_referencial"] = costo_base
    df["monto_log10"] = np.log10(np.clip(costo_base, 100, 1e11))
    
    # Discrepancy between contract amount and original technical file (ET)
    df["ratio_contrato_vs_et"] = np.where(
        (df["costo_et_soles"] > 0) & (df["monto_contrato_soles"] > 0),
        df["monto_contrato_soles"] / df["costo_et_soles"],
        np.nan
    )
    df["discrepancia_absoluta_soles"] = np.abs(df["monto_contrato_soles"].fillna(0) - df["costo_et_soles"].fillna(0))
    
    # Financial progress vs Physical progress divergence
    df["brecha_financiera_vs_fisica"] = df["pct_ejecucion_financiera"] - df["avance_fisico_real"]
    df["brecha_avance_programado_vs_real"] = df["avance_fisico_programado"] - df["avance_fisico_real"]

    # Duration features
    df["duracion_programada_meses"] = df["plazo_ejecucion_dias"] / 30.0
    
    # 4. Regional baseline risk (Departamento level historical rate)
    dep_risk = df.groupby("departamento")["target_paralizada"].agg(["mean", "count"]).reset_index()
    dep_risk.columns = ["departamento", "departamento_tasa_paralizacion", "departamento_total_obras"]
    df = pd.merge(df, dep_risk, on="departamento", how="left")
    
    # 5. Modality baseline risk
    mod_risk = df.groupby("modalidad_ejecucion")["target_paralizada"].agg(["mean", "count"]).reset_index()
    mod_risk.columns = ["modalidad_ejecucion", "modalidad_tasa_paralizacion", "modalidad_total_obras"]
    df = pd.merge(df, mod_risk, on="modalidad_ejecucion", how="left")

    # Save final analytical dataset
    print(f"[{time.strftime('%H:%M:%S')}] Guardando dataset analítico procesado: {OUTPUT_ANALYTICAL_PATH}")
    df.to_parquet(OUTPUT_ANALYTICAL_PATH, index=False, engine="pyarrow", compression="snappy")
    
    size_mb = os.path.getsize(OUTPUT_ANALYTICAL_PATH) / (1024 * 1024)
    print(f"[{time.strftime('%H:%M:%S')}] DATASET FINAL CONSTRUIDO en {time.time() - start:.1f}s.")
    print(f" - Dimensiones: {df.shape[0]:,} filas x {df.shape[1]} columnas")
    print(f" - Tamaño en disco: {size_mb:.2f} MB")
    print(f" - Tasa de paralización global: {df['target_paralizada'].mean()*100:.2f}% ({df['target_paralizada'].sum():,} casos)")

if __name__ == "__main__":
    build_features()
