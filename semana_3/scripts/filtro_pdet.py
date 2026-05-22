import pandas as pd
import geopandas as gpd
import urllib.request
import os
from shapely.geometry import box
import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db

# Función para convertir QuadKey a bbox de coordenadas
def quadkey_to_bbox(quadkey):
    x, y, level = 0, 0, len(quadkey)
    for i, char in enumerate(quadkey):
        mask = 1 << (level - 1 - i)
        if char in ('1', '3'): x |= mask
        if char in ('2', '3'): y |= mask
    n = 2 ** level
    lon_min = (x / n) * 360 - 180
    lon_max = ((x + 1) / n) * 360 - 180
    lat_min = 180 / 3.14159 * (2 * __import__('math').atan(
        __import__('math').exp((1 - 2 * (y + 1) / n) * 3.14159)) - 3.14159 / 2)
    lat_max = 180 / 3.14159 * (2 * __import__('math').atan(
        __import__('math').exp((1 - 2 * y / n) * 3.14159)) - 3.14159 / 2)
    return lon_min, lat_min, lon_max, lat_max

# Bbox PDET
pdet = gpd.read_file(os.path.join(BASE, "semana_2", "datos", "procesados", "municipios_pdet.geojson"))
bbox = pdet.total_bounds
bbox_poly = box(bbox[0], bbox[1], bbox[2], bbox[3])

# Filtrar tiles que intersectan con bbox PDET
tiles = pd.read_csv(os.path.join(BASE, "semana_3", "datos", "raw", "microsoft", "tiles_index.csv"))

tiles_filtrados = []
for _, row in tiles.iterrows():
    lon_min, lat_min, lon_max, lat_max = quadkey_to_bbox(str(row["QuadKey"]))
    tile_poly = box(lon_min, lat_min, lon_max, lat_max)
    if bbox_poly.intersects(tile_poly):
        tiles_filtrados.append(row)

tiles_pdet = pd.DataFrame(tiles_filtrados)
print(f"Tiles totales Colombia:       {len(tiles)}")
print(f"Tiles que cubren zona PDET:   {len(tiles_pdet)}")

# Guardar índice filtrado
out_path = os.path.join(BASE, "semana_3", "datos", "raw", "microsoft", "tiles_pdet.csv")
tiles_pdet.to_csv(out_path, index=False)
print(f"\nÍndice filtrado guardado en:\n{out_path}")

# Descargar los tiles filtrados
out_dir = os.path.join(BASE, "semana_3", "datos", "raw", "microsoft", "tiles")
os.makedirs(out_dir, exist_ok=True)

print(f"\nIniciando descarga de {len(tiles_pdet)} tiles...")
for i, (_, row) in enumerate(tiles_pdet.iterrows(), 1):
    filename = f"{row['QuadKey']}.geojson.gz"
    out_path = os.path.join(out_dir, filename)
    if not os.path.exists(out_path):
        try:
            print(f"[{i}/{len(tiles_pdet)}] Descargando {filename}...")
            urllib.request.urlretrieve(row["Url"], out_path)
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print(f"[{i}/{len(tiles_pdet)}] Ya existe: {filename}")

print("\nDescarga Microsoft completada.")