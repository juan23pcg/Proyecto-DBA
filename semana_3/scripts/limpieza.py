import pandas as pd
from shapely import wkt
from shapely.geometry import mapping
import json
import os

import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db
csv_path = os.path.join(BASE, "semana_3", "datos", "procesados", "microsoft_pdet_filtrado.csv")
out_path = os.path.join(BASE, "semana_3", "datos", "procesados", "microsoft_pdet_limpio.csv")

df = pd.read_csv(csv_path)
print(f"Registros antes: {len(df)}")

# Coordenada del polígono problemático conocido
COORD_PROBLEMATICA = "-74.77944668605295"

# Eliminar cualquier fila que contenga esa coordenada
mask = df["geometry"].str.contains(COORD_PROBLEMATICA, na=False)
print(f"Filas con polígono problemático: {mask.sum()}")
df = df[~mask]

# Segunda validación — verificar cada geometría contra MongoDB
# MongoDB rechaza polígonos donde edges se cruzan aunque Shapely diga is_valid=True
# La forma más confiable es convertir a GeoJSON y verificar que el anillo esté orientado correctamente
from shapely.geometry.polygon import orient

validos = []
descartados = 0

for _, fila in df.iterrows():
    try:
        geom = wkt.loads(fila["geometry"])
        # Forzar orientación correcta CCW (counter-clockwise) que MongoDB requiere
        if geom.geom_type == "Polygon":
            geom = orient(geom, sign=1.0)
        elif geom.geom_type == "MultiPolygon":
            from shapely.ops import unary_union
            geom = orient(geom, sign=1.0)

        # Convertir a GeoJSON y verificar que sea serializable
        geojson = mapping(geom)
        json.dumps(geojson)  # verificar que no tiene NaN ni valores inválidos
        validos.append({
            "geometry": json.dumps(geojson),
            "area_m2":  fila["area_m2"],
            "height":   fila["height"],
            "fuente":   fila["fuente"]
        })
    except Exception as e:
        descartados += 1
        continue

df_limpio = pd.DataFrame(validos)
df_limpio.to_csv(out_path, index=False)

print(f"Registros después: {len(df_limpio)}")
print(f"Descartados: {descartados}")
print(f"CSV limpio guardado en: {out_path}")