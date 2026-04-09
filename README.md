# Chess Analytics Pipeline

A batch-processing data pipeline utilizing a Medallion Architecture to analyze PGN (Portable Game Notation) files. The stack utilizes local, in-process analytical processing (OLAP) via DuckDB against partitioned Parquet files, decoupling compute from storage for the frontend.

## Architecture Stack
* **Extraction (Bronze):** `python-chess` + `Polars` (Regex/Header extraction to Parquet)
* **Transformation (Gold):** `PySpark` (Type casting, null handling, feature engineering)
* **Analytical Engine (OLAP):** `DuckDB` (Vectorized SQL execution on disk)
* **Presentation (UI):** `Streamlit` + `Altair` (Interactive state and rendering)

## Project Structure
```text
chess_analytics/
├── .streamlit/
│   └── config.toml          # Enforces dark mode theme
├── data/
│   ├── games.pgn            # Raw Lichess/Chess.com data (Ignored)
│   ├── bronze_games.parquet # Extracted metadata (Ignored)
│   └── gold_games.parquet/  # Transformed PySpark output (Ignored)
├── pipeline/
│   ├── __init__.py
│   ├── spark_etl.py         # PySpark transformation logic
│   └── queries.py           # DuckDB SQL execution functions
├── app.py                   # Streamlit dashboard & Altair rendering
├── pgn_to_parquet.py        # Ingestion script
├── requirements.txt
└── .gitignore
```

## Execution Pipeline

**1. Environment Setup**
Ensure Java/OpenJDK is installed (required for PySpark). 
```bash
python -m venv chess-env
source chess-env/bin/activate
pip install -r requirements.txt
```

**2. Data Ingestion (Raw to Bronze)**
Place your raw `.pgn` file in the `data/` directory and name it `games.pgn`. This script parses the headers and writes a highly compressed Bronze Parquet file.
```bash
python pgn_to_parquet.py
```

**3. ETL Processing (Bronze to Gold)**
Executes the PySpark job to clean data types, filter malformed Lichess data (`?` Elo ratings), engineer features (EloDiff), and write the final Gold dataset via `coalesce(1)`.
```bash
# Note: Ensure JAVA_HOME is configured for your environment
python pipeline/spark_etl.py
```

**4. Analytics Dashboard**
Spins up the Streamlit server. DuckDB executes all SQL queries directly against the `gold_games.parquet` file on disk.
```bash
streamlit run app.py
```
