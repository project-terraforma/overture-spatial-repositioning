import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from shapely.wkt import loads as load_wkt
from shapely.geometry import box, Point
import ast

DB_URL = "postgresql://postgres:password@localhost:5433/overture"
engine = create_engine(DB_URL)

def run_prototype():
    print("Testing Hypothesis: Is the Bounding Box Center better than the original pin?")
    
    query = text("""
        SELECT 
            gt.id,
            gt.correct_lat,
            gt.correct_lon,
            r.bbox,
            ST_AsText(r.geometry) as original_geom_wkt
        FROM ground_truth gt
        JOIN raw_places r ON gt.id = r.id;
    """)
    
    df = pd.read_sql(query, engine)
    
    if len(df) == 0:
        print("No ground truth data found! Did you verify any points?")
        return

    improvements = 0
    total_dist_original = 0
    total_dist_new = 0
    valid_count = 0
    
    print(f"\nEvaluating {len(df)} sample points...")
    
    for idx, row in df.iterrows():
        try:
            truth_point = Point(row['correct_lon'], row['correct_lat'])
            
            original_point = load_wkt(row['original_geom_wkt'])
            
            b_str = row['bbox']
            if isinstance(b_str, str):
                b = ast.literal_eval(b_str)
            else:
                b = b_str

            if isinstance(b, dict):
                bbox_poly = box(b['xmin'], b['ymin'], b['xmax'], b['ymax'])
            elif isinstance(b, list) and len(b) == 4:
                bbox_poly = box(b[0], b[1], b[2], b[3])
            else:
                print(f"Skipping ID {row['id']}: Unknown bbox format {b}")
                continue

            new_prediction = bbox_poly.centroid
            
            dist_original = original_point.distance(truth_point)
            dist_new = new_prediction.distance(truth_point)
            
            total_dist_original += dist_original
            total_dist_new += dist_new
            valid_count += 1
            
            if dist_new < dist_original:
                improvements += 1
                
        except Exception as e:
            print(f"Skipping ID {row['id']}: Error {e}")
            continue

    if valid_count == 0:
        print("Could not process any points successfully.")
        return

    # Results
    avg_orig = total_dist_original / valid_count
    avg_new = total_dist_new / valid_count
    
    print("\n--- Prototype Results ---")
    print(f"Original Mean Error (Deg): {avg_orig:.6f}")
    print(f"New Model Mean Error (Deg): {avg_new:.6f}")
    print(f"Success Rate: The 'Box Center' method beat the original pin in {improvements}/{valid_count} cases.")
    
    if avg_new < avg_orig:
        print("\n✅ CONCLUSION: The Prototype successfully reduces spatial error!")
    else:
        print("\n❌ CONCLUSION: The Prototype is worse. We need a better heuristic (e.g., nearest road).")

if __name__ == "__main__":
    run_prototype()
