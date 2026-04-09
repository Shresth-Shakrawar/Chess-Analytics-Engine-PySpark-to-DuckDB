import duckdb
import polars as pl

GOLD_DATA = "data/gold_games.parquet/*.parquet"

def get_kpis(min_elo, max_elo):
    query = f"""
        SELECT 
            COUNT(*)::INT as total_games,
            AVG((WhiteElo + BlackElo) / 2.0)::INT as avg_elo,
            (SUM(CASE WHEN ResultLabel = 'White Win' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) as white_win_rate,
            (SUM(CASE WHEN ResultLabel = 'Draw' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) as draw_rate
        FROM '{GOLD_DATA}' 
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo} 
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
    """
    res = duckdb.sql(query).fetchone()
    
    q_pop = f"""
        SELECT BaseOpening FROM '{GOLD_DATA}' 
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo} AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
        GROUP BY BaseOpening ORDER BY COUNT(*) DESC LIMIT 1
    """
    pop_res = duckdb.sql(q_pop).fetchone()
    
    # THE FIX: We now explicitly check that the result "is not None", otherwise default to 0
    return {
        "total_games": res[0] if res and res[0] is not None else 0,
        "avg_elo": res[1] if res and res[1] is not None else 0,
        "white_win_rate": res[2] if res and res[2] is not None else 0.0,
        "draw_rate": res[3] if res and res[3] is not None else 0.0,
        "top_opening": pop_res[0] if pop_res and pop_res[0] is not None else "N/A"
    }

def get_opening_efficacy(min_elo, max_elo, limit=10):
    # Notice we return the raw categories here so Altair can stack them nicely
    query = f"""
        WITH TopOpenings AS (
            SELECT BaseOpening FROM '{GOLD_DATA}'
            WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo} AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
            GROUP BY BaseOpening ORDER BY COUNT(*) DESC LIMIT {limit}
        )
        SELECT BaseOpening, ResultLabel, COUNT(*)::INT as count
        FROM '{GOLD_DATA}'
        WHERE BaseOpening IN (SELECT BaseOpening FROM TopOpenings)
          AND WhiteElo >= {min_elo} AND BlackElo >= {min_elo} AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
        GROUP BY BaseOpening, ResultLabel
    """
    return duckdb.sql(query).pl()

def get_draw_rate_trend():
    # We ignore the slider for this one to show the global trend across ALL Elos
    query = f"""
        SELECT 
            CAST(round((WhiteElo + BlackElo) / 2.0 / 100) * 100 AS INT) as EloBucket,
            (SUM(CASE WHEN ResultLabel = 'Draw' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as DrawRate,
            COUNT(*)::INT as GameVolume
        FROM '{GOLD_DATA}'
        WHERE WhiteElo > 1000 AND BlackElo > 1000
        GROUP BY EloBucket
        HAVING GameVolume > 500
        ORDER BY EloBucket
    """
    return duckdb.sql(query).pl()

def get_popular_openings():
    # Gets a list of openings that have enough games to be statistically significant
    query = f"""
        SELECT BaseOpening 
        FROM '{GOLD_DATA}' 
        GROUP BY BaseOpening 
        HAVING COUNT(*) > 500 
        ORDER BY COUNT(*) DESC
    """
    # Return as a standard Python list for the Streamlit selectbox
    return duckdb.sql(query).pl()['BaseOpening'].to_list()

def get_opening_win_rate_by_elo(opening_name):
    # Escape any single quotes so "King's" becomes "King''s" in SQL
    safe_opening = opening_name.replace("'", "''")
    
    query = f"""
        WITH BracketTotals AS (
            SELECT 
                CAST(round((WhiteElo + BlackElo) / 2.0 / 100) * 100 AS INT) as EloBucket,
                COUNT(*) as TotalGames
            FROM '{GOLD_DATA}'
            WHERE BaseOpening = '{safe_opening}'
            GROUP BY EloBucket
            HAVING TotalGames >= 25
        )
        SELECT 
            t.EloBucket,
            g.ResultLabel,
            (COUNT(*) * 100.0 / t.TotalGames) as WinRate,
            t.TotalGames as GameVolume
        FROM '{GOLD_DATA}' g
        JOIN BracketTotals t ON CAST(round((g.WhiteElo + g.BlackElo) / 2.0 / 100) * 100 AS INT) = t.EloBucket
        WHERE g.BaseOpening = '{safe_opening}'
        GROUP BY t.EloBucket, g.ResultLabel, t.TotalGames
        ORDER BY t.EloBucket
    """
    return duckdb.sql(query).pl()