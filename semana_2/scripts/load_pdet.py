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
    print(gdf.columns)

    print("\nCOLUMNAS EXCEL:")
    print(pdet.columns)


    gdf["cod_dane"] = (
        gdf["mpio_ccdgo"]
        .astype(str)
        .str.zfill(5)
    )

    pdet["cod_dane"] = (
        pdet["Codigo dane de municipio"]
        .astype(str)
        .str.zfill(5)
    )

    gdf_pdet = gdf.merge(
        pdet,
        on="cod_dane",
        how="inner"
    )

    gdf_pdet = gdf_pdet[
        gdf_pdet.geometry.notnull()
    ]

    gdf_pdet["geometry"] = (
        gdf_pdet.buffer(0)
    )
    gdf_pdet = gdf_pdet.to_crs(
        epsg=4326
    )
    metric = gdf_pdet.to_crs(
        epsg=9377
    )

    gdf_pdet["area_km2"] = (
        metric.area / 1_000_000
    )
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
        "../datos/processed/municipios_pdet.geojson",
        driver="GeoJSON"
    )

    print("\nMunicipios PDET cargados:")
    print(len(gdf_pdet))

    return gdf_pdet