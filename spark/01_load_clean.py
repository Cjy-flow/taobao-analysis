# -*- coding: utf-8 -*-
"""
01 数据加载与清洗
- 读取无表头 CSV：user_id,item_id,category_id,behavior_type,ts(秒级)
- 类型转换、派生北京时间维度（date/hour/weekday/behavior_cn）
- 清洗：合法行为、非空、限定官方采集窗口、去重
- 缓存为 Parquet，并写入 MySQL 表 user_behavior
- 输出数据概览 overview
"""
import os
import json
from common import (build_spark, add_time_dims, save_result, write_mysql,
                    DATA_CSV, PARQUET, OUT_TABLES, WIN_START, WIN_END, BEHAVIOR_ORDER)
from pyspark.sql import functions as F

spark = build_spark('01_load_clean')

# ---------- 读取 ----------
raw = (spark.read.csv(DATA_CSV, header=False)
       .toDF('user_id', 'item_id', 'category_id', 'behavior_type', 'ts'))
n_raw = raw.count()
print('原始行数:', n_raw)

df = (raw.withColumn('user_id', F.col('user_id').cast('long'))
         .withColumn('item_id', F.col('item_id').cast('long'))
         .withColumn('category_id', F.col('category_id').cast('long'))
         .withColumn('ts', F.col('ts').cast('long')))
df = add_time_dims(df)

# ---------- 清洗 ----------
n_nonnull = df.dropna(subset=['user_id', 'item_id', 'category_id', 'ts']).count()
step1 = df.filter(F.col('behavior_type').isin(*BEHAVIOR_ORDER))
n_validbeh = step1.count()
step2 = step1.filter((F.col('date') >= F.lit(WIN_START)) & (F.col('date') <= F.lit(WIN_END)))
n_inwindow = step2.count()
clean = step2.dropDuplicates(['user_id', 'item_id', 'category_id', 'behavior_type', 'ts'])
n_clean = clean.count()
print('非空行:%d  合法行为:%d  窗口内:%d  去重后:%d' % (n_nonnull, n_validbeh, n_inwindow, n_clean))
print('剔除噪声/重复行: %d (%.4f%%)' % (n_raw - n_clean, 100 * (n_raw - n_clean) / n_raw))

# 缓存顺序：行为类型、日期、小时、星期
clean = clean.select('user_id', 'item_id', 'category_id', 'behavior_type',
                     'behavior_cn', 'ts', 'event_time', 'date', 'hour', 'weekday')
clean.cache()
n_clean = clean.count()

# ---------- 写 Parquet ----------
clean.write.mode('overwrite').parquet(PARQUET)
print('parquet written ->', PARQUET)

# ---------- 写 MySQL ----------
write_mysql(clean, 'user_behavior', mode='overwrite')

# ---------- 数据概览 ----------
overview = {
    'raw_rows': n_raw,
    'clean_rows': n_clean,
    'dropped_rows': n_raw - n_clean,
    'n_users': clean.select('user_id').distinct().count(),
    'n_items': clean.select('item_id').distinct().count(),
    'n_categories': clean.select('category_id').distinct().count(),
    'date_start': str(clean.agg(F.min('date')).first()[0]),
    'date_end': str(clean.agg(F.max('date')).first()[0]),
}
beh = (clean.groupBy('behavior_type', 'behavior_cn').count()
       .orderBy(F.col('behavior_type')))
beh_pdf = beh.toPandas()
overview['behavior_dist'] = {r['behavior_type']: int(r['count']) for _, r in beh_pdf.iterrows()}
print(json.dumps(overview, ensure_ascii=False, indent=2))
with open(os.path.join(OUT_TABLES, 'overview.json'), 'w', encoding='utf-8') as f:
    json.dump(overview, f, ensure_ascii=False, indent=2)
save_result(beh, 'behavior_dist')

# 每日总量（后续常用，顺带落地）
daily = (clean.groupBy('date').agg(
    F.count('*').alias('cnt'),
    F.sum(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('pv'),
    F.sum(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('fav'),
    F.sum(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('cart'),
    F.sum(F.when(F.col('behavior_type') == 'buy', 1).otherwise(0)).alias('buy'),
).orderBy('date'))
save_result(daily, 'daily_overview')
write_mysql(daily, 'daily_overview', mode='overwrite')

spark.stop()
print('01 LOAD_CLEAN DONE')
