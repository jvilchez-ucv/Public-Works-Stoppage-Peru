"""
04_train_models.py
------------------
Entrena y evalúa los modelos predictivos bajo partición temporal estricta (Backtesting)
con el grafo nacional completo (2018 - 2026):
- Train: Obras iniciadas hasta 2022 (115,952 obras)
- Test: Obras iniciadas en 2023 - 2026 (29,194 obras - evaluación fuera de tiempo)

Compara:
1. Baseline Lineal: Regresión Logística Balanceada
2. Baseline Tabular: LightGBM sin variables de red
3. Modelo Propuesto: LightGBM Graph-Augmented (Tabular + Métricas de Red SEACE 2018-2026)

Calcula AUPRC, AUROC, Brier Score, y Recall@Top K% de auditoría para Contraloría.
"""

import os
import time
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, 
    brier_score_loss, classification_report, f1_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import lightgbm as lgb

DATA_PATH = "02_Obras_Publicas_GNN_XAI_Peru/data/processed/dataset_obras_analitico.parquet"
RESULTS_DIR = "02_Obras_Publicas_GNN_XAI_Peru/reports"
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_feature_sets():
    # 1. Variables tabulares tradicionales (sin red)
    features_tabular = [
        "monto_log10", "costo_inversion_referencial", "plazo_ejecucion_dias", "duracion_programada_meses",
        "ratio_contrato_vs_et", "discrepancia_absoluta_soles",
        "avance_fisico_programado", "avance_fisico_real", "pct_ejecucion_financiera",
        "brecha_financiera_vs_fisica", "brecha_avance_programado_vs_real",
        # MEF tracking indicators
        "mef_tiene_historial", "mef_total_reportes", "mef_num_problemas", "mef_num_riesgos",
        "mef_num_atrasos_paralizaciones", "mef_meses_seguimiento", "mef_ratio_problemas",
        # Historical regional & modality baselines
        "departamento_tasa_paralizacion", "modalidad_tasa_paralizacion"
    ]
    
    # 2. Variables de red SEACE (Graph features 2018-2026)
    features_network = [
        "seace_num_adjudicaciones", "seace_monto_total_adjudicado",
        "seace_num_entidades_distintas", "seace_num_cuis_distintos",
        "seace_anios_activos",
        "graph_degree_contratista", "graph_pagerank_contratista"
    ]
    
    return features_tabular, features_tabular + features_network

def compute_recall_at_k(y_true, y_prob, k_percent):
    n = len(y_true)
    top_k = int(n * (k_percent / 100.0))
    idx = np.argsort(y_prob)[::-1][:top_k]
    total_positives = np.sum(y_true)
    if total_positives == 0:
        return 0.0
    detected_positives = np.sum(y_true[idx])
    return (detected_positives / total_positives) * 100.0

def run_experiment():
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Cargando dataset analítico completo...")
    df = pd.read_parquet(DATA_PATH)
    
    df = df[df["anio_inicio_obra"].notna() & (df["anio_inicio_obra"] >= 2012) & (df["anio_inicio_obra"] <= 2026)].copy()
    print(f" - Obras con año de inicio válido: {len(df):,}")
    
    # Temporal Split: Train <= 2022, Test 2023-2026
    train_mask = df["anio_inicio_obra"] <= 2022
    test_mask = df["anio_inicio_obra"] >= 2023
    
    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()
    
    y_train = df_train["target_paralizada"].values
    y_test = df_test["target_paralizada"].values
    
    print(f"\n--- PARTICIÓN TEMPORAL ESTRICTA (Sin Data Leakage) ---")
    print(f"Train (<= 2022): {len(df_train):,} obras | Paralizadas: {np.sum(y_train):,} ({np.mean(y_train)*100:.2f}%)")
    print(f"Test (2023-2026): {len(df_test):,} obras | Paralizadas: {np.sum(y_test):,} ({np.mean(y_test)*100:.2f}%)")
    
    feat_tab, feat_all = get_feature_sets()
    
    models = {
        "1. Regresión Logística (Tabular)": ("logreg", feat_tab),
        "2. LightGBM (Tabular Base)": ("lgb_tab", feat_tab),
        "3. LightGBM + Graph Network (Propuesto)": ("lgb_graph", feat_all)
    }
    
    results = {}
    
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    
    X_train_tab_imp = scaler.fit_transform(imputer.fit_transform(df_train[feat_tab]))
    X_test_tab_imp = scaler.transform(imputer.transform(df_test[feat_tab]))
    
    for name, (m_type, feats) in models.items():
        print(f"\n[{time.strftime('%H:%M:%S')}] Evaluando {name}...")
        
        if m_type == "logreg":
            clf = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
            clf.fit(X_train_tab_imp, y_train)
            y_probs = clf.predict_proba(X_test_tab_imp)[:, 1]
            
        elif m_type.startswith("lgb"):
            X_tr = df_train[feats]
            X_te = df_test[feats]
            
            pos_weight = (len(y_train) - np.sum(y_train)) / max(np.sum(y_train), 1)
            
            clf = lgb.LGBMClassifier(
                n_estimators=300,
                learning_rate=0.03,
                num_leaves=31,
                scale_pos_weight=pos_weight,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
            clf.fit(X_tr, y_train)
            y_probs = clf.predict_proba(X_te)[:, 1]
            
            if m_type == "lgb_graph":
                best_model = clf
                best_features = feats
                
        # Metrics
        auroc = roc_auc_score(y_test, y_probs)
        precision, recall, _ = precision_recall_curve(y_test, y_probs)
        auprc = auc(recall, precision)
        brier = brier_score_loss(y_test, y_probs)
        
        rec_5 = compute_recall_at_k(y_test, y_probs, 5)
        rec_10 = compute_recall_at_k(y_test, y_probs, 10)
        rec_20 = compute_recall_at_k(y_test, y_probs, 20)
        
        results[name] = {
            "AUPRC": round(auprc, 4),
            "AUROC": round(auroc, 4),
            "Brier_Score": round(brier, 4),
            "Recall@Top5%": round(rec_5, 2),
            "Recall@Top10%": round(rec_10, 2),
            "Recall@Top20%": round(rec_20, 2)
        }
        
        print(f"   -> AUROC: {auroc:.4f} | AUPRC: {auprc:.4f} | Brier: {brier:.4f}")
        print(f"   -> Auditoría Priorizada: Recall@Top5%: {rec_5:.1f}% | Recall@Top10%: {rec_10:.1f}% | Recall@Top20%: {rec_20:.1f}%")

    res_df = pd.DataFrame(results).T
    print("\n=======================================================")
    print("TABLA COMPARATIVA DE RENDIMIENTO ACTUALIZADA (2018-2026)")
    print("=======================================================")
    print(res_df.to_string())
    
    res_df.to_csv(os.path.join(RESULTS_DIR, "model_comparison_metrics.csv"))
    
    df_test_preds = df_test[["cui", "nombre_obra", "departamento", "target_paralizada"]].copy()
    df_test_preds["prob_paralizacion"] = y_probs
    df_test_preds.to_parquet(os.path.join(RESULTS_DIR, "test_predictions_graph_model.parquet"), index=False)
    
    print(f"\n[{time.strftime('%H:%M:%S')}] Modelado completado en {time.time() - start:.1f}s.")
    return best_model, best_features, df_test

if __name__ == "__main__":
    run_experiment()
