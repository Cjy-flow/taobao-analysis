# -*- coding: utf-8 -*-
"""
05 购买意向预测（XGBoost）
- 观察期 2017-11-25~12-01 构造特征；标签期 2017-12-02~12-03 是否购买
- 特征：用户-商品交互(pv/fav/cart、最近间隔、是否收藏加购) + 用户活跃度 + 商品热度 + 用户-类目交互
- 负样本下采样(1:20)，XGBoost 分类，输出 AUC/混淆矩阵/特征重要性/ROC/购买概率排行榜，并保存模型
"""
import os
import json
import numpy as np
import pandas as pd
from common import build_spark, save_result, write_mysql, PARQUET, OUT_TABLES, ROOT
from pyspark.sql import functions as F
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix, roc_curve)
import xgboost as xgb

MODEL_DIR = os.path.join(ROOT, 'outputs', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)
LABEL_START = '2017-12-02'
LABEL_START_TS = 1512144000  # 2017-12-02 00:00:00 (UTC+8)
spark = build_spark('05_intent_xgboost')
df = spark.read.parquet(PARQUET)
obs = df.filter(F.col('date') <= F.lit('2017-12-01'))
lbl = df.filter((F.col('date') >= F.lit(LABEL_START)) & (F.col('behavior_type') == 'buy'))

