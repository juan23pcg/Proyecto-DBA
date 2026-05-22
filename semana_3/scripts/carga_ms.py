import gzip
import json
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from shapely.ops import unary_union
import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db

# Cargar municipios PDET
print("Cargando municipios PDET...")
pdet       = gpd.read_file(os.path.join(BASE, "semana_2", "datos", "procesados", "municipios_pdet.geojson"))
pdet_union = pdet.dissolve().geometry.iloc[0]

tiles_dir = os.path.join(BASE, "semana_3", "datos", "raw", "microsoft", "tiles")
out_csv   = os.path.join(BASE, "semana_3", "datos", "procesados", "microsoft_pdet_filtrado.csv")

archivos = [
    f for f in os.listdir(tiles_dir)
    if f.endswith(".csv.gz") and f != "test_tile.csv.gz"
]

total       = 0
total_fuera = 0
errores     = 0
primer_chunk = True
rows        = []

print(f"Procesando {len(archivos)} tiles...\n")

for archivo in archivos:
    path = os.path.join(tiles_dir, archivo)
    print(f"Tile: {archivo}")
    tile_count = 0

    with gzip.open(path, "rt", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                feature      = json.loads(linea)
                geom_shapely = shape(feature["geometry"])

                # Reparación triple
                if not geom_shapely.is_valid:
                    geom_shapely = make_valid(geom_shapely)

                if geom_shapely.geom_type == "GeometryCollection":
                    poligonos = [g for g in geom_shapely.geoms
                                 if g.geom_type in ("Polygon", "MultiPolygon")]
                    if not poligonos:
                        errores += 1
                        continue
                    geom_shapely = unary_union(poligonos)

                geom_shapely = geom_shapely.buffer(0)

                if geom_shapely.is_empty or not geom_shapely.is_valid:
                    errores += 1
                    continue
                if geom_shapely.geom_type not in ("Polygon", "MultiPolygon"):
                    errores += 1
                    continue

                # Filtro espacial
                if not pdet_union.contains(geom_shapely.centroid):
                    total_fuera += 1
                    continue

                # Calcular área
                gdf_tmp = gpd.GeoDataFrame(
                    [{"geometry": geom_shapely}], crs="EPSG:4326"
                ).to_crs(epsg=9377)
                area_m2 = float(gdf_tmp.area.iloc[0])

                # Guardar como WKT para el CSV
                rows.append({
                    "geometry": geom_shapely.wkt,
                    "area_m2":  area_m2,
                    "height":   float(feature["properties"].get("height", -1)),
                    "fuente":   "microsoft"
                })
                tile_count += 1
                total += 1

            except Exception:
                errores += 1
                continue

    print(f"  {tile_count} edificios dentro de PDET")

    # Guardar cada tile al CSV para no acumular en memoria
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(
            out_csv,
            mode="w" if primer_chunk else "a",
            header=primer_chunk,
            index=False
        )
        primer_chunk = False
        rows = []

print(f"\n✅ CSV generado: {out_csv}")
print(f"   Total guardados: {total:,}")
print(f"   Fuera de PDET:   {total_fuera:,}")
print(f"   Errores:         {errores}")