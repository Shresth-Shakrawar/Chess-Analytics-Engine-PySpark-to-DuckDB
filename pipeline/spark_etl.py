import os

# 1. Force PySpark to use OpenJDK 21 for this script only
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-21-openjdk"
# Optional but good practice: Ensure the PySpark driver uses the same Python as your venv
os.environ["PYSPARK_PYTHON"] = "python" 

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, split, when

def run_etl():
    print(f"Using Java Home: {os.environ.get('JAVA_HOME')}")
    print("Initializing PySpark Session...")
    
    spark = SparkSession.builder \
        .appName("ChessAnalyticsPipeline") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()

    # 2. Read the Bronze dataset
    print("Reading bronze dataset...")
    df = spark.read.parquet("data/bronze_games.parquet")

    # 3. Clean and Transform
    print("Applying transformations...")
    clean_df = df \
        .filter((col("WhiteElo") != "?") & (col("BlackElo") != "?")) \
        .filter(col("WhiteElo").isNotNull() & col("BlackElo").isNotNull()) \
        .withColumn("WhiteElo", col("WhiteElo").cast("integer")) \
        .withColumn("BlackElo", col("BlackElo").cast("integer")) \
        .withColumn("EloDiff", col("WhiteElo") - col("BlackElo")) \
        .withColumn("BaseOpening", split(col("Opening"), ":")[0]) \
        .withColumn("ResultLabel", 
                    when(col("Result") == "1-0", "White Win")
                    .when(col("Result") == "0-1", "Black Win")
                    .otherwise("Draw"))

    # 4. Write the Gold dataset
    output_path = "data/gold_games.parquet"
    print(f"Writing optimized data to {output_path}...")
    
    # coalesce(1) forces it into a single parquet file for easier DuckDB reading
    clean_df.coalesce(1).write.mode("overwrite").parquet(output_path)
    
    print("ETL Complete! Gold dataset is ready.")
    spark.stop()

if __name__ == "__main__":
    run_etl()