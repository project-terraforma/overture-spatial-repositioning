import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from shapely import wkb

DB_URL = "postgresql://postgres:password@localhost:5433/overture"
engine = create_engine(DB_URL)

def load_data():
    print("Loading parquet file with Pandas...")
    try:
        df = pd.read_parquet("project_d_samples.parquet")
        
        print(f"Read {len(df)} rows.")
        
        print("Converting geometry column...")
        df['geometry'] = gpd.GeoSeries.from_wkb(df['geometry'])

        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs(epsg=4326, inplace=True)

        print("Writing to PostGIS database (this might take 10-20 seconds)...")
        gdf.to_postgis("raw_places", engine, if_exists="replace", index=False)
        
        print("Success! Data is now in the 'raw_places' table.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    load_data()