# -*- coding: utf-8 -*-
import sys
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("DataAnalysis")
         .master("local[*]")
         .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
         .config("spark.sql.shuffle.partitions", "4")
         .getOrCreate())
spark.sparkContext.setLogLevel("WARN")
print(">>> Spark version:", spark.version)
print(">>> Python:", sys.version)
df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])
df.show()
cnt = df.count()
print(">>> row count =", cnt)
spark.stop()
print(">>> SPARK_ENV_OK")
