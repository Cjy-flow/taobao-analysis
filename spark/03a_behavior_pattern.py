# -*- coding: utf-8 -*-
"""
03a 行为模式分析（指导书 行为模式分析 输入块1、3、4）
- 各行为类型(PV/FAV/CART/BUY)分布比例（环形图数据）
- 用户活跃时段：小时级、星期级、小时×星期热力矩阵
- 用户购买日期：本次购买时间与上次购买时间(lag)
- 浏览量Top10商品及其购买次数；购买量Top10商品及其浏览量
"""
from common import build_spark, save_result, write_mysql, PARQUET
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = build_spark('03a_behavior_pattern')
df = spark.read.parquet(PARQUET)
df.createOrReplaceTempView('behavior')
total = df.count()

# ---------- 1. 行为类型分布比例 ----------
ratio = spark.sql('''
SELECT behavior_type, behavior_cn, COUNT(*) AS cnt,
       ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (), 3) AS ratio_pct
FROM behavior GROUP BY behavior_type, behavior_cn
ORDER BY cnt DESC
''')
save_result(ratio, 'bp_behavior_ratio')
write_mysql(ratio, 'bp_behavior_ratio')

# ---------- 2a. 按小时（分行为） ----------
hour_df = spark.sql('''
SELECT hour,
  SUM(IF(behavior_type='pv',1,0))  AS pv,
  SUM(IF(behavior_type='fav',1,0)) AS fav,
  SUM(IF(behavior_type='cart',1,0)) AS cart,
  SUM(IF(behavior_type='buy',1,0)) AS buy,
  COUNT(*) AS cnt
FROM behavior GROUP BY hour ORDER BY hour
''')
save_result(hour_df, 'bp_hour')
write_mysql(hour_df, 'bp_hour')

# ---------- 2b. 小时×星期 热力矩阵 ----------
heat = spark.sql('''
SELECT weekday, hour, COUNT(*) AS cnt
FROM behavior GROUP BY weekday, hour ORDER BY weekday, hour
''')
save_result(heat, 'bp_hour_weekday')
write_mysql(heat, 'bp_hour_weekday')

# ---------- 2c. 按星期的日均行为量 ----------
# 9 天窗口中各 weekday 出现的天数不同，需除以天数得到“日均”
wd_days = (df.select('date', 'weekday').distinct()
             .groupBy('weekday').agg(F.count('*').alias('ndays')))
wd = (df.groupBy('weekday')
        .agg(F.count('*').alias('total_cnt'),
             F.sum(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('pv'),
             F.sum(F.when(F.col('behavior_type') == 'buy', 1).otherwise(0)).alias('buy'))
        .join(wd_days, 'weekday')
        .withColumn('avg_cnt', F.round(F.col('total_cnt') / F.col('ndays'), 1))
        .withColumn('avg_pv', F.round(F.col('pv') / F.col('ndays'), 1))
        .withColumn('avg_buy', F.round(F.col('buy') / F.col('ndays'), 1))
        .orderBy('weekday'))
wd_cn = F.create_map([F.lit(1), F.lit('周一'), F.lit(2), F.lit('周二'), F.lit(3), F.lit('周三'),
                      F.lit(4), F.lit('周四'), F.lit(5), F.lit('周五'), F.lit(6), F.lit('周六'),
                      F.lit(7), F.lit('周日')])
wd = wd.withColumn('weekday_cn', wd_cn[F.col('weekday')])
save_result(wd, 'bp_weekday_avg')
write_mysql(wd, 'bp_weekday_avg')

# ---------- 3. 用户本次/上次购买时间对照 ----------
w = Window.partitionBy('user_id').orderBy('event_time')
buy = (df.filter(F.col('behavior_type') == 'buy')
         .select('user_id', 'item_id', 'category_id', 'event_time', 'ts')
         .withColumn('prev_time', F.lag('event_time').over(w))
         .withColumn('gap_days', F.datediff('event_time', 'prev_time'))
         .withColumnRenamed('event_time', 'buy_time')
         .orderBy('user_id', 'buy_time'))
save_result(buy, 'bp_user_purchase_lag')
write_mysql(buy, 'bp_user_purchase_lag')

# ---------- 4. 商品浏览/购买交叉 Top10 ----------
item = spark.sql('''
SELECT item_id,
  SUM(IF(behavior_type='pv',1,0))  AS pv,
  SUM(IF(behavior_type='fav',1,0)) AS fav,
  SUM(IF(behavior_type='cart',1,0)) AS cart,
  SUM(IF(behavior_type='buy',1,0)) AS buy,
  COUNT(*) AS cnt
FROM behavior GROUP BY item_id
''')
item.cache()
top_pv = item.orderBy(F.desc('pv')).limit(10).withColumn('rank_by_pv', F.row_number().over(Window.orderBy(F.desc('pv'))))
top_buy = item.orderBy(F.desc('buy'), F.desc('pv')).limit(10).withColumn('rank_by_buy', F.row_number().over(Window.orderBy(F.desc('buy'), F.desc('pv'))))
save_result(top_pv.orderBy('rank_by_pv'), 'bp_top10_pv_items')
write_mysql(top_pv, 'bp_top10_pv_items')
save_result(top_buy.orderBy('rank_by_buy'), 'bp_top10_buy_items')
write_mysql(top_buy, 'bp_top10_buy_items')

print('behavior ratio:'); ratio.show()
print('weekday avg:'); wd.orderBy('weekday').show()
spark.stop()
print('03A BEHAVIOR_PATTERN DONE')
