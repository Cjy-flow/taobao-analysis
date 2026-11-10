# -*- coding: utf-8 -*-
"""
06 协同过滤推荐（Spark MLlib ALS，隐式反馈）
- 行为加权构造用户-商品偏好：pv=1,fav=3,cart=4,buy=5，同一用户-商品聚合后截断到[0,10]
- 训练/测试 8:2 划分，RankingMetrics 评估 Precision@10/Recall@10/NDCG@10
- recommendForAllUsers 生成每用户 Top10；冷启动(无历史)用户以全局热门兜底
- 保存 ALS 模型，输出示例推荐与热门兜底商品
"""
import os
import shutil
import pandas as pd
from common import build_spark, save_result, write_mysql, PARQUET, ROOT
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType
from pyspark.ml.recommendation import ALS
from pyspark.mllib.evaluation import RankingMetrics

MODEL_DIR = os.path.join(ROOT, 'outputs', 'models', 'als_model')
spark = build_spark('06_als_recommend')
df = spark.read.parquet(PARQUET)

# ---------- 行为加权偏好 ----------
w = (F.when(F.col('behavior_type') == 'pv', 1)
      .when(F.col('behavior_type') == 'fav', 3)
      .when(F.col('behavior_type') == 'cart', 4)
      .when(F.col('behavior_type') == 'buy', 5).otherwise(1))
inter = (df.withColumn('w', w)
           .groupBy('user_id', 'item_id').agg(F.sum('w').alias('raw'))
           .withColumn('rating', F.least(F.col('raw'), F.lit(10)).cast('float'))
           .withColumn('user_id', F.col('user_id').cast('int'))
           .withColumn('item_id', F.col('item_id').cast('int'))
           .filter(F.col('item_id').isNotNull()))
# 过滤长尾：保留交互次数>=2 的商品，降低维度与噪声
item_cnt = inter.groupBy('item_id').count().withColumnRenamed('count', 'ic')
inter = inter.join(item_cnt, 'item_id').filter(F.col('ic') >= 2).drop('ic')
inter.cache()
print('交互三元组:', inter.count(), ' 用户:', inter.select('user_id').distinct().count(),
      ' 商品:', inter.select('item_id').distinct().count())

train, test = inter.randomSplit([0.8, 0.2], seed=42)
als = ALS(rank=12, maxIter=12, regParam=0.06, alpha=1.0, nonnegative=True,
          implicitPrefs=True, coldStartStrategy='drop',
          userCol='user_id', itemCol='item_id', ratingCol='rating', seed=42)
model = als.fit(train)

# ---------- 排序评估 ----------
K = 10
rec_all = model.recommendForAllUsers(K).select('user_id', F.col('recommendations.item_id').alias('pred'))
true = (test.groupBy('user_id').agg(F.collect_set('item_id').alias('true')))
joined = (rec_all.join(true, 'user_id').rdd.map(lambda r: (list(r.pred), list(r.true))))
rm = RankingMetrics(joined)
eval_metrics = {
    'precision@10': round(float(rm.precisionAt(K)), 4),
    'recall@10': round(float(rm.recallAt(K)), 4),
    'ndcg@10': round(float(rm.ndcgAt(K)), 4),
    'map': round(float(rm.meanAveragePrecision), 4),
}
print('ALS 评估:', eval_metrics)

# ---------- 全量重训 + 每用户 Top10 推荐 ----------
full_model = als.fit(inter)
recs = full_model.recommendForAllUsers(K)
rec_flat = recs.selectExpr('user_id', 'posexplode(recommendations) as (pos, rec)') \
    .selectExpr('user_id', 'pos+1 as rank', 'rec.item_id as item_id', 'round(rec.rating,4) as score')
# 附带商品自身热度，便于前端卡片展示
item_info = (df.groupBy('item_id').agg(
    F.count('*').alias('i_pv'),
    F.sum(F.when(F.col('behavior_type') == 'buy', 1).otherwise(0)).alias('i_buy'),
    F.first('category_id').alias('category_id'))
    .withColumn('item_id', F.col('item_id').cast('int')))
rec_out = rec_flat.join(item_info, 'item_id', 'left').orderBy('user_id', 'rank')
save_result(rec_out.limit(5000), 'als_user_recs')   # 落库前5000条便于查看，全量另存
write_mysql(rec_out.limit(5000), 'als_user_recs')
rec_out.toPandas().to_csv(os.path.join(ROOT, 'outputs', 'tables', 'als_user_recs_full.csv'),
                          index=False, encoding='utf-8-sig')

# ---------- 热门兜底（冷启动策略） ----------
popular = (df.groupBy('item_id').agg(
    F.count('*').alias('hot'),
    F.sum(F.when(F.col('behavior_type') == 'buy', 1).otherwise(0)).alias('buy'),
    F.first('category_id').alias('category_id'))
    .orderBy(F.desc('hot')).limit(10))
save_result(popular, 'als_popular_items')
write_mysql(popular, 'als_popular_items')

# 冷启动统计：无任何交互的用户数（演示冷启动规模，用热门兜底）
n_users_total = df.select('user_id').distinct().count()
n_users_seen = inter.select('user_id').distinct().count()
cold = n_users_total - n_users_seen
mdf = spark.createDataFrame([
    ('als_precision_at10', eval_metrics['precision@10'], 'ALS Top10精确率'),
    ('als_recall_at10', eval_metrics['recall@10'], 'ALS Top10召回率'),
    ('als_ndcg_at10', eval_metrics['ndcg@10'], 'ALS NDCG@10'),
    ('als_map', eval_metrics['map'], '平均精度均值'),
    ('als_coldstart_users', float(cold), '冷启动用户数(热门兜底)'),
], ['metric', 'value', 'note'])
save_result(mdf, 'als_metrics')
write_mysql(mdf, 'als_metrics')
write_mysql(mdf.select('metric', 'value', 'note'), 'analysis_metrics', mode='append')

# 保存模型
if os.path.exists(MODEL_DIR):
    shutil.rmtree(MODEL_DIR, ignore_errors=True)
full_model.write().overwrite().save(MODEL_DIR)
print('示例用户推荐:'); rec_out.show(12)
print('冷启动用户数:', cold)
spark.stop()
print('06 ALS DONE')
