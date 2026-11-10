# -*- coding: utf-8 -*-
"""绘制实践报告所需的系统设计图：业务流程、用例图、总体架构、功能模块"""
import os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Rectangle
from matplotlib import font_manager

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:\dev\projects\taobao-analysis'
OUT = os.path.join(ROOT, 'report', 'design_figs')
os.makedirs(OUT, exist_ok=True)
for cand in ['Microsoft YaHei', 'SimHei']:
    if any(cand in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams['font.sans-serif'] = [cand]; break
plt.rcParams['axes.unicode_minus'] = False

BLUE, LBLUE, GREEN, ORANGE, PURPLE, GREY = '#2E6BE6', '#E8F1FF', '#36A269', '#FF8A3D', '#925FB3', '#F0F2F5'

def box(ax, x, y, w, h, text, fc=LBLUE, ec=BLUE, fs=11, tc='#1f2d3d', round=True, lw=1.4):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08" if round else "square,pad=0",
                       fc=fc, ec=ec, lw=lw, mutation_scale=1)
    ax.add_patch(p)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs, color=tc, wrap=True)

def arrow(ax, p1, p2, color='#666', lw=1.6, style='-|>'):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14, color=color, lw=lw))

# ---------- 1. 业务流程图 ----------
fig, ax = plt.subplots(figsize=(11, 3.2))
ax.set_xlim(0, 12); ax.set_ylim(0, 3.4); ax.axis('off')
steps = [('数据源\n天池UserBehavior\n(用户行为日志)', '#FFF3E6', ORANGE),
         ('数据清洗\n时间转换·去重\n异常过滤', LBLUE, BLUE),
         ('分布式分析\nPySpark统计\n+机器学习', '#E9F7EF', GREEN),
         ('数据入库\nMySQL结果表\nParquet缓存', '#F3EBFB', PURPLE),
         ('可视化系统\nVue+ECharts\n交互分析', LBLUE, BLUE),
         ('运营决策\n精准营销·推荐\n用户运营', '#FDECEA', '#E15759')]
w = 1.72; gap = 0.18; x = 0.15
for i,(t,fc,ec) in enumerate(steps):
    box(ax, x, 1.0, w, 1.5, t, fc=fc, ec=ec, fs=9.5)
    if i < len(steps)-1:
        arrow(ax, (x+w, 1.75), (x+w+gap, 1.75))
    x += w+gap
ax.text(6, 3.05, '淘宝用户购物行为大数据分析系统 —— 业务流程图', ha='center', fontsize=13, weight='bold')
ax.text(6, 0.45, '数据分析人员贯穿全流程：采集 → 清洗 → 分析建模 → 存储 → 可视化 → 决策支持', ha='center', fontsize=9.5, color='#666')
fig.tight_layout(); fig.savefig(os.path.join(OUT,'business_flow.png'), dpi=150, bbox_inches='tight'); plt.close()
print('business_flow done')

# ---------- 2. 用例图 ----------
fig, ax = plt.subplots(figsize=(9.5, 6.2))
ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis('off')
# 系统边界
ax.add_patch(Rectangle((3.2, 0.4), 6.3, 6.2, fc='#FAFCFF', ec=BLUE, lw=1.6))
ax.text(6.35, 6.25, '淘宝用户行为分析系统', ha='center', fontsize=12, weight='bold', color=BLUE)
# actor
ax.plot(1.3, 4.0, marker='o', ms=14, mfc='white', mec='#333', mew=1.6)
ax.plot([1.3,1.3],[3.75,2.9], color='#333', lw=1.6)
ax.plot([0.85,1.75],[3.5,3.5], color='#333', lw=1.6)
ax.plot([1.3,0.9],[2.9,2.3], color='#333', lw=1.6)
ax.plot([1.3,1.7],[2.9,2.3], color='#333', lw=1.6)
ax.text(1.3, 1.9, '数据分析/运营人员', ha='center', fontsize=10.5)
ucs = ['查看仪表盘总览(KPI/趋势/行为分布)','行为模式分析(时段/漏斗/路径/关联)',
       'RFM 用户分群管理与明细查询','XGBoost 购买意向预测与排行榜',
       'ALS 个性化商品推荐查询','预测结果/分群数据导出']
ys = [5.5,4.7,3.9,3.1,2.3,1.5]
for u,y in zip(ucs,ys):
    ax.add_patch(Ellipse((6.35,y), 3.5, 0.62, fc=LBLUE, ec=BLUE, lw=1.2))
    ax.text(6.35,y,u,ha='center',va='center',fontsize=9.3)
    ax.plot([1.75,4.6],[3.4,y],color='#999',lw=1)  # 连线
