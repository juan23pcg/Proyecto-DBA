import pandas as pd
import geopandas as gpd
import os

import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db

# Cargar municipios PDET
pdet = gpd.read_file(os.path.join(BASE, "semana_2", "datos", "procesados", "municipios_pdet.geojson"))
bbox = pdet.total_bounds
print(f"Bbox PDET:")
print(f"  Longitudes: {bbox[0]:.4f} a {bbox[2]:.4f}")
print(f"  Latitudes:  {bbox[1]:.4f} a {bbox[3]:.4f}")

# Descargar índice de Microsoft
print("\nDescargando índice de Microsoft...")
url_index = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"
df = pd.read_csv(url_index)
colombia = df[df["Location"] == "Colombia"]
print(f"Tiles disponibles para Colombia: {len(colombia)}")

# Guardar índice
out_dir = os.path.join(BASE, "semana_3", "datos", "raw", "microsoft")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "tiles_index.csv")
colombia.to_csv(out_path, index=False)
print(f"\nÍndice guardado en:\n{out_path}")