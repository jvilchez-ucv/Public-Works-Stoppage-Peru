"""
generate_fig1_framework.py
--------------------------
Generates the high-resolution (300 DPI) methodological framework diagram (Figure 1)
in academic English for the RDLC Q1/Q2 manuscript using the 2018-2026 cohort.
"""

import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches

FIG_DIR_REPORTS = "02_Obras_Publicas_GNN_XAI_Peru/reports/figures"
FIG_DIR_PAPER = "02_Obras_Publicas_GNN_XAI_Peru/paper/figures"
os.makedirs(FIG_DIR_REPORTS, exist_ok=True)
os.makedirs(FIG_DIR_PAPER, exist_ok=True)

fig, ax = plt.subplots(figsize=(13.2, 6.6), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color palette
c_blue = '#1f77b4'
c_green = '#2ca02c'
c_orange = '#ff7f0e'
c_purple = '#9467bd'

def draw_box(x, y, w, h, title, items, color, header_color):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.5",
                                  facecolor=color, edgecolor=header_color, linewidth=1.5, alpha=0.95)
    ax.add_patch(rect)
    
    h_rect = patches.FancyBboxPatch((x, y + h - 7), w, 7, boxstyle="round,pad=0.2,rounding_size=1.0",
                                    facecolor=header_color, edgecolor=header_color)
    ax.add_patch(h_rect)
    
    ax.text(x + w/2, y + h - 3.8, title, ha='center', va='center', fontsize=9.3, fontweight='bold', color='white')
    
    y_text = y + h - 11
    for it in items:
        ax.text(x + 1.8, y_text, it, ha='left', va='center', fontsize=8.0, color='#212529')
        y_text -= 4.2

# 1. Ingestion Box
draw_box(2, 10, 21.5, 80, "1. MASSIVE INGESTION (2018–2026)", [
    "• INFOBRAS (Comptroller CGR):",
    "  - 191,180 gross / 145,146 modeled",
    "  - Physical & financial progress",
    "  - Ground-truth: 7,810 stoppages",
    "",
    "• MEF (Invierte.pe / SSI):",
    "  - 1,405,386 situational reports",
    "  - Risk & delay tracking alerts",
    "",
    "• SEACE v3 (106 OCDS packages):",
    "  - 633,593 procurement processes",
    "  - 446,867 public contracts",
    "",
    "• Longitudinal Linkage Keys:",
    "  - CUI (Unique Investment Code)",
    "  - Contractor RUC ID (192,225)"
], '#e7f5ff', c_blue)

# 2. Graph & Feature Box
draw_box(26, 10, 22, 80, "2. RELATIONAL MODELING", [
    "• Bipartite Contracting Graph:",
    "  - 195,337 network nodes",
    "  - 320,916 relational edges",
    "  - 3,112 public entities",
    "  - 192,225 contractors/consortia",
    "",
    "• Structural Topology:",
    "  - Relational Degree Centrality",
    "  - National PageRank Centrality",
    "  - 9-year active persistence",
    "",
    "• Feature Filtering (76 -> 27):",
    "  - Contract-to-Tech. File Ratio",
    "  - Financial-Physical Gap (%)"
], '#ebfbee', c_green)

# 3. Model Training Box
draw_box(51, 10, 22, 80, "3. TEMPORAL EVALUATION", [
    "• Strict Out-of-Time Split:",
    "  - Train: Works <= 2022 (115,952)",
    "  - Test: Works 2023–2026 (29,194)",
    "  - Zero data leakage / lookahead",
    "",
    "• Predictive Architecture:",
    "  - Baseline: Logistic Regression",
    "  - Baseline: Tabular LightGBM",
    "  - Proposed: Graph-Augmented GBDT",
    "",
    "• Out-of-Time Performance:",
    "  - AUROC: 0.7753 | AUPRC: 0.2587",
    "  - Calibrated Brier Score: 0.2580"
], '#fff4e6', c_orange)

# 4. XAI & Decision Support Box
draw_box(76, 10, 22, 80, "4. EXPLAINABILITY & AUDIT", [
    "• Auditable XAI Layer:",
    "  - Global TreeSHAP (Beeswarm)",
    "  - Local TreeSHAP (Waterfall)",
    "  - Key risk driver attribution",
    "",
    "• Fiscal Efficiency (Comptroller):",
    "  - Recall@Top 10%: 32.3%",
    "  - Recall@Top 20%: 54.7%",
    "  - 2.74x lift vs. random audit",
    "",
    "• Public Policy Impact:",
    "  - Ex-ante Early-Warning System",
    "  - Optimal oversight prioritization"
], '#f3f0ff', c_purple)

# Connecting arrows
arrow_style = dict(facecolor='#495057', edgecolor='#495057', width=1.5, headwidth=7, headlength=8)
ax.annotate('', xy=(26, 50), xytext=(23.5, 50), arrowprops=arrow_style)
ax.annotate('', xy=(51, 50), xytext=(48, 50), arrowprops=arrow_style)
ax.annotate('', xy=(76, 50), xytext=(73, 50), arrowprops=arrow_style)

plt.title("Methodological Framework of the Graph-Augmented Early-Warning System with XAI Explainability (2018–2026)", 
          fontsize=11.5, fontweight='bold', pad=15)
plt.tight_layout()

fig1_reports = os.path.join(FIG_DIR_REPORTS, "fig1_methodological_framework.png")
fig1_paper = os.path.join(FIG_DIR_PAPER, "fig1_methodological_framework.png")
plt.savefig(fig1_reports, dpi=300, bbox_inches='tight')
plt.close()
shutil.copyfile(fig1_reports, fig1_paper)
print(f"Figure 1 updated in English at: {fig1_reports} and {fig1_paper}")
