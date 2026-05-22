import pandas as pd
from pymongo import MongoClient
from shapely import wkt
from datetime import datetime
import os

import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db
client = MongoClient("mongodb://localhost:27017/")
db     = client["upme_solar_db"]
col    = db["goo_buildings"]
col.drop()

csv_path = os.path.join(BASE, "semana_3", "datos", "procesados", "google_pdet_filtrado.csv")

BATCH_SIZE = 10_000
total = 0
errores = 0
batch = []

for chunk in pd.read_csv(csv_path, chunksize=BATCH_SIZE):
    for _, fila in chunk.iterrows():
        try:
            geom = wkt.loads(fila["geometry"])
            doc  = {
                "geometry":           geom.__geo_interface__,
                "area_m2":            float(fila["area_in_meters"]),
                "confidence":         float(fila["confidence"]),
                "cod_dane_municipio": str(fila["cod_dane_municipio"]),
                "fuente":             "google",
                "cargado_en":         datetime.utcnow()
            }
            batch.append(doc)
        except Exception:
            errores += 1
            continue

        if len(batch) >= BATCH_SIZE:
            col.insert_many(batch)
            total += len(batch)
            batch = []
            print(f"  Insertados: {total:,}  |  Errores: {errores}")

if batch:
    col.insert_many(batch)
    total += len(batch)

col.create_index([("geometry", "2dsphere")])
col.create_index([("cod_dane_municipio", 1)])
col.create_index([("confidence", -1)])
print(f"\ngoo_buildings: {col.count_documents({}):,} documentos cargados")
print(f"Errores omitidos: {errores}")