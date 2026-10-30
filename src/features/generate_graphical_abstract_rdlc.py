"""
generate_graphical_abstract_rdlc.py
-----------------------------------
Generates the Graphical Abstract with the exact official dimensions
required by Revista de la Construcción (RDLC):
Dimensions: 15 cm wide x 5 cm high (3:1 aspect ratio), 300 DPI high resolution.
Includes full sample traceability (191,180 gross -> 145,146 modeled cohort; 4.16% gross / 5.38% cohort).
"""

import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches

FIG_DIR_PAPER = "02_Obras_Publicas_GNN_XAI_Peru/paper/figures"
FIG_DIR_REPORTS = "02_Obras_Publicas_GNN_XAI_Peru/reports/figures"
os.makedirs(FIG_DIR_PAPER, exist_ok=True)
os.makedirs(FIG_DIR_REPORTS, exist_ok=True)

# 15 cm x 5 cm -> 3:1 aspect ratio
fig, ax = plt.subplots(figsize=(8.0, 2.67), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color palette matching RDLC blue style
c_navy = '#0a3871'
c_blue = '#0072bc'
c_light_blue = '#e6f2fa'
c_green = '#2e7d32'
c_light_green = '#e8f5e9'
c_orange = '#d84315'
c_light_orange = '#fbe9e7'

# Panel 1: Data Integration (0 to 30)
rect1 = patches.FancyBboxPatch((1, 4), 28, 92, boxstyle="round,pad=0.3,rounding_size=1.5",
                              facecolor=c_light_blue, edgecolor=c_blue, linewidth=1.2)
ax.add_patch(rect1)
ax.text(15, 87, "1. NATIONWIDE DATA (PERU)", ha='center', va='center', fontsize=7.5, fontweight='bold', color=c_navy)
ax.text(15, 65, "• INFOBRAS: 191,180 Gross Works\n  (145,146 Modeled Cohort)\n• MEF SSI: 1.4M Risk Logs\n• SEACE: 633K Processes (OCDS)", 
        ha='center', va='center', fontsize=6.0, color='#212529', linespacing=1.25)
ax.text(15, 19, "Stoppage: 4.16% Gross (5.38% Cohort)\nLinkage via CUI (89.3%)", ha='center', va='center', fontsize=5.8, fontweight='bold', color=c_blue)

# Arrow 1 -> 2
ax.annotate('', xy=(32, 50), xytext=(29.5, 50), 
            arrowprops=dict(facecolor=c_navy, edgecolor=c_navy, width=1.0, headwidth=4.5, headlength=5.0))

# Panel 2: Relational Graph & Features (33 to 63)
rect2 = patches.FancyBboxPatch((32.5, 4), 31, 92, boxstyle="round,pad=0.3,rounding_size=1.5",
                              facecolor=c_light_green, edgecolor=c_green, linewidth=1.2)
ax.add_patch(rect2)
ax.text(48, 87, "2. CONTRACTING GRAPH & XAI", ha='center', va='center', fontsize=7.5, fontweight='bold', color=c_green)
ax.text(48, 65, "• Bipartite Graph: 195K Nodes\n• 320K Contracting Edges\n• Degree & PageRank Centrality\n• 27 Selected Features (from 76)", 
        ha='center', va='center', fontsize=6.0, color='#212529', linespacing=1.25)
ax.text(48, 19, "LightGBM + Graph Network\nStrict Out-of-Time Test (2023–26)", ha='center', va='center', fontsize=5.8, fontweight='bold', color=c_green)

# Arrow 2 -> 3
ax.annotate('', xy=(66.5, 50), xytext=(64, 50), 
            arrowprops=dict(facecolor=c_navy, edgecolor=c_navy, width=1.0, headwidth=4.5, headlength=5.0))

# Panel 3: Performance & Audit Impact (67 to 99)
rect3 = patches.FancyBboxPatch((67, 4), 31.5, 92, boxstyle="round,pad=0.3,rounding_size=1.5",
                              facecolor=c_light_orange, edgecolor=c_orange, linewidth=1.2)
ax.add_patch(rect3)
ax.text(82.7, 87, "3. AUDIT EFFICIENCY & LIFT", ha='center', va='center', fontsize=7.5, fontweight='bold', color=c_orange)
ax.text(82.7, 65, "• AUROC: 0.7753 | AUPRC: 0.2587\n• Top 20% Audits Capture:\n  54.65% Stalled Works (2.74x)\n• TreeSHAP Auditability Dossier", 
        ha='center', va='center', fontsize=6.0, color='#212529', linespacing=1.25)
ax.text(82.7, 19, "Ex-Ante Preventive Control\nSupreme Audit Institutions", ha='center', va='center', fontsize=5.8, fontweight='bold', color=c_orange)

plt.tight_layout()
ga_paper = os.path.join(FIG_DIR_PAPER, "graphical_abstract_rdlc.png")
ga_reports = os.path.join(FIG_DIR_REPORTS, "graphical_abstract_rdlc.png")
plt.savefig(ga_paper, dpi=300, bbox_inches='tight', pad_inches=0.02)
plt.close()
shutil.copyfile(ga_paper, ga_reports)

print(f"Graphical Abstract RDLC generated at: {ga_paper} and {ga_reports}")
