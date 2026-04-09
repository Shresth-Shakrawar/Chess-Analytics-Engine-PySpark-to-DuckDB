import chess.pgn
import polars as pl
import os

# Define file paths
PGN_FILE = "data/games.pgn"
OUTPUT_PARQUET = "data/bronze_games.parquet"

def extract_games():
    print(f"Starting extraction from {PGN_FILE}...")
    games_data = []
    
    with open(PGN_FILE, "r") as pgn:
        count = 0
        while True:
            headers = chess.pgn.read_headers(pgn)
            if headers is None:
                break
            
            games_data.append(dict(headers))
            count += 1
            
            # Print a progress update every 50k games
            if count % 50000 == 0:
                print(f"Parsed {count} games...")

    print("Parsing complete. Converting to Parquet...")
    df = pl.DataFrame(games_data)
    df.write_parquet(OUTPUT_PARQUET)
    print(f"Success! Saved to {OUTPUT_PARQUET}")

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    extract_games()