fig.tight_layout(); fig.savefig(os.path.join(OUT,'usecase.png'), dpi=150, bbox_inches='tight'); plt.close()
print('usecase done')

# ---------- 3. 系统总体架构图（分层） ----------
fig, ax = plt.subplots(figsize=(10.5, 6.9))
ax.set_xlim(0, 12); ax.set_ylim(0, 8.5); ax.axis('off')
layers = [
    ('展示层  Vue3 + Element Plus + ECharts + Axios', ['仪表盘总览','行为模式分析','RFM分群管理','预测模型监控'], '#E8F1FF', BLUE, 6.5),
    ('接口层  Spring Boot 3 · Spring MVC · JdbcTemplate（RESTful API / 跨域 CORS）', ['OverviewController','DashboardController','RfmController','PredictController'], '#E9F7EF', GREEN, 4.9),
    ('计算层  PySpark 3.5 · Spark SQL · MLlib', ['行为统计分析','Apriori关联','RFM+KMeans','XGBoost预测','ALS协同过滤'], '#F3EBFB', PURPLE, 3.3),
    ('存储层  MySQL 8.0（结果表） + Parquet（清洗缓存） + CSV/JSON', ['taobao_behavior 库 · 31张结果表'], '#FFF3E6', ORANGE, 1.7),
    ('数据源  天池 UserBehavior 数据集（100万行样本：pv/fav/cart/buy）', ['UserBehavior.csv'], '#FDECEA', '#E15759', 0.3),
]
for title, mods, fc, ec, y in layers:
    ax.add_patch(FancyBboxPatch((0.3,y),11.4,1.35, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=1.5))
    ax.text(0.55, y+1.08, title, ha='left', va='center', fontsize=10.5, weight='bold', color=ec)
    n=len(mods); ww=11.0/max(n,1)
    for i,m in enumerate(mods):
        box(ax, 0.55+i*ww+0.05, y+0.12, ww-0.2, 0.55, m, fc='white', ec=ec, fs=9, lw=1)
for y in [6.5,4.9,3.3,1.7]:
    arrow(ax,(6,y),(6,y-0.05),color='#888')
ax.text(6,8.25,'系统总体技术架构图（数据源 → 存储 → 计算 → 接口 → 展示）',ha='center',fontsize=13,weight='bold')
fig.tight_layout(); fig.savefig(os.path.join(OUT,'architecture.png'), dpi=150, bbox_inches='tight'); plt.close()
print('architecture done')

# ---------- 4. 功能模块图 ----------
fig, ax = plt.subplots(figsize=(11, 5.6))
ax.set_xlim(0,12); ax.set_ylim(0,7); ax.axis('off')
box(ax, 4.5, 5.9, 3, 0.8, '淘宝用户行为分析系统', fc=BLUE, ec=BLUE, tc='white', fs=12)
sub = [('数据分析引擎',1.0,GREEN),('数据服务(API)',4.6,PURPLE),('可视化前端',8.2,ORANGE)]
for t,x,c in sub:
    box(ax,x,4.4,2.6,0.75,t,fc='white',ec=c,fs=11)
    arrow(ax,(6,5.9),(x+1.3,5.15),color=c)
leafs = [
    ['行为模式统计','行为路径/漏斗','Apriori关联','RFM+KMeans分群','XGBoost购买预测','ALS协同推荐'],
    ['总览接口','看板接口','分群接口','预测/推荐接口','统一响应/跨域','分页查询'],
    ['仪表盘总览','行为模式分析','RFM分群管理','预测模型监控','交互筛选/分页','CSV导出'],
]
for (t,x,c),items in zip(sub,leafs):
    for i,it in enumerate(items):
        yy=3.5-i*0.62
        box(ax,x,yy,2.6,0.5,it,fc='#F7F9FC',ec=c,fs=9,lw=1)
        arrow(ax,(x+1.3,4.4),(x+1.3,yy+0.5),color='#bbb',lw=1)
ax.text(6,6.85,'系统功能模块结构图',ha='center',fontsize=13,weight='bold')
fig.tight_layout(); fig.savefig(os.path.join(OUT,'function_module.png'), dpi=150, bbox_inches='tight'); plt.close()
print('function_module done')
print('ALL DESIGN FIGS ->', OUT, os.listdir(OUT))
