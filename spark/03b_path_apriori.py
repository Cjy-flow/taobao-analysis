# -*- coding: utf-8 -*-
"""
03b 点击流路径分析 + 商品类目关联规则(Apriori)
- 以“同一用户相邻行为间隔 >30 分钟”切分会话(session)
- 还原 浏览-购买 / 浏览-收藏-购买 / 浏览-加购-购买 / 浏览-加购-收藏-购买 / 浏览-流失
- 计算各路径会话数与转化率（漏斗/桑基图数据）
- 以(用户,天)为购物篮、热门类目为商品，Apriori 挖掘类目关联规则(support/confidence/lift)
"""
import pandas as pd
from common import build_spark, save_result, write_mysql, PARQUET
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = build_spark('03b_path_apriori')
df = spark.read.parquet(PARQUET)

# ============ 一、会话切分 ============
w = Window.partitionBy('user_id').orderBy('ts')
s = (df.orderBy('user_id', 'ts')
       .withColumn('prev_ts', F.lag('ts').over(w))
       .withColumn('is_new',
                   F.when(F.col('prev_ts').isNull() | ((F.col('ts') - F.col('prev_ts')) > 1800), 1)
                    .otherwise(0))
       .withColumn('sess_seq', F.sum('is_new').over(w.rowsBetween(Window.unboundedPreceding, Window.currentRow)))
       .withColumn('session_id', F.concat_ws('_', F.col('user_id').cast('string'), F.col('sess_seq').cast('string'))))

sess = (s.groupBy('session_id').agg(
    F.max(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('has_pv'),
    F.max(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('has_fav'),
    F.max(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('has_cart'),
    F.max(F.when(F.col('behavior_type') == 'buy', 1).otherwise(0)).alias('has_buy'),
    F.count('*').alias('n_action')))
sess.cache()
n_sess = sess.count()
n_pv = sess.filter('has_pv=1').count()

def cnt(cond):
    return sess.filter(cond).count()

funnel_rows = [
    ('有效会话', n_sess, 100.0),
    ('含浏览(pv)', cnt('has_pv=1'), round(100*cnt('has_pv=1')/n_sess, 3)),
    ('含收藏(fav)', cnt('has_fav=1'), round(100*cnt('has_fav=1')/n_sess, 3)),
    ('含加购(cart)', cnt('has_cart=1'), round(100*cnt('has_cart=1')/n_sess, 3)),
    ('含购买(buy)', cnt('has_buy=1'), round(100*cnt('has_buy=1')/n_sess, 3)),
]
funnel_pdf = pd.DataFrame(funnel_rows, columns=['stage', 'sessions', 'pct_of_all'])
# 路径转化率（相对进入该前置路径的会话）
pv_fav = cnt('has_pv=1 and has_fav=1')
pv_cart = cnt('has_pv=1 and has_cart=1')
pv_fav_cart = cnt('has_pv=1 and has_fav=1 and has_cart=1')
path_rows = [
    ('浏览-购买',        cnt('has_pv=1 and has_buy=1 and has_fav=0 and has_cart=0'), n_pv,    round(100*cnt('has_pv=1 and has_buy=1')/n_pv, 3)),
    ('浏览-收藏-购买',    cnt('has_pv=1 and has_fav=1 and has_buy=1 and has_cart=0'), pv_fav, round(100*cnt('has_pv=1 and has_fav=1 and has_buy=1')/max(pv_fav,1), 3)),
    ('浏览-加购-购买',    cnt('has_pv=1 and has_cart=1 and has_buy=1 and has_fav=0'), pv_cart, round(100*cnt('has_pv=1 and has_cart=1 and has_buy=1')/max(pv_cart,1), 3)),
    ('浏览-加购-收藏-购买', cnt('has_pv=1 and has_cart=1 and has_fav=1 and has_buy=1'), pv_fav_cart, round(100*cnt('has_pv=1 and has_cart=1 and has_fav=1 and has_buy=1')/max(pv_fav_cart,1), 3)),
    ('浏览-流失(未购买)', cnt('has_pv=1 and has_buy=0'), n_pv, round(100*cnt('has_pv=1 and has_buy=0')/n_pv, 3)),
]
path_pdf = pd.DataFrame(path_rows, columns=['path', 'sessions', 'base_sessions', 'conversion_pct'])
print('总会话数:', n_sess); print(funnel_pdf); print(path_pdf)

for name, pdf in [('bp_session_funnel', funnel_pdf), ('bp_path_conversion', path_pdf)]:
    sdf = spark.createDataFrame(pdf)
    save_result(sdf, name)
    write_mysql(sdf, name)

# 桑基/流转边：行为阶段间流量（会话级）
edge_rows = [
    ('浏览', '收藏', pv_fav), ('浏览', '加购', pv_cart),
    ('浏览', '购买', cnt('has_pv=1 and has_buy=1')), ('浏览', '流失', cnt('has_pv=1 and has_buy=0')),
    ('收藏', '购买', cnt('has_fav=1 and has_buy=1')),
    ('加购', '购买', cnt('has_cart=1 and has_buy=1')),
]
edge_pdf = pd.DataFrame(edge_rows, columns=['source', 'target', 'value'])
edge_sdf = spark.createDataFrame(edge_pdf)
save_result(edge_sdf, 'bp_flow_edges')
write_mysql(edge_sdf, 'bp_flow_edges')

# ============ 二、Apriori 类目关联规则 ============
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

# 热门 Top200 类目（聚焦，避免长尾稀疏）
top_cat = [r['category_id'] for r in
           df.groupBy('category_id').count().orderBy(F.desc('count')).limit(200).collect()]
bc = set(top_cat)
basket_rows = (df.filter(F.col('category_id').isin(top_cat))
                 .groupBy('user_id', 'date')
                 .agg(F.collect_set('category_id').alias('cats'))
                 .collect())
transactions = [[str(c) for c in row['cats']] for row in basket_rows]
print('购物篮数量:', len(transactions))
te = TransactionEncoder()
arr = te.fit_transform(transactions)
basket = pd.DataFrame(arr, columns=te.columns_)
freq = apriori(basket, min_support=0.01, use_colnames=True, max_len=3)
print('频繁项集数:', len(freq))
if len(freq) > 0:
    rules = association_rules(freq, metric='confidence', min_threshold=0.25)
    rules = rules[rules['lift'] > 1.1].sort_values(['lift', 'confidence'], ascending=False)
    rules_out = rules.head(50).copy()
    rules_out['antecedents'] = rules_out['antecedents'].apply(lambda x: ','.join(sorted(x)))
    rules_out['consequents'] = rules_out['consequents'].apply(lambda x: ','.join(sorted(x)))
    for c in ['support', 'confidence', 'lift']:
        rules_out[c] = rules_out[c].round(4)
    rules_out = rules_out[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
else:
    rules_out = pd.DataFrame(columns=['antecedents', 'consequents', 'support', 'confidence', 'lift'])
print('关联规则数(lift>1):', len(rules_out)); print(rules_out.head(10))
r_sdf = spark.createDataFrame(rules_out)
save_result(r_sdf, 'bp_apriori_rules')
write_mysql(r_sdf, 'bp_apriori_rules')

spark.stop()
print('03B PATH_APRIORI DONE')
