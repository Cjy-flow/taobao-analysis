# -*- coding: utf-8 -*-
"""
02 行为模式统计分析（对应指导书 课程任务(一) 前 5 项）
1) 2017-11 月每天的访问量及每天累计访问量
2) 2017-11/12 月每天购买量、全局累计与当月累计购买量
3) 2017-11 月购买商品品类数的用户排名
4) 购买数量前 30% 的用户
5) 购买时间间隔超过 5 天的用户数
"""
import math
from common import build_spark, save_result, write_mysql, PARQUET
from pyspark.sql import functions as F

spark = build_spark('02_behavior_stats')
df = spark.read.parquet(PARQUET)
df.createOrReplaceTempView('behavior')
metrics = []  # (metric, value, note)

def keep_metric(k, v, note=''):
    metrics.append((k, float(v), note))
    print('[metric] %s = %s %s' % (k, v, note))

# ---------- 任务1：11月每日访问量 + 累计访问量 ----------
q1 = spark.sql('''
SELECT date,
       COUNT(*) AS pv_cnt,
       SUM(COUNT(*)) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cum_pv
FROM behavior
WHERE behavior_type='pv' AND date BETWEEN '2017-11-01' AND '2017-11-30'
GROUP BY date ORDER BY date
''')
t1 = save_result(q1, 'stat_nov_pv_cum')
write_mysql(q1, 'stat_nov_pv_cum')
keep_metric('nov_total_pv', int(t1['pv_cnt'].sum()), '11月(11-25~30)累计访问量')

# ---------- 任务2：11/12月每日购买量 + 全局累计 + 当月累计 ----------
q2 = spark.sql('''
SELECT date, ym, buy_cnt,
       SUM(buy_cnt) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS total_cum_buy,
       SUM(buy_cnt) OVER (PARTITION BY ym ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS month_cum_buy
FROM (
  SELECT date, DATE_FORMAT(date,'yyyy-MM') AS ym, COUNT(*) AS buy_cnt
  FROM behavior WHERE behavior_type='buy' GROUP BY date
) ORDER BY date
''')
t2 = save_result(q2, 'stat_buy_cum')
write_mysql(q2, 'stat_buy_cum')
keep_metric('total_buy', int(t2['buy_cnt'].sum()), '全周期累计购买量')

# ---------- 任务3：11月购买商品品类数的用户排名 ----------
q3 = spark.sql('''
SELECT user_id, n_category,
       DENSE_RANK() OVER (ORDER BY n_category DESC) AS dense_rk,
       ROW_NUMBER() OVER (ORDER BY n_category DESC, user_id) AS rn
FROM (
  SELECT user_id, COUNT(DISTINCT category_id) AS n_category
  FROM behavior
  WHERE behavior_type='buy' AND date BETWEEN '2017-11-01' AND '2017-11-30'
  GROUP BY user_id
) ORDER BY n_category DESC, user_id
''')
t3 = save_result(q3, 'stat_nov_user_category_rank')
write_mysql(q3, 'stat_nov_user_category_rank')
keep_metric('nov_buy_users', len(t3), '11月有购买行为的用户数')
keep_metric('nov_max_category', int(t3['n_category'].max()), '11月单用户最多购买品类数')

# ---------- 任务4：购买数量前30%的用户 ----------
ub = spark.sql('''
SELECT user_id, n_buy,
       ROW_NUMBER() OVER (ORDER BY n_buy DESC, user_id) AS rn,
       PERCENT_RANK() OVER (ORDER BY n_buy DESC) AS pr
FROM (SELECT user_id, COUNT(*) AS n_buy FROM behavior WHERE behavior_type='buy' GROUP BY user_id)
''')
n_buy_users = ub.count()
total_buy_all = ub.agg(F.sum('n_buy')).first()[0]
top_n = math.ceil(n_buy_users * 0.3)
q4 = ub.where(F.col('rn') <= top_n).orderBy(F.col('rn'))
t4 = save_result(q4, 'stat_top30_buy_users')
write_mysql(q4, 'stat_top30_buy_users')
threshold_buy = int(t4['n_buy'].min())
keep_metric('buy_user_total', n_buy_users, '有购买行为的用户总数')
keep_metric('top30_user_count', len(t4), '购买量前30%用户数')
keep_metric('top30_threshold_buy', threshold_buy, '前30%用户的最低购买次数')
keep_metric('top30_buy_share', round(100.0*t4['n_buy'].sum()/total_buy_all, 2), '前30%用户贡献购买量占比%')

# ---------- 任务5：购买时间间隔超过5天的用户数 ----------
gap = spark.sql('''
SELECT user_id,
       DATEDIFF(date, LAG(date) OVER (PARTITION BY user_id ORDER BY date)) AS gap_days
FROM (SELECT DISTINCT user_id, date FROM behavior WHERE behavior_type='buy')
''')
gap.createOrReplaceTempView('gap')
user_gap = spark.sql('''
SELECT user_id, MAX(gap_days) AS max_gap, COUNT(*) AS n_gap
FROM gap WHERE gap_days IS NOT NULL GROUP BY user_id
''')
# 间隔分布
gap_dist = user_gap.select('max_gap').groupBy('max_gap').count().orderBy('max_gap')
save_result(gap_dist, 'stat_buy_gap_dist')
write_mysql(gap_dist, 'stat_buy_gap_dist')
over5 = user_gap.where(F.col('max_gap') > 5)
n_over5 = over5.count()
n_multi = user_gap.count()
save_result(over5.orderBy(F.col('max_gap').desc()), 'stat_buy_gap_over5')
write_mysql(over5.orderBy(F.col('max_gap').desc()), 'stat_buy_gap_over5')
keep_metric('multi_buy_users', n_multi, '购买>=2次(可算间隔)的用户数')
keep_metric('gap_over5_users', n_over5, '相邻购买间隔超过5天的用户数')
keep_metric('gap_over5_ratio', round(100.0*n_over5/n_multi, 2), '占多次购买用户比例%')

# ---------- 指标汇总入库 ----------
mdf = spark.createDataFrame(metrics, ['metric', 'value', 'note'])
save_result(mdf.orderBy('metric'), 'analysis_metrics_02')
write_mysql(mdf, 'analysis_metrics', mode='overwrite')  # 02 初始化指标汇总表，后续脚本 append
mdf.show(50, truncate=False)
spark.stop()
print('02 BEHAVIOR_STATS DONE')
