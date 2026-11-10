# -*- coding: utf-8 -*-
"""公共模块：路径、Spark 会话、MySQL 写入、结果导出等工具。"""
import os
import sys
import json

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '8')  # 避免 joblib 在部分 Windows 上的核心数告警

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from pyspark.sql import SparkSession, functions as F

# ---------------- 路径 ----------------
ROOT = r'D:\dev\projects\taobao-analysis'
DATA_CSV   = os.path.join(ROOT, 'data', 'UserBehavior.csv')        # 100 万行正式数据
DATA_SMALL = os.path.join(ROOT, 'data', 'UserBehavior_small.csv')  # 10 万行快速测试
OUT_TABLES = os.path.join(ROOT, 'outputs', 'tables')
OUT_FIG    = os.path.join(ROOT, 'outputs', 'figures')
PARQUET    = os.path.join(ROOT, 'outputs', 'parquet', 'clean')
JDBC_JAR   = r'D:\dev\jars\mysql-connector-java-8.0.30.jar'

# ---------------- MySQL ----------------
MYSQL_URL = ('jdbc:mysql://localhost:3306/taobao_analysis?useSSL=false'
             '&characterEncoding=utf8&serverTimezone=Asia/Shanghai'
             '&allowPublicKeyRetrieval=true&rewriteBatchedStatements=true')
MYSQL_PROPS = {'user': 'root', 'password': 'CHANGE_ME', 'driver': 'com.mysql.cj.jdbc.Driver'}

# ---------------- 业务常量 ----------------
BEHAVIOR_CN = {'pv': '浏览', 'cart': '加购', 'fav': '收藏', 'buy': '购买'}
BEHAVIOR_ORDER = ['pv', 'fav', 'cart', 'buy']
# 官方数据采集窗口
WIN_START = '2017-11-25'
WIN_END   = '2017-12-03'

for d in (OUT_TABLES, OUT_FIG):
    os.makedirs(d, exist_ok=True)


def build_spark(app='TaobaoAnalysis', master='local[*]'):
    spark = (SparkSession.builder
             .appName(app).master(master)
             .config('spark.sql.session.timeZone', 'Asia/Shanghai')
             .config('spark.sql.legacy.timeParserPolicy', 'LEGACY')
             .config('spark.sql.shuffle.partitions', '8')
             .config('spark.jars', JDBC_JAR)
             .config('spark.driver.extraJavaOptions', '-Dfile.encoding=UTF-8')
             .getOrCreate())
    spark.sparkContext.setLogLevel('WARN')
    return spark


def save_result(df, name, coalesce=1):
    """聚合结果统一导出为 CSV(utf-8-sig) + JSON，并返回 pandas DataFrame。"""
    pdf = df.toPandas()
    csv_path = os.path.join(OUT_TABLES, name + '.csv')
    json_path = os.path.join(OUT_TABLES, name + '.json')
    pdf.to_csv(csv_path, index=False, encoding='utf-8-sig')
    pdf.to_json(json_path, orient='records', force_ascii=False, indent=1)
    print('[save] %s -> %d rows' % (name, len(pdf)))
    return pdf


def write_mysql(df, table, mode='overwrite'):
    (df.write.format('jdbc')
       .option('url', MYSQL_URL).option('dbtable', table)
       .options(**MYSQL_PROPS).option('batchsize', '5000')
       .mode(mode).save())
    print('[mysql] table %s %s, partitions=%d' % (table, mode, df.rdd.getNumPartitions()))


def add_time_dims(df):
    """由秒级时间戳派生北京时间的日期、小时、星期(1=周一..7=周日)。"""
    df = df.withColumn('event_time', F.from_unixtime(F.col('ts')).cast('timestamp'))
    df = df.withColumn('date', F.to_date('event_time'))
    df = df.withColumn('hour', F.hour('event_time'))
    # pmod(datediff(date, 1970-01-05),7): 0=Monday ... 6=Sunday
    df = df.withColumn('weekday', (F.pmod(F.datediff('date', F.lit('1970-01-05')), F.lit(7)) + 1))
    cn = F.create_map([x for kv in BEHAVIOR_CN.items() for x in (F.lit(kv[0]), F.lit(kv[1]))])
    df = df.withColumn('behavior_cn', cn[F.col('behavior_type')])
    return df
