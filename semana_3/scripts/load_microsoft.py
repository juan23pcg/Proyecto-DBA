import pandas as pd
import json
from pymongo import MongoClient
from datetime import datetime
import os

import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db
client = MongoClient("mongodb://localhost:27017/")
db     = client["upme_solar_db"]
col    = db["ms_buildings"]
col.drop()
print("Colección limpia.")

csv_path   = os.path.join(BASE, "semana_3", "datos", "procesados", "microsoft_pdet_limpio.csv")
BATCH_SIZE = 1_000
total      = 0
errores    = 0
batch      = []

df = pd.read_csv(csv_path)
print(f"Total filas a cargar: {len(df)}")

for _, fila in df.iterrows():
    try:
        geom_str = fila["geometry"]

        # Si viene con escapes dobles, limpiarlos
        if isinstance(geom_str, str):
            geom_str = geom_str.replace('""', '"').strip('"')

        geom = json.loads(geom_str)

        doc = {
            "geometry":           geom,
            "area_m2":            float(fila["area_m2"]),
            "height":             float(fila["height"]),
            "cod_dane_municipio": None,
            "fuente":             "microsoft",
            "cargado_en":         datetime.utcnow()
        }
        batch.append(doc)

    except Exception as e:
        errores += 1
        if errores <= 3:  # mostrar solo los primeros 3 errores para debug
            print(f"  Error fila {_}: {e}")
            print(f"  Valor: {str(fila['geometry'])[:100]}")
        continue

    if len(batch) >= BATCH_SIZE:
        col.insert_many(batch)
        total += len(batch)
        batch = []
        print(f"  Insertados: {total:,}  |  Errores: {errores}")

if batch:
    col.insert_many(batch)
    total += len(batch)

print(f"\nCreando índices...")
col.create_index([("geometry", "2dsphere")])
col.create_index([("cod_dane_municipio", 1)])
print("Índices:", list(col.index_information().keys()))

print(f"\n✅ Carga completada")
print(f"   Total insertados: {total:,}")
print(f"   Errores:          {errores}")
print(f"   Total en MongoDB: {col.count_documents({}):,}")