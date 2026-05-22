import geopandas as gpd
from pymongo import MongoClient
from datetime import datetime
import os

import sys
from pathlib import Path

# Agregar raíz del proyecto al path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import BASE, get_db
client = MongoClient("mongodb://localhost:27017/")
db = client["upme_solar_db"]
col = db["municipios_pdet"]
col.drop()

pdet = gpd.read_file(os.path.join(BASE, "semana_2", "datos", "procesados", "municipios_pdet.geojson"))

docs = []
for _, fila in pdet.iterrows():
    doc = {
        "cod_dane":       str(fila["cod_dane"]),
        "nombre":         fila["Municipio"],
        "departamento":   fila["Departamento"],
        "subregion_pdet": fila["SubPDET"],
        "area_km2":       float(fila["area_km2"]),
        "pdet":           True,
        "geometry":       fila["geometry"].__geo_interface__,
        "fuente":         "MGN2025",
        "cargado_en":     datetime.utcnow()
    }
    docs.append(doc)

col.insert_many(docs)
col.create_index([("geometry", "2dsphere")])
col.create_index([("cod_dane", 1)], unique=True)
print(f"municipios_pdet: {col.count_documents({})} documentos cargados")