# -*- coding: utf-8 -*-
"""
07 生成可视化图表（读取 outputs/tables 的结果 CSV，输出 PNG 到 outputs/figures）
纯 pandas+matplotlib，无需启动 Spark。供实践报告与前端设计参考。
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:\dev\projects\taobao-analysis'
T = os.path.join(ROOT, 'outputs', 'tables')
FIG = os.path.join(ROOT, 'outputs', 'figures')
os.makedirs(FIG, exist_ok=True)

# 中文字体
for cand in ['Microsoft YaHei', 'SimHei', 'Microsoft JhengHei']:
    if any(cand in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.sans-serif'] = [cand]
        break
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 130
C = {'pv': '#4E79A7', 'fav': '#59A14F', 'cart': '#F28E2B', 'buy': '#E15759',
     'blue': '#2E6BE6', 'orange': '#FF8A3D', 'green': '#36A269', 'grey': '#9AA5B1'}
BEH_CN = {'pv': '浏览', 'fav': '收藏', 'cart': '加购', 'buy': '购买'}

def load(n):
    return pd.read_csv(os.path.join(T, n + '.csv'))

def save(fig, name):
    fig.tight_layout()
    p = os.path.join(FIG, name + '.png')
    fig.savefig(p, bbox_inches='tight')
    plt.close(fig)
    print('figure:', name)

# 1. 行为分布环形图
try:
    d = load('bp_behavior_ratio')
    fig, ax = plt.subplots(figsize=(6, 5))
    colors = [C[x] for x in d['behavior_type']]
    w, _, at = ax.pie(d['cnt'], labels=d['behavior_cn'], autopct='%1.2f%%', startangle=90,
                      colors=colors, wedgeprops=dict(width=0.42, edgecolor='w'), pctdistance=0.78)
    ax.set_title('用户行为类型分布')
    ax.text(0, 0, '行为\n分布', ha='center', va='center', fontsize=13, weight='bold')
    save(fig, '01_behavior_donut')
except Exception as e:
    print('donut err', e)

# 2. 11月每日访问量+累计
try:
    d = load('stat_nov_pv_cum')
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.bar(d['date'], d['pv_cnt'], color=C['blue'], alpha=.75, label='当日访问量')
    ax1.set_ylabel('当日访问量(PV)'); ax1.tick_params(axis='x', rotation=30)
    ax2 = ax1.twinx()
    ax2.plot(d['date'], d['cum_pv'], color=C['buy'], marker='o', lw=2, label='累计访问量')
    ax2.set_ylabel('累计访问量')
    ax1.set_title('2017年11月 每日访问量与累计访问量')
    fig.legend(loc='upper left', bbox_to_anchor=(.1, .95))
    save(fig, '02_nov_pv_cum')
except Exception as e:
    print('novpv err', e)

# 3. 每日购买量+全局/当月累计
try:
    d = load('stat_buy_cum')
    fig, ax1 = plt.subplots(figsize=(8.5, 4.5))
    ax1.bar(d['date'], d['buy_cnt'], color=C['green'], alpha=.7, label='当日购买量')
    ax1.set_ylabel('当日购买量'); ax1.tick_params(axis='x', rotation=30)
    ax2 = ax1.twinx()
    ax2.plot(d['date'], d['total_cum_buy'], color=C['buy'], marker='o', lw=2, label='全局累计')
    ax2.plot(d['date'], d['month_cum_buy'], color=C['orange'], marker='s', lw=2, ls='--', label='当月累计')
    ax2.set_ylabel('累计购买量'); ax1.set_title('每日购买量与累计购买量（11月/12月）')
    fig.legend(loc='upper left', bbox_to_anchor=(.1, .95))
    save(fig, '03_buy_cum')
except Exception as e:
    print('buycum err', e)

# 4. 小时活跃（分行为）
try:
    d = load('bp_hour')
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for b in ['pv', 'fav', 'cart', 'buy']:
        ax.plot(d['hour'], d[b], marker='o', ms=3, label=BEH_CN[b], color=C[b])
    ax.set_xticks(range(0, 24)); ax.set_xlabel('小时'); ax.set_ylabel('行为次数')
    ax.set_title('一天24小时用户行为活跃曲线'); ax.legend(); ax.grid(alpha=.3)
    save(fig, '04_hour_curve')
except Exception as e:
    print('hour err', e)

# 5. 小时×星期热力图
try:
    d = load('bp_hour_weekday')
    m = d.pivot(index='weekday', columns='hour', values='cnt').reindex(index=range(1, 8), columns=range(0, 24)).fillna(0)
    names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    fig, ax = plt.subplots(figsize=(11, 4))
    im = ax.imshow(m.values, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(24)); ax.set_xticklabels(range(24))
    ax.set_yticks(range(7)); ax.set_yticklabels(names)
    ax.set_xlabel('小时'); ax.set_title('用户活跃时段热力图（星期×小时）')
    fig.colorbar(im, ax=ax, label='行为量', shrink=.85)
    save(fig, '05_heatmap')
except Exception as e:
    print('heat err', e)

# 6. 星期日均
try:
    d = load('bp_weekday_avg')
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bars = ax.bar(d['weekday_cn'], d['avg_cnt'], color=C['blue'], alpha=.8)
    for b, v in zip(bars, d['avg_cnt']):
        ax.text(b.get_x()+b.get_width()/2, v, f'{v:.0f}', ha='center', va='bottom', fontsize=9)
    ax.set_title('各星期平均每日行为量'); ax.set_ylabel('日均行为量'); ax.grid(axis='y', alpha=.3)
    save(fig, '06_weekday_avg')
except Exception as e:
    print('wd err', e)

# 7. 会话漏斗
try:
    d = load('bp_session_funnel')
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    bars = ax.barh(d['stage'][::-1], d['sessions'][::-1], color=[C['grey'], C['buy'], C['cart'], C['green'], C['blue']][::-1])
    for b, v, p in zip(bars, d['sessions'][::-1], d['pct_of_all'][::-1]):
        ax.text(v, b.get_y()+b.get_height()/2, f' {v:,} ({p}%)', va='center', fontsize=9)
    ax.set_title('会话级行为漏斗'); ax.set_xlabel('会话数')
    save(fig, '07_funnel')
except Exception as e:
    print('funnel err', e)

# 8. 路径转化率
try:
    d = load('bp_path_conversion')
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bars = ax.bar(d['path'], d['conversion_pct'], color=[C['blue'], C['green'], C['orange'], C['buy'], C['grey']])
    for b, v in zip(bars, d['conversion_pct']):
        ax.text(b.get_x()+b.get_width()/2, v, f'{v}%', ha='center', va='bottom', fontsize=9)
    ax.set_title('不同点击流路径转化率'); ax.set_ylabel('转化率(%)'); ax.tick_params(axis='x', rotation=15)
    save(fig, '08_path_conversion')
except Exception as e:
    print('path err', e)

# 9. Top10 浏览 / 购买商品
try:
    pv = load('bp_top10_pv_items'); bu = load('bp_top10_buy_items')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].barh(pv['item_id'].astype(str)[::-1], pv['pv'][::-1], color=C['blue'])
    axes[0].set_title('浏览量Top10商品（数字为购买次数）')
    for i, (p, b) in enumerate(zip(pv['pv'][::-1], pv['buy'][::-1])):
        axes[0].text(p, i, f' 购{b}', va='center', fontsize=8)
    axes[1].barh(bu['item_id'].astype(str)[::-1], bu['buy'][::-1], color=C['buy'])
    axes[1].set_title('购买量Top10商品（数字为浏览次数）')
    for i, (b, p) in enumerate(zip(bu['buy'][::-1], bu['pv'][::-1])):
        axes[1].text(b, i, f' 览{p}', va='center', fontsize=8)
    save(fig, '09_top_items')
except Exception as e:
    print('topitem err', e)

# 10. Apriori Top15 规则 lift
try:
    d = load('bp_apriori_rules').head(15)
    labels = (d['antecedents'].astype(str) + ' → ' + d['consequents'].astype(str))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(labels[::-1], d['lift'][::-1], color=C['green'])
    ax.set_xlabel('Lift 提升度'); ax.set_title('类目关联规则 Top15（按提升度）')
    save(fig, '10_apriori')
except Exception as e:
    print('apriori err', e)

# 11. RFM 簇散点 + 占比
try:
    rfm = load('rfm_detail'); seg = load('rfm_cluster_summary')
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    sc = axes[0].scatter(rfm['recency'], rfm['frequency'], c=rfm['cluster'], cmap='viridis', s=8, alpha=.5)
    axes[0].set_xlabel('Recency 最近购买间隔(天)'); axes[0].set_ylabel('Frequency 购买次数')
    axes[0].set_title('R-F 用户分群散点'); axes[0].set_ylim(0, rfm['frequency'].quantile(.99))
    colors = ['#E15759', '#F28E2B', '#36A269']
    axes[1].pie(seg['users'], labels=seg['segment'], autopct='%1.1f%%', colors=colors, startangle=90)
    axes[1].set_title('K-Means 用户价值分群占比')
    save(fig, '11_rfm_cluster')
except Exception as e:
    print('rfm err', e)

# 12. RFM 八分法
try:
    d = load('rfm_octant_summary')
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bars = ax.bar(d['octant'], d['users'], color=C['blue'], alpha=.8)
    for b, v in zip(bars, d['users']):
        ax.text(b.get_x()+b.get_width()/2, v, str(v), ha='center', va='bottom', fontsize=9)
    ax.set_title('RFM 八分法用户数量'); ax.set_ylabel('用户数'); ax.tick_params(axis='x', rotation=20)
    save(fig, '12_rfm_octant')
except Exception as e:
    print('oct err', e)

# 13. XGBoost ROC / 混淆矩阵 / 特征重要性
try:
    roc = load('xgb_roc'); cm = load('xgb_confusion'); fi = load('xgb_feature_importance').head(12)
    fig = plt.figure(figsize=(13, 4.2))
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.plot(roc['fpr'], roc['tpr'], color=C['buy'], lw=2)
    ax1.plot([0, 1], [0, 1], ls='--', color=C['grey'])
    ax1.set_xlabel('假正率FPR'); ax1.set_ylabel('真正率TPR'); ax1.set_title('ROC 曲线')
    ax2 = fig.add_subplot(1, 3, 2)
    mat = cm['count'].values.reshape(2, 2)
    im = ax2.imshow(mat, cmap='Blues')
    for i in range(2):
        for j in range(2):
            ax2.text(j, i, mat[i, j], ha='center', va='center', fontsize=12)
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(['预测负', '预测正'])
    ax2.set_yticks([0, 1]); ax2.set_yticklabels(['实际负', '实际正']); ax2.set_title('混淆矩阵')
    ax3 = fig.add_subplot(1, 3, 3)
    ax3.barh(fi['feature'][::-1], fi['gain'][::-1], color=C['green'])
    ax3.set_title('特征重要性 Top12(Gain)'); ax3.tick_params(labelsize=8)
    save(fig, '13_xgb')
except Exception as e:
    print('xgb fig err', e)

print('ALL FIGURES DONE ->', FIG)
print(os.listdir(FIG))
