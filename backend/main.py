from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from pydantic import BaseModel
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "postgresql://postgres:password@localhost:5433/overture"
engine = create_engine(DB_URL)

class Verification(BaseModel):
    id: str
    correct_lat: float
    correct_lon: float

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.get("/place/next")
def get_next_place():
    """
    Fetches a random place from 'raw_places' that we haven't verified yet.
    """
    query = text("""
        SELECT 
            id, 
            names, 
            categories, 
            ST_AsGeoJSON(geometry) as geom_json
        FROM raw_places 
        ORDER BY RANDOM() 
        LIMIT 1;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query).fetchone()
        
    if not result:
        raise HTTPException(status_code=404, detail="No places found")

    geom = json.loads(result.geom_json)
    
    place_name = "Unknown Place"
    if result.names:
        place_name = str(result.names)

    return {
        "id": result.id,
        "name": place_name,
        "category": str(result.categories),
        "longitude": geom['coordinates'][0],
        "latitude": geom['coordinates'][1]
    }

@app.post("/place/verify")
def verify_place(data: Verification):
    """
    Saves the user's corrected location to the 'ground_truth' table.
    """
    create_table_sql = text("""
        CREATE TABLE IF NOT EXISTS ground_truth (
            id TEXT PRIMARY KEY,
            correct_lat FLOAT,
            correct_lon FLOAT,
            verified_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    upsert_sql = text("""
        INSERT INTO ground_truth (id, correct_lat, correct_lon)
        VALUES (:id, :lat, :lon)
        ON CONFLICT (id) DO UPDATE 
        SET correct_lat = :lat, correct_lon = :lon, verified_at = NOW();
    """)

    with engine.begin() as conn:
        conn.execute(create_table_sql)
        conn.execute(upsert_sql, {"id": data.id, "lat": data.correct_lat, "lon": data.correct_lon})
        
    return {"status": "saved", "id": data.id}