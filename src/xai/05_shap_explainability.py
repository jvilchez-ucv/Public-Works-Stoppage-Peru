"""
05_shap_explainability.py
-------------------------
Computes global and local TreeSHAP explanations for the proposed model and generates
high-resolution (300 DPI) scientific figures in academic English for the RDLC manuscript:
- Fig 2 (fig2_roc_pr_curves.png): Out-of-time ROC and Precision-Recall curves (2023–2026).
- Fig 3 in manuscript (fig5_audit_efficiency_recall_curve.png): Cumulative Audit Capture Curve (Recall@Top K%).
- Fig 4 in manuscript (fig3_shap_summary_beeswarm.png): Global TreeSHAP Summary Beeswarm Plot (27 features).
- Fig 5 in manuscript (fig4_shap_waterfall_auditing_case.png): Local TreeSHAP Waterfall Plot of a real audited stalled work,
  with corrected percentage scaling (69.27%, 19.47%, 0.00%) and formatted PEN currency amounts with thousand separators.
"""

import os
import shutil
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import lightgbm as lgb
from sklearn.metrics import roc_curve, precision_recall_curve, auc

DATA_PATH = "02_Obras_Publicas_GNN_XAI_Peru/data/processed/dataset_obras_analitico.parquet"
FIG_DIR_REPORTS = "02_Obras_Publicas_GNN_XAI_Peru/reports/figures"
FIG_DIR_PAPER = "02_Obras_Publicas_GNN_XAI_Peru/paper/figures"
os.makedirs(FIG_DIR_REPORTS, exist_ok=True)
os.makedirs(FIG_DIR_PAPER, exist_ok=True)

# Publication styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 12

# Complete mapping of the 27 retained features into academic English
FEATURE_NAMES_MAP = {
    "monto_log10": "Investment Amount (Log10 PEN)",
    "costo_inversion_referencial": "Reference Cost (PEN)",
    "plazo_ejecucion_dias": "Contractual Duration (Days)",
    "duracion_programada_meses": "Scheduled Duration (Months)",
    "ratio_contrato_vs_et": "Contract-to-Technical File Ratio",
    "discrepancia_absoluta_soles": "Budget Discrepancy (PEN)",
    "avance_fisico_programado": "Scheduled Physical Progress (%)",
    "avance_fisico_real": "Actual Physical Progress (%)",
    "pct_ejecucion_financiera": "Financial Execution (%)",
    "brecha_financiera_vs_fisica": "Financial-Physical Gap (%)",
    "brecha_avance_programado_vs_real": "Physical Schedule Lag (Sched. - Actual %)",
    "mef_tiene_historial": "MEF Tracking Registration",
    "mef_total_reportes": "Total MEF Situational Reports",
    "mef_num_problemas": "MEF Problem Reports Count",
    "mef_num_riesgos": "MEF Risk Alerts",
    "mef_num_atrasos_paralizaciones": "Prior Delay/Stoppage Alerts (MEF)",
    "mef_meses_seguimiento": "MEF Tracked Months",
    "mef_ratio_problemas": "Problem Report Ratio (MEF)",
    "departamento_tasa_paralizacion": "Regional Historical Risk",
    "modalidad_tasa_paralizacion": "Execution Modality Historical Risk",
    "seace_num_adjudicaciones": "SEACE Contract Awards (2018–2026)",
    "seace_monto_total_adjudicado": "Total SEACE Awarded Amount (PEN)",
    "seace_num_entidades_distintas": "Distinct Procuring Entities",
    "seace_num_cuis_distintos": "Distinct CUI Projects",
    "seace_anios_activos": "Active Contracting Years (SEACE)",
    "graph_degree_contratista": "Contractor Relational Degree",
    "graph_pagerank_contratista": "Contractor Structural PageRank"
}

PCT_BASIS_COLS = {
    "avance_fisico_programado",
    "avance_fisico_real",
    "pct_ejecucion_financiera",
    "brecha_financiera_vs_fisica",
    "brecha_avance_programado_vs_real"
}

CURRENCY_PEN_COLS = {
    "costo_inversion_referencial",
    "discrepancia_absoluta_soles",
    "seace_monto_total_adjudicado"
}

INT_COUNT_COLS = {
    "plazo_ejecucion_dias",
    "mef_tiene_historial",
    "mef_total_reportes",
    "mef_num_problemas",
    "mef_num_riesgos",
    "mef_num_atrasos_paralizaciones",
    "mef_meses_seguimiento",
    "seace_num_adjudicaciones",
    "seace_num_entidades_distintas",
    "seace_num_cuis_distintos",
    "seace_anios_activos",
    "graph_degree_contratista"
}


