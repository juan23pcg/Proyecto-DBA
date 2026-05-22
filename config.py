# config.py  ← va en la raíz del repo: Proyecto-DBA/config.py
from pathlib import Path
from pymongo import MongoClient

# Raíz del proyecto — se calcula automáticamente desde donde está este archivo
BASE = Path(__file__).resolve().parent

# MongoDB — cada quien puede sobreescribir con variable de entorno
import os
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = "upme_solar_db"

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]