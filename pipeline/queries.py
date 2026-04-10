import duckdb
import polars as pl

GOLD_DATA = "data/gold_games.parquet/*.parquet"


def get_kpis(min_elo, max_elo):
    query = f"""
        SELECT 
            COUNT(*)::INT as total_games,
            AVG((WhiteElo + BlackElo) / 2.0)::INT as avg_elo,
            (SUM(CASE WHEN ResultLabel = 'White Win' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) as white_win_rate,
            (SUM(CASE WHEN ResultLabel = 'Draw' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)) as draw_rate,
            AVG(ABS(EloDiff))::INT as avg_elo_diff
        FROM '{GOLD_DATA}' 
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo} 
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
    """
    res = duckdb.sql(query).fetchone()

    q_pop = f"""
        SELECT BaseOpening FROM '{GOLD_DATA}' 
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
        GROUP BY BaseOpening ORDER BY COUNT(*) DESC LIMIT 1
    """
    pop_res = duckdb.sql(q_pop).fetchone()

    return {
        "total_games":    res[0]     if res and res[0] is not None else 0,
        "avg_elo":        res[1]     if res and res[1] is not None else 0,
        "white_win_rate": res[2]     if res and res[2] is not None else 0.0,
        "draw_rate":      res[3]     if res and res[3] is not None else 0.0,
        "avg_elo_diff":   res[4]     if res and res[4] is not None else 0,
        "top_opening":    pop_res[0] if pop_res and pop_res[0] is not None else "N/A",
    }


def get_opening_efficacy(min_elo, max_elo, limit=10):
    query = f"""
        WITH TopOpenings AS (
            SELECT BaseOpening FROM '{GOLD_DATA}'
            WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
              AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
            GROUP BY BaseOpening ORDER BY COUNT(*) DESC LIMIT {limit}
        )
        SELECT BaseOpening, ResultLabel, COUNT(*)::INT as count
        FROM '{GOLD_DATA}'
        WHERE BaseOpening IN (SELECT BaseOpening FROM TopOpenings)
          AND WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
        GROUP BY BaseOpening, ResultLabel
    """
    return duckdb.sql(query).pl()


def get_draw_rate_trend():
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

def get_popular_openings(min_elo=800, max_elo=2800):
    query = f"""
        SELECT BaseOpening 
        FROM '{GOLD_DATA}' 
        WHERE WhiteElo >= {min_elo} AND WhiteElo <= {max_elo}
        GROUP BY BaseOpening 
        HAVING COUNT(*) > 500 
        ORDER BY COUNT(*) DESC
    """
    return duckdb.sql(query).pl()['BaseOpening'].to_list()
    
def get_opening_win_rate_by_elo(opening_name):
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


def get_elo_gap_win_rate(min_elo, max_elo):
    """Line chart: White win rate and draw rate bucketed by EloDiff (PySpark column)."""
    query = f"""
        SELECT
            CAST(round(EloDiff / 50.0) * 50 AS INT) as EloDiffBucket,
            (SUM(CASE WHEN ResultLabel = 'White Win' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as WhiteWinRate,
            (SUM(CASE WHEN ResultLabel = 'Draw'      THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as DrawRate,
            COUNT(*)::INT as GameVolume
        FROM '{GOLD_DATA}'
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
          AND ABS(EloDiff) <= 500
        GROUP BY EloDiffBucket
        HAVING GameVolume > 100
        ORDER BY EloDiffBucket
    """
    return duckdb.sql(query).pl()


def get_elodiff_distribution(min_elo, max_elo):
    """
    Histogram of EloDiff — a column computed by PySpark ETL.
    Shows whether games are evenly matched or heavily skewed.
    """
    query = f"""
        SELECT
            CAST(round(EloDiff / 25.0) * 25 AS INT) as EloDiffBucket,
            COUNT(*)::INT as GameCount
        FROM '{GOLD_DATA}'
        WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
          AND ABS(EloDiff) <= 600
        GROUP BY EloDiffBucket
        ORDER BY EloDiffBucket
    """
    return duckdb.sql(query).pl()


def get_opening_avg_elodiff(min_elo, max_elo, limit=12):
    """
    Horizontal bar: avg absolute EloDiff per opening (top 12 by volume).
    Showcases the PySpark-derived EloDiff column meaningfully.
    """
    query = f"""
        WITH TopOpenings AS (
            SELECT BaseOpening FROM '{GOLD_DATA}'
            WHERE WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
              AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
            GROUP BY BaseOpening ORDER BY COUNT(*) DESC LIMIT {limit}
        )
        SELECT
            BaseOpening,
            AVG(ABS(EloDiff)) as AvgEloDiff,
            COUNT(*)::INT     as GameCount
        FROM '{GOLD_DATA}'
        WHERE BaseOpening IN (SELECT BaseOpening FROM TopOpenings)
          AND WhiteElo >= {min_elo} AND BlackElo >= {min_elo}
          AND WhiteElo <= {max_elo} AND BlackElo <= {max_elo}
        GROUP BY BaseOpening
        ORDER BY AvgEloDiff DESC
    """
    return duckdb.sql(query).pl()


def get_elo_distribution(min_elo, max_elo):
    """Overlapping histogram: Elo distribution for White vs Black players."""
    query = f"""
        SELECT EloBucket, Side, COUNT(*)::INT as PlayerCount
        FROM (
            SELECT CAST(round(WhiteElo / 100.0) * 100 AS INT) as EloBucket, 'White' as Side
            FROM '{GOLD_DATA}'
            WHERE WhiteElo >= {min_elo} AND WhiteElo <= {max_elo}
            UNION ALL
            SELECT CAST(round(BlackElo / 100.0) * 100 AS INT) as EloBucket, 'Black' as Side
            FROM '{GOLD_DATA}'
            WHERE BlackElo >= {min_elo} AND BlackElo <= {max_elo}
        )
        GROUP BY EloBucket, Side
        ORDER BY EloBucket
    """
    return duckdb.sql(query).pl()