def format_feature_value(col_name, raw_val):
    """Formats a single feature value cleanly for the TreeSHAP Waterfall plot."""
    if pd.isna(raw_val):
        return "N/A"
    if col_name in PCT_BASIS_COLS:
        # Stored in basis points (x100); convert to real percentage with 2 decimals
        real_pct = float(raw_val) / 100.0 if abs(float(raw_val)) > 100.0 else float(raw_val)
        return f"{real_pct:.2f}%"
    if col_name in CURRENCY_PEN_COLS:
        return f"S/ {float(raw_val):,.0f}"
    if col_name in INT_COUNT_COLS:
        return f"{int(round(float(raw_val))):,}"
    return f"{float(raw_val):.2f}"


def save_both(fig_filename):
    src = os.path.join(FIG_DIR_REPORTS, fig_filename)
    dst = os.path.join(FIG_DIR_PAPER, fig_filename)
    plt.savefig(src, dpi=300, bbox_inches='tight')
    plt.close()
    shutil.copyfile(src, dst)
    print(f" -> Saved (300 DPI): {src} & {dst}")


def generate_visualizations():
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Loading analytical dataset (N = 145,146 modeled works)...")
    df = pd.read_parquet(DATA_PATH)
    df = df[df["anio_inicio_obra"].notna() & (df["anio_inicio_obra"] >= 2012) & (df["anio_inicio_obra"] <= 2026)].copy()
    
    train_mask = df["anio_inicio_obra"] <= 2022
    test_mask = df["anio_inicio_obra"] >= 2023
    
    features = list(FEATURE_NAMES_MAP.keys())
    
    X_train = df.loc[train_mask, features]
    y_train = df.loc[train_mask, "target_paralizada"].values
    X_test = df.loc[test_mask, features]
    y_test = df.loc[test_mask, "target_paralizada"].values
    
    pos_weight = (len(y_train) - np.sum(y_train)) / max(np.sum(y_train), 1)
    
    print(f"[{time.strftime('%H:%M:%S')}] Training Graph-Augmented LightGBM model...")
    model = lgb.LGBMClassifier(
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
    model.fit(X_train, y_train)
    y_probs = model.predict_proba(X_test)[:, 1]
    
    # -------------------------------------------------------------
    # FIGURE 2: Out-of-Time ROC and Precision-Recall Curves (English)
    # -------------------------------------------------------------
    print(f"[{time.strftime('%H:%M:%S')}] Generating Figure 2: ROC and Precision-Recall Curves...")
    fpr, tpr, _ = roc_curve(y_test, y_probs)
    precision, recall, _ = precision_recall_curve(y_test, y_probs)
    roc_auc_val = auc(fpr, tpr)
    pr_auc_val = auc(recall, precision)
    
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), dpi=300)
    
    # Panel A: ROC
    axes[0].plot(fpr, tpr, color='#1f77b4', lw=2.2, label=f'Proposed (AUROC = {roc_auc_val:.3f})')
    axes[0].plot([0, 1], [0, 1], color='#7f7f7f', lw=1.2, linestyle='--', label='Random (AUROC = 0.500)')
    axes[0].set_title('A. ROC Curve (Out-of-Time Evaluation 2023–2026)', fontweight='bold')
    axes[0].set_xlabel('False Positive Rate (1 - Specificity)')
    axes[0].set_ylabel('True Positive Rate (Sensitivity)')
    axes[0].legend(loc='lower right', frameon=True)
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # Panel B: PR Curve
    no_skill = np.sum(y_test) / len(y_test)
    axes[1].plot(recall, precision, color='#d62728', lw=2.2, label=f'Proposed (AUPRC = {pr_auc_val:.3f})')
    axes[1].plot([0, 1], [no_skill, no_skill], color='#7f7f7f', lw=1.2, linestyle='--', label=f'Random ({no_skill*100:.1f}%)')
    axes[1].set_title('B. Precision-Recall Curve (Rare Class: 9.5% Test)', fontweight='bold')
    axes[1].set_xlabel('Recall (Sensitivity)')
    axes[1].set_ylabel('Precision (Positive Predictive Value)')
    axes[1].legend(loc='upper right', frameon=True)
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    save_both("fig2_roc_pr_curves.png")

    # -------------------------------------------------------------
    # FIGURE 4 (in manuscript): Global TreeSHAP Summary Beeswarm Plot
    # -------------------------------------------------------------
    print(f"[{time.strftime('%H:%M:%S')}] Computing TreeSHAP explanations across 3,000 test works...")
    np.random.seed(42)
    sample_idx = np.random.choice(len(X_test), size=min(3000, len(X_test)), replace=False)
    X_sample = X_test.iloc[sample_idx].copy()
    
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)
    
    # Map feature names to academic English
    english_feature_names = [FEATURE_NAMES_MAP.get(f, f) for f in features]
    shap_values.feature_names = english_feature_names
    
    fig, ax = plt.subplots(figsize=(10.5, 7.5), dpi=300)
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    plt.title("Global Feature Impact on Project Stoppage Probability (TreeSHAP)", fontweight='bold', pad=15)
    plt.xlabel("SHAP Value (Impact on Model Log-Odds Output)")
    plt.tight_layout()
    save_both("fig3_shap_summary_beeswarm.png")

    # -------------------------------------------------------------
    # FIGURE 5 (in manuscript): Local TreeSHAP Waterfall Plot (Corrected Scale)
    # -------------------------------------------------------------
    print(f"[{time.strftime('%H:%M:%S')}] Generating Figure 5: Local TreeSHAP Waterfall Audit Case...")
    stalled_test_indices = np.where((y_test[sample_idx] == 1) & (y_probs[sample_idx] > 0.70))[0]
    chosen_idx = stalled_test_indices[0] if len(stalled_test_indices) > 0 else 0
    
    # Create an Explanation object with formatted string display values for clean waterfall rendering
    raw_instance_data = X_sample.iloc[chosen_idx]
    formatted_data_strings = np.array(
        [format_feature_value(col, raw_instance_data[col]) for col in features],
        dtype=object
    )
    
    waterfall_exp = shap.Explanation(
        values=shap_values[chosen_idx].values,
        base_values=shap_values[chosen_idx].base_values,
        data=formatted_data_strings,
        feature_names=english_feature_names
    )
    
    base_val = float(shap_values[chosen_idx].base_values)
    fx_val = base_val + float(np.sum(shap_values[chosen_idx].values))
    prob_val = 1.0 / (1.0 + np.exp(-fx_val))
    print(f" -> Audited Case Metrics: E[f(X)] = {base_val:.3f}, f(x) = {fx_val:.3f}, Predicted Prob = {prob_val*100:.2f}%")
    for col, f_str, sv in zip(features, formatted_data_strings, shap_values[chosen_idx].values):
        if abs(sv) >= 0.08:
            print(f"    * {FEATURE_NAMES_MAP[col]}: {f_str} -> SHAP = {sv:+.3f}")

    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=300)
    shap.plots.waterfall(waterfall_exp, max_display=10, show=False)
    plt.title("Explainable Audit of a Stalled Public Work (Real Test Case)", fontweight='bold', pad=15)
    plt.tight_layout()
    save_both("fig4_shap_waterfall_auditing_case.png")

    # -------------------------------------------------------------
    # FIGURE 3 (in manuscript): Fiscal Audit Efficiency Curve (Recall@Top K%)
    # -------------------------------------------------------------
    print(f"[{time.strftime('%H:%M:%S')}] Generating Figure 3: Fiscal Audit Efficiency Curve...")
    ks = np.arange(1, 51, 1)
    recalls_model = []
    recalls_random = []
    
    n_test = len(y_test)
    total_pos = np.sum(y_test)
    sorted_idx = np.argsort(y_probs)[::-1]
    
    for k in ks:
        top_n = int(n_test * (k / 100.0))
        detected = np.sum(y_test[sorted_idx[:top_n]])
        recalls_model.append((detected / total_pos) * 100.0)
        recalls_random.append(k)
        
    plt.figure(figsize=(8.8, 5.2), dpi=300)
    plt.plot(ks, recalls_model, color='#1f77b4', lw=2.5, label='Proposed Early-Warning System')
    plt.plot(ks, recalls_random, color='#7f7f7f', lw=1.5, linestyle='--', label='Random Audit Selection (Baseline)')
    plt.axvline(x=20, color='#2ca02c', linestyle=':', lw=1.8, label=f'Top 20% Audit (Captures {recalls_model[19]:.1f}% of Stoppages)')
    plt.axvline(x=10, color='#ff7f0e', linestyle=':', lw=1.8, label=f'Top 10% Audit (Captures {recalls_model[9]:.1f}% of Stoppages)')
    
    plt.title('Model Fiscal Efficiency: Proportion of Detected Stoppages vs. Audit Effort', fontweight='bold')
    plt.xlabel('Percentage of Works Audited by Comptroller (Top % by Risk)')
    plt.ylabel('Percentage of Early Detected Stalled Works (Recall %)')
    plt.legend(loc='lower right', frameon=True)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    save_both("fig5_audit_efficiency_recall_curve.png")

    print(f"[{time.strftime('%H:%M:%S')}] All English figures generated successfully in {time.time() - start:.1f}s.")


if __name__ == "__main__":
    generate_visualizations()
