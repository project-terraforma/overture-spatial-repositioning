import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text

# Connect to DB (Port 5433)
DB_URL = "postgresql://postgres:password@localhost:5433/overture"
engine = create_engine(DB_URL)

def analyze_offsets():
    # SQL Query:
    # 1. Join 'ground_truth' (your clicks) with 'raw_places' (original data).
    # 2. Calculate the distance (ST_Distance) in meters between the two points.
    # 3. Use the 'geography' type for accurate meter calculation on a sphere.
    query = text("""
        SELECT 
            gt.id,
            r.names,
            ST_Distance(
                ST_SetSRID(ST_MakePoint(gt.correct_lon, gt.correct_lat), 4326)::geography,
                r.geometry::geography
            ) as offset_meters
        FROM ground_truth gt
        JOIN raw_places r ON gt.id = r.id;
    """)
    
    # Load into Pandas
    print("Fetching data from database...")
    df = pd.read_sql(query, engine)
    
    if len(df) == 0:
        print("No data found! Did you click 'Confirm' on the map at least once?")
        return

    # Basic Statistics
    print("\n--- Offset Analysis ---")
    print(f"Count: {len(df)} places verified")
    print(f"Mean Offset: {df['offset_meters'].mean():.2f} meters")
    print(f"Median Offset: {df['offset_meters'].median():.2f} meters")
    print(f"Max Offset: {df['offset_meters'].max():.2f} meters")
    
    # Generate the Histogram (Visual Proof)
    plt.figure(figsize=(10, 6))
    sns.histplot(df['offset_meters'], bins=10, kde=True)
    plt.title('Distribution of Positional Error (Overture vs. Ground Truth)')
    plt.xlabel('Offset Error (meters)')
    plt.ylabel('Count of Places')
    
    # Save the plot
    plt.savefig('offset_report.png')
    print("\nGraph saved as 'offset_report.png'. Check your folder!")

if __name__ == "__main__":
    analyze_offsets()
