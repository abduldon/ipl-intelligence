import pandas as pd
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ipl.db")
RAW_PATH = os.path.join(os.path.dirname(__file__), "raw")

def get_connection():
    return sqlite3.connect(DB_PATH)

def ingest_matches():
    path = os.path.join(RAW_PATH, "matches.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.to_sql("matches", get_connection(), if_exists="replace", index=False)
    print(f"✅ Loaded {len(df)} matches into DB")

def ingest_deliveries():
    path = os.path.join(RAW_PATH, "deliveries.csv")
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df.to_sql("deliveries", get_connection(), if_exists="replace", index=False)
    print(f"✅ Loaded {len(df)} deliveries into DB")

if __name__ == "__main__":
    print("Starting data ingestion...")
    ingest_matches()
    ingest_deliveries()
    print("✅ Database ready at data/ipl.db")