# -*- coding: utf-8 -*-
"""
04 RFM 模型与用户分群（指导书 任务(二)）
- Recency：最近一次购买距基准日(窗口结束次日 2017-12-04)的天数，越小越好
- Frequency：统计周期内购买次数，越大越好
- Monetary 代理：数据集无订单金额，以“购买不同商品数”衡量消费丰富度，越大越好
- 五分位评分(1~5)；K-Means 聚为 3 类并映射高/中/低价值标签与运营策略；另给经典八分法
"""
import numpy as np
import pandas as pd
from common import build_spark, save_result, write_mysql, PARQUET
from pyspark.sql import functions as F
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

spark = build_spark('04_rfm')
df = spark.read.parquet(PARQUET)

# ---------- Spark SQL 聚合 R/F/M ----------
rfm_sdf = (df.filter(F.col('behavior_type') == 'buy')
    .groupBy('user_id').agg(
        F.datediff(F.lit('2017-12-04'), F.max('date')).alias('recency'),
        F.count('*').alias('frequency'),
        F.countDistinct('item_id').alias('monetary')))
rfm = rfm_sdf.toPandas()
print('RFM 用户数:', len(rfm))

# ---------- 五分位评分 ----------
def quintile_score(s, ascending=True):
    # ascending=True: 值越大分越高(F/M)；False: 值越小分越高(R)
    q = s.quantile([.2, .4, .6, .8]).values
    def sc(x):
        if ascending:
            return 1 + int(x > q[0]) + int(x > q[1]) + int(x > q[2]) + int(x > q[3])
        else:
            return 1 + int(x < q[3]) + int(x < q[2]) + int(x < q[1]) + int(x < q[0])
    return s.map(sc)
rfm['r_score'] = quintile_score(rfm['recency'], ascending=False)
rfm['f_score'] = quintile_score(rfm['frequency'], ascending=True)
rfm['m_score'] = quintile_score(rfm['monetary'], ascending=True)
rfm['rfm_sum'] = rfm['r_score'] + rfm['f_score'] + rfm['m_score']

# ---------- K-Means 聚类 ----------
X = StandardScaler().fit_transform(rfm[['recency', 'frequency', 'monetary']].astype(float))
sil = {}
for k in range(2, 7):
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    sil[k] = round(silhouette_score(X, km.labels_), 4)
print('不同k的轮廓系数:', sil)
k = 3  # 指导书要求三类用户价值标签
km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
rfm['cluster'] = km.labels_

# 依据簇中心综合价值(-R+F+M，标准化量纲)排序，映射价值标签
raw_mean = rfm.groupby('cluster')[['recency', 'frequency', 'monetary']].mean()
z = pd.DataFrame(StandardScaler().fit_transform(raw_mean.values),
                 index=raw_mean.index, columns=['rz', 'fz', 'mz'])
z['value'] = -z['rz'] + z['fz'] + z['mz']
rank = z['value'].sort_values(ascending=False)
label_map = {rank.index[0]: '高价值客户', rank.index[1]: '一般维持客户', rank.index[2]: '低价值/流失客户'}
strategy = {
    '高价值客户': '重点维护，VIP专属权益与新品优先推荐，提升复购与客单',
    '一般维持客户': '通过优惠券、加购/收藏召回提升活跃度与转化，引导向上成长',
    '低价值/流失客户': '流失预警与唤醒，推送促销触达，控制营销成本',
}
rfm['segment'] = rfm['cluster'].map(label_map)
rfm['strategy'] = rfm['segment'].map(strategy)

# ---------- 簇汇总 ----------
summary = (rfm.groupby(['cluster', 'segment', 'strategy'])
           .agg(users=('user_id', 'count'),
                recency_avg=('recency', 'mean'), frequency_avg=('frequency', 'mean'),
                monetary_avg=('monetary', 'mean'),
                r_avg=('r_score', 'mean'), f_avg=('f_score', 'mean'), m_avg=('m_score', 'mean'))
           .reset_index())
summary['ratio_pct'] = (100 * summary['users'] / len(rfm)).round(2)
for c in ['recency_avg', 'frequency_avg', 'monetary_avg', 'r_avg', 'f_avg', 'm_avg']:
    summary[c] = summary[c].round(2)
summary = summary.sort_values('cluster')
print(summary)

# ---------- 经典 RFM 八分法 ----------
rm, fm, mm = rfm['r_score'].mean(), rfm['f_score'].mean(), rfm['m_score'].mean()
def octant(row):
    rh, fh, mh = row['r_score'] >= rm, row['f_score'] >= fm, row['m_score'] >= mm
    table = {
        (1,1,1): '重要价值客户', (1,0,1): '重要发展客户', (0,1,1): '重要保持客户', (0,0,1): '重要挽留客户',
        (1,1,0): '一般价值客户', (1,0,0): '一般发展客户', (0,1,0): '一般保持客户', (0,0,0): '一般挽留客户'}
    return table[(int(rh), int(fh), int(mh))]
rfm['octant'] = rfm.apply(octant, axis=1)
oct_summary = (rfm.groupby('octant').agg(users=('user_id', 'count')).reset_index())
oct_summary['ratio_pct'] = (100 * oct_summary['users'] / len(rfm)).round(2)
oct_summary = oct_summary.sort_values('users', ascending=False)
print(oct_summary)

# ---------- 输出 / 入库 ----------
detail_cols = ['user_id', 'recency', 'frequency', 'monetary', 'r_score', 'f_score', 'm_score',
               'rfm_sum', 'cluster', 'segment', 'strategy', 'octant']
detail = spark.createDataFrame(rfm[detail_cols])
save_result(detail, 'rfm_detail')
write_mysql(detail, 'rfm_detail')
sdf = spark.createDataFrame(summary)
save_result(sdf, 'rfm_cluster_summary')
write_mysql(sdf, 'rfm_cluster_summary')
osdf = spark.createDataFrame(oct_summary)
save_result(osdf, 'rfm_octant_summary')
write_mysql(osdf, 'rfm_octant_summary')

metrics = spark.createDataFrame([
    ('rfm_users', float(len(rfm)), '参与RFM分群的购买用户数'),
    ('rfm_silhouette_k3', float(sil[3]), 'KMeans k=3 轮廓系数'),
    ('rfm_best_k', float(max(sil, key=sil.get)), '轮廓系数最优k'),
    ('rfm_high_value_users', float(int((rfm.segment == "高价值客户").sum())), '高价值客户数'),
], ['metric', 'value', 'note'])
write_mysql(metrics, 'analysis_metrics', mode='append')
spark.stop()
print('04 RFM DONE')
