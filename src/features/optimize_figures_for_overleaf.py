"""
optimize_figures_for_overleaf.py
--------------------------------
Convierte las imágenes de RGBA (con canal alfa pesado) a RGB estándar
optimizadas para que pdfLaTeX en el plan gratuito de Overleaf compile en menos de 5 segundos.
"""

import os
import glob
from PIL import Image

FIG_DIR = "02_Obras_Publicas_GNN_XAI_Peru/paper/figures"

for p in sorted(glob.glob(os.path.join(FIG_DIR, "*.png"))):
    im = Image.open(p)
    orig_size_kb = os.path.getsize(p) / 1024
    
    # Convert RGBA to RGB with white background
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        bg = Image.new('RGB', im.size, (255, 255, 255))
        if im.mode == 'P':
            im = im.convert('RGBA')
        bg.paste(im, mask=im.split()[-1]) # Use alpha as mask
        im = bg
    else:
        im = im.convert('RGB')
        
    # Resize slightly if width > 2000 px (sufficient for 300 DPI on 6.5 inches)
    if im.width > 2000:
        new_w = 2000
        new_h = int(im.height * (2000 / im.width))
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
    # Save optimized RGB PNG
    im.save(p, "PNG", optimize=True)
    new_size_kb = os.path.getsize(p) / 1024
    print(f"Optimizada: {os.path.basename(p)} ({im.size[0]}x{im.size[1]}) | {orig_size_kb:.1f} KB -> {new_size_kb:.1f} KB")

