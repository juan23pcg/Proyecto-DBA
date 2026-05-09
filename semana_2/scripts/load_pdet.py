import geopandas as gpd
import pandas as pd

def load_pdet():

    gdf = gpd.read_file(
        "../datos/raw/MGN_ADM_MPIO_GRAFICO.shp"
    )

    pdet = pd.read_excel(
        "../datos/raw/MunicipiosPDET.xlsx"
    )

    print("COLUMNAS SHP:")
    print(gdf.columns.tolist())
    print("\nCOLUMNAS EXCEL:")
    print(pdet.columns.tolist())

    gdf["cod_dane"] = gdf["mpio_cdpmp"].astype(str).str.zfill(5)

    pdet["cod_dane"] = (
        pdet["CodMuni"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.zfill(5)
    )

    print("\nEjemplos cod_dane SHP:", gdf["cod_dane"].head(3).tolist())
    print("Ejemplos cod_dane Excel:", pdet["cod_dane"].head(3).tolist())

    gdf_pdet = gdf.merge(pdet, on="cod_dane", how="inner")

    print(f"\nMunicipios después del merge: {len(gdf_pdet)}")

    gdf_pdet = gdf_pdet[gdf_pdet.geometry.notnull()]
    gdf_pdet["geometry"] = gdf_pdet.buffer(0)
    gdf_pdet = gdf_pdet.to_crs(epsg=4326)

    metric = gdf_pdet.to_crs(epsg=9377)
    gdf_pdet["area_km2"] = metric.area / 1_000_000

    bounds = gdf_pdet.geometry.bounds
    gdf_pdet["bbox"] = bounds.apply(
        lambda r: {
            "min_lng": r.minx,
            "min_lat": r.miny,
            "max_lng": r.maxx,
            "max_lat": r.maxy
        },
        axis=1
    )

    gdf_pdet.to_file(
        "../datos/procesados/municipios_pdet.geojson",
        driver="GeoJSON"
    )

    print(f"\n Municipios PDET exportados: {len(gdf_pdet)}")
    print(f"   Esperados: 170")
    if len(gdf_pdet) != 170:
        print(" El conteo no coincide, revisar el cruce")

    return gdf_pdet