# ---------- 用户-商品 观察期特征 ----------
label_start_ts = int(F.unix_timestamp(F.lit('2017-12-02 00:00:00')).toString()) if False else 1512144000  # 2017-12-02 00:00 CST
ui = (obs.groupBy('user_id', 'item_id').agg(
        F.sum(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('ui_pv'),
        F.sum(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('ui_fav'),
        F.sum(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('ui_cart'),
        F.count('*').alias('ui_act'),
        F.max('ts').alias('ui_last_ts'),
        F.first('category_id').alias('category_id'))
      .withColumn('ui_last_gap_h', F.round((F.lit(LABEL_START_TS) - F.col('ui_last_ts')) / 3600.0, 2))
      .withColumn('has_fav', F.when(F.col('ui_fav') > 0, 1).otherwise(0))
      .withColumn('has_cart', F.when(F.col('ui_cart') > 0, 1).otherwise(0)))

# ---------- 用户 / 商品 / 用户-类目 特征 ----------
u = (obs.groupBy('user_id').agg(
        F.sum(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('u_pv'),
        F.sum(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('u_fav'),
        F.sum(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('u_cart'),
        F.countDistinct('item_id').alias('u_items'),
        F.countDistinct('category_id').alias('u_cats'),
        F.countDistinct('date').alias('u_active_days')))
it = (obs.groupBy('item_id').agg(
        F.sum(F.when(F.col('behavior_type') == 'pv', 1).otherwise(0)).alias('i_pv'),
        F.sum(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('i_fav'),
        F.sum(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('i_cart'),
        F.count('*').alias('i_act')))
uc = (obs.groupBy('user_id', 'category_id').agg(
        F.count('*').alias('uc_act'),
        F.sum(F.when(F.col('behavior_type') == 'cart', 1).otherwise(0)).alias('uc_cart'),
        F.sum(F.when(F.col('behavior_type') == 'fav', 1).otherwise(0)).alias('uc_fav')))

# ---------- 标签：标签期是否购买 ----------
y = (lbl.select('user_id', 'item_id').distinct()
        .withColumn('label', F.lit(1)))
data = (ui.join(y, ['user_id', 'item_id'], 'left')
          .join(u, 'user_id', 'left')
          .join(it, 'item_id', 'left')
          .join(uc, ['user_id', 'category_id'], 'left')
          .fillna(0, subset=['label'])).fillna(0)
pdf = data.toPandas()
print('候选样本:', len(pdf), ' 正样本:', int(pdf.label.sum()))

# ---------- 负样本下采样 1:20 ----------
pos = pdf[pdf.label == 1]
neg_all = pdf[pdf.label == 0]
neg = neg_all.sample(n=min(len(neg_all), len(pos) * 20), random_state=42)
ds = pd.concat([pos, neg], ignore_index=True).sample(frac=1, random_state=42)
feat_cols = ['ui_pv', 'ui_fav', 'ui_cart', 'ui_act', 'ui_last_gap_h', 'has_fav', 'has_cart',
             'u_pv', 'u_fav', 'u_cart', 'u_items', 'u_cats', 'u_active_days',
             'i_pv', 'i_fav', 'i_cart', 'i_act', 'uc_act', 'uc_cart', 'uc_fav']
X = ds[feat_cols].astype(float).values
y_ = ds['label'].astype(int).values
Xtr, Xva, ytr, yva = train_test_split(X, y_, test_size=0.2, stratify=y_, random_state=42)
spw = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
model = xgb.XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.08, subsample=0.9,
    colsample_bytree=0.9, reg_lambda=1.0, scale_pos_weight=spw,
    eval_metric='auc', random_state=42, n_jobs=4, use_label_encoder=False)
model.fit(Xtr, ytr)
proba = model.predict_proba(Xva)[:, 1]
pred = (proba >= 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(yva, pred).ravel()
auc = roc_auc_score(yva, proba)
metrics = {
    'auc': round(float(auc), 4),
    'accuracy': round(accuracy_score(yva, pred), 4),
    'precision': round(precision_score(yva, pred, zero_division=0), 4),
    'recall': round(recall_score(yva, pred, zero_division=0), 4),
    'f1': round(f1_score(yva, pred, zero_division=0), 4),
    'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
    'n_train': int(len(Xtr)), 'n_pos_train': int(ytr.sum()), 'neg_ratio': 20}
print(json.dumps(metrics, ensure_ascii=False, indent=2))

# ---------- 结果表 ----------
mdf = pd.DataFrame([(k, v) for k, v in metrics.items() if isinstance(v, (int, float))],
                   columns=['metric', 'value'])
mdf['note'] = 'XGBoost购买意向预测'
save_result(spark.createDataFrame(mdf), 'xgb_metrics')
write_mysql(spark.createDataFrame(mdf), 'xgb_metrics')

cm = pd.DataFrame([['真负TN', tn], ['假正FP', fp], ['假负FN', fn], ['真正TP', tp]],
                  columns=['cell', 'count'])
save_result(spark.createDataFrame(cm), 'xgb_confusion')
write_mysql(spark.createDataFrame(cm), 'xgb_confusion')

fi = pd.DataFrame({'feature': feat_cols,
                   'gain': model.feature_importances_.round(4)}).sort_values('gain', ascending=False)
save_result(spark.createDataFrame(fi), 'xgb_feature_importance')
write_mysql(spark.createDataFrame(fi), 'xgb_feature_importance')

# ROC 曲线（抽 100 点）
fpr, tpr, thr = roc_curve(yva, proba)
idx = np.linspace(0, len(fpr) - 1, 100).astype(int)
roc = pd.DataFrame({'fpr': fpr[idx].round(4), 'tpr': tpr[idx].round(4)})
save_result(spark.createDataFrame(roc), 'xgb_roc')
write_mysql(spark.createDataFrame(roc), 'xgb_roc')

# ---------- 全量候选打分：购买概率排行榜 Top200 ----------
allX = pdf[feat_cols].astype(float)
pdf['buy_prob'] = model.predict_proba(allX)[:, 1].round(4)
rank = (pdf.sort_values('buy_prob', ascending=False)
        .drop_duplicates(['user_id', 'item_id']).head(200)
        [['user_id', 'item_id', 'category_id', 'buy_prob', 'ui_pv', 'ui_fav', 'ui_cart', 'has_fav', 'has_cart']]
        .reset_index(drop=True))
rank.insert(0, 'rank', range(1, len(rank) + 1))
save_result(spark.createDataFrame(rank), 'xgb_predict_rank')
write_mysql(spark.createDataFrame(rank), 'xgb_predict_rank')

# ---------- 保存模型 + 指标汇总 ----------
model.get_booster().save_model(os.path.join(MODEL_DIR, 'xgb_intent_model.json'))
am = spark.createDataFrame([
    ('xgb_auc', float(metrics['auc']), '购买意向预测AUC'),
    ('xgb_f1', float(metrics['f1']), '购买意向预测F1'),
    ('xgb_recall', float(metrics['recall']), '购买意向预测召回率'),
], ['metric', 'value', 'note'])
write_mysql(am, 'analysis_metrics', mode='append')
print('Top10 购买概率候选:'); print(rank.head(10))
spark.stop()
print('05 XGBOOST DONE')
