# -*- coding: utf-8 -*-
"""
生成《行业工程实践》课程实践报告 Word 文档（严格按模板六章结构，图文并茂）
姓名/学号在下方 STUDENT_NAME / STUDENT_ID 修改后重跑即可。
"""
import os, sys
import pandas as pd
import pymysql
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'D:\dev\projects\taobao-analysis'
TAB = os.path.join(ROOT, 'outputs', 'tables')
FIG = os.path.join(ROOT, 'outputs', 'figures')
DFIG = os.path.join(ROOT, 'report', 'design_figs')
UISHOT = os.path.join(ROOT, 'report', 'ui_shots')

# ====== 学生信息（拿到后改这里重跑） ======
STUDENT_NAME = '程少锋'   # 学生姓名
STUDENT_ID = '2501330008'  # 学号
OUT_DOCX = os.path.join(ROOT, 'report', f'《行业工程实践》课程实践报告-{STUDENT_ID}-{STUDENT_NAME}.docx')

# ---------- 读取结果数据 ----------
def csv(n): return pd.read_csv(os.path.join(TAB, n + '.csv'))
metrics = {}
try:
    conn = pymysql.connect(host='localhost', user='root', password='CHANGE_ME', database='taobao_behavior', charset='utf8mb4')
    mdf = pd.read_sql('SELECT metric,value FROM analysis_metrics', conn); conn.close()
    metrics = dict(zip(mdf.metric, mdf.value))
except Exception as e:
    print('[WARN] 读取MySQL失败，使用内置数字', e)
    metrics = dict(nov_total_pv=551538, total_buy=20359, buy_user_total=6689, rfm_high_value_users=497,
                   top30_buy_share=60.94, gap_over5_ratio=12.75, xgb_auc=0.8506, xgb_accuracy=0.9089,
                   xgb_precision=0.2845, xgb_recall=0.6047, xgb_f1=0.3869, rfm_users=6689)
beh = csv('bp_behavior_ratio')
rfm_seg = csv('rfm_cluster_summary')
octant = csv('rfm_octant_summary')
xgbm = dict(zip(csv('xgb_metrics').metric, csv('xgb_metrics').value))
alsm = dict(zip(csv('als_metrics').metric, csv('als_metrics').value))
funnel = csv('bp_session_funnel')
pathc = csv('bp_path_conversion')
apriori = csv('bp_apriori_rules')

# ---------- docx 样式辅助 ----------
doc = Document()
# 页面 A4
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.54); sec.left_margin = sec.right_margin = Cm(2.8)

def _font(run, cn='宋体', en='Times New Roman', size=12, bold=False, color=None):
    run.font.size = Pt(size); run.font.bold = bold; run.font.name = en
    rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.append(rf)
    rf.set(qn('w:eastAsia'), cn); rf.set(qn('w:ascii'), en); rf.set(qn('w:hAnsi'), en)
    if color: run.font.color.rgb = RGBColor(*color)

def para(text='', size=12, cn='宋体', bold=False, align=None, indent=True,
         space_after=6, line=1.5, color=None):
    p = doc.add_paragraph(); pf = p.paragraph_format
    pf.line_spacing = line; pf.space_after = Pt(space_after)
    if indent: pf.first_line_indent = Pt(size*2)
    if align is not None: p.alignment = align
    if text:
        r = p.add_run(text); _font(r, cn=cn, size=size, bold=bold, color=color)
    return p

def h1(num, text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(8)
    r = p.add_run(f'{num}  {text}'); _font(r, cn='黑体', en='Arial', size=16, bold=True)
    return p

def h2(num, text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(8); p.paragraph_format.space_after = Pt(6)
    r = p.add_run(f'{num} {text}'); _font(r, cn='黑体', en='Arial', size=14, bold=True)
    return p

_fig_no = 0
def figure(path, caption, width=15.0):
    global _fig_no
    if not os.path.exists(path):
        para('[缺图: %s]' % path, size=10, color=(200,0,0)); return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(4)
    p.add_run().add_picture(path, width=Cm(width))
    cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER; cap.paragraph_format.space_after = Pt(10)
    r = cap.add_run(caption); _font(r, cn='黑体', size=10.5, bold=True)

_tbl_no = 0
def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd')
    sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),hexcolor); tcPr.append(sh)

def table(headers, rows, caption=None, widths=None, fs=10.5, header_fill='D9E6FB'):
    global _tbl_no
    if caption:
        cp = doc.add_paragraph(); cp.paragraph_format.space_before = Pt(6)
        r = cp.add_run(caption); _font(r, cn='黑体', size=10.5, bold=True)
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i,h in enumerate(headers):
        hdr[i].text=''; rr = hdr[i].paragraphs[0].add_run(str(h)); _font(rr, cn='黑体', size=fs, bold=True)
        hdr[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER; _shade(hdr[i], header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i,v in enumerate(row):
            cells[i].text=''; rr = cells[i].paragraphs[0].add_run(str(v)); _font(rr, size=fs)
            cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if widths:
        for i,w in enumerate(widths):
            for row in t.rows: row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def code(text, title=None):
    if title:
        p=doc.add_paragraph(); r=p.add_run(title); _font(r,cn='黑体',size=10.5,bold=True)
    for line in text.strip('\n').split('\n'):
        p = doc.add_paragraph(); pf=p.paragraph_format
        pf.left_indent=Cm(0.4); pf.space_after=Pt(0); pf.line_spacing=1.0
        pPr = p._p.get_or_add_pPr(); sh=OxmlElement('w:shd'); sh.set(qn('w:val'),'clear'); sh.set(qn('w:fill'),'F4F6F8'); pPr.append(sh)
        r=p.add_run(line if line else ' '); _font(r,cn='Consolas',en='Consolas',size=9)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)

def bullets(items, size=12):
    for it in items:
        p=doc.add_paragraph(style=None); pf=p.paragraph_format
        pf.left_indent=Pt(24); pf.line_spacing=1.5; pf.space_after=Pt(3)
        r=p.add_run('● '+it); _font(r,size=size)

# ============================================================
# 封面
# ============================================================
for _ in range(2): doc.add_paragraph()
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('课程实践报告'); _font(r,cn='黑体',size=30,bold=True)
for _ in range(3): doc.add_paragraph()
cover_items = [('课程名称','行业工程实践'),('项    目','淘宝用户购物行为大数据分析系统'),
               ('学    院','计算与信息科学学院'),('专    业','软件工程（专升本）'),
               ('班    级','2025级1班'),('指导教师','张炯辉'),
               ('学生姓名',STUDENT_NAME),('学    号',STUDENT_ID)]
for k,v in cover_items:
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(14)
    r=p.add_run(f'{k}：{v}'); _font(r,cn='楷体',size=15,bold=True)
for _ in range(3): doc.add_paragraph()
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('2026 年 8 月'); _font(r,cn='楷体',size=15,bold=True)
doc.add_page_break()

# ============================================================
# 1 系统分析
# ============================================================
h1('1','系统分析')
h2('1.1','需求分析')
para('随着电子商务的快速发展，淘宝等平台每天都会产生海量的用户行为日志。对用户浏览、收藏、加购、购买等行为进行大数据分析，能够还原用户的购物决策路径、识别用户价值、预测购买意向并进行个性化推荐，从而为精准营销、商品运营和用户增长提供数据支撑。本项目基于阿里巴巴天池公开数据集 UserBehavior，设计并实现一套“数据采集—清洗—分布式分析—机器学习建模—可视化交互”的完整大数据分析系统。')
para('（1）数据规模与字段。数据集包含用户 ID、商品 ID、商品类目 ID、行为类型和时间戳五个字段，行为类型分为浏览(pv)、收藏(fav)、加购(cart)、购买(buy)四类。本项目在全量约一亿条（3.42GB）数据的背景下，采用一百万条行为样本进行分析，覆盖 9739 名用户、398971 件商品、5793 个类目，时间窗口为 2017-11-25 至 2017-12-03，共 9 天。')
para('（2）功能需求。根据课程任务，系统需实现三大分析方向与一套可视化系统：')
bullets([
 '行为模式统计：每日访问量与累计访问量、每日购买量与累计购买量、11 月购买品类的用户排名、购买量前 30% 用户及其购买量占比、多次购买用户的相邻购买间隔分布；',
 '行为模式分析：行为类型占比、活跃时段（小时×星期）、会话切分与行为漏斗、点击流路径转化率、商品类目关联规则（Apriori）、热门商品交叉分析；',
 'RFM 用户价值分群：构建 RFM 模型，结合 K-Means 聚类与经典八分法对用户分层，并给出差异化运营策略；',
 '购买意向预测：以观察期特征预测标签期是否购买，采用 XGBoost 二分类并输出购买概率排行榜；',
 '协同过滤推荐：基于 Spark MLlib ALS 隐式反馈为用户生成个性化 Top-N 商品推荐，并处理冷启动；',
 '可视化系统：Spring Boot + Vue3 + ECharts 实现仪表盘总览、行为模式分析、RFM 分群管理、预测模型监控四大交互模块。'])
para('（3）性能与非功能需求。数据量达到百万级，单机 Pandas 难以高效完成多次迭代计算，因此分析层采用 Apache Spark 集群式（本地多线程）计算，并将清洗结果缓存为 Parquet 列式存储以复用；结果统一写入 MySQL，由后端提供 REST 接口，前端查询响应控制在百毫秒级；系统需保证可复现（一键重跑脚本）、可扩展（新增分析只需新增脚本与结果表）和健壮性（接口防注入、跨域、空数据兜底）。')

h2('1.2','业务流程图')
para('从用户（数据分析/运营人员）使用角度，系统的业务流程为：首先采集原始行为日志，经过时间转换、去重与异常过滤得到干净数据；随后由 PySpark 完成统计分析与机器学习建模，结果写入 MySQL 并缓存为 Parquet/CSV；最后通过可视化系统以图表形式交互呈现，支撑运营决策。业务流程如图 1-1 所示。')
figure(os.path.join(DFIG,'business_flow.png'),'图 1-1  系统业务流程图',15.5)

h2('1.3','系统用例图')
para('系统的主要参与者为数据分析/运营人员，其可执行的用例包括：查看仪表盘总览、进行行为模式分析、RFM 分群管理与明细查询、XGBoost 购买意向预测与排行榜查看、ALS 个性化商品推荐查询，以及分析结果导出。系统用例如图 1-2 所示，各用例说明见表 1-1。')
figure(os.path.join(DFIG,'usecase.png'),'图 1-2  系统用例图',13.5)
table(['用例','功能描述','对应模块'],
 [['查看仪表盘总览','查看核心 KPI、每日/累计访问与购买趋势、行为占比','仪表盘总览'],
  ['行为模式分析','活跃时段热力、漏斗、路径转化、关联规则、热门商品','行为模式分析'],
  ['RFM 分群管理','查看分群占比与策略、四象限散点、按分群筛选明细分页','RFM 分群管理'],
  ['购买意向预测','查看 AUC/混淆矩阵/特征重要性与购买概率排行榜','预测模型监控'],
  ['个性化推荐','输入用户 ID 获取 ALS Top10 推荐及热门兜底','预测模型监控'],
  ['数据导出','导出购买概率预测结果 CSV','预测模型监控']],
 caption='表 1-1  系统用例描述', widths=[3.2,8.2,3.6])

# ============================================================
# 2 系统设计
# ============================================================
h1('2','系统设计')
h2('2.1','系统结构设计')
para('系统采用分层架构，自上而下分为展示层、接口层、计算层、存储层和数据源，总体结构如图 2-1 所示。展示层使用 Vue3 + Element Plus + ECharts 构建单页应用；接口层使用 Spring Boot 3 提供 RESTful 接口并通过 JdbcTemplate 读取结果表；计算层使用 PySpark（Spark SQL、MLlib）完成统计与机器学习；存储层使用 MySQL 8.0 持久化分析结果、Parquet 缓存清洗数据；数据源为天池 UserBehavior 数据集。技术选型见表 2-1。')
figure(os.path.join(DFIG,'architecture.png'),'图 2-1  系统总体技术架构图',15.5)
table(['层次','技术选型','职责'],
 [['展示层','Vue3 / Vite / Element Plus / ECharts / Axios','四大交互模块、图表渲染、分页筛选'],
  ['接口层','Spring Boot 3.2 / Spring MVC / JdbcTemplate','REST 接口、统一响应、跨域、防注入'],
  ['计算层','PySpark 3.5 / Spark SQL / MLlib / XGBoost / mlxtend / scikit-learn','清洗、统计、关联规则、聚类、预测、推荐'],
  ['存储层','MySQL 8.0 / Parquet / CSV·JSON','结果表持久化、中间缓存、结果双份导出'],
  ['数据源','天池 UserBehavior（百万行样本）','用户行为原始日志']],
 caption='表 2-1  技术选型表', widths=[2.6,7.2,5.2])

h2('2.2','功能模块设计')
para('从开发/技术角度，系统划分为数据分析引擎、数据服务（API）和可视化前端三个子系统，功能模块结构如图 2-2 所示。数据分析引擎由 01~07 共七个脚本组成流水线：01 数据加载清洗并缓存 Parquet，02 行为统计，03a/03b 行为模式与路径关联，04 RFM 分群，05 XGBoost 预测，06 ALS 推荐，07 汇总生成图表；数据服务层按业务划分四个 Controller；可视化前端对应四个页面。')
figure(os.path.join(DFIG,'function_module.png'),'图 2-2  系统功能模块结构图',15.5)
para('数据分析流水线采用“一次清洗、多处复用”的设计：01 脚本将清洗后的 999,530 条数据缓存为 Parquet，后续脚本直接读取缓存，避免重复清洗；每个脚本通过公共框架 common.py 统一构建 SparkSession、注入 MySQL 驱动，并将结果同时写入 MySQL、导出 UTF-8-SIG 编码的 CSV 与 JSON，保证结果可追溯、前端与报告均可复用。')

h2('2.3','数据结构设计')
para('原始数据为无表头 CSV，五个字段含义见表 2-2。分析结果在 MySQL 库 taobao_behavior 中以结果表形式存储，共 31 张表，按主题分类见表 2-3；其中用户行为明细表与三张核心模型表的结构分别见表 2-4~表 2-5。')
table(['字段','类型','含义'],
 [['user_id','BIGINT','用户唯一标识（脱敏）'],['item_id','BIGINT','商品唯一标识'],
  ['category_id','BIGINT','商品所属类目标识'],['behavior_type','STRING','pv 浏览 / fav 收藏 / cart 加购 / buy 购买'],
  ['ts','BIGINT','行为发生的秒级时间戳（北京时间 UTC+8）']],
 caption='表 2-2  UserBehavior 原始字段说明', widths=[3.2,2.6,9.2])
table(['主题','结果表（示例）'],
 [['清洗/概览','user_behavior、daily_overview'],
  ['行为统计','stat_nov_pv_cum、stat_buy_cum、stat_nov_user_category_rank、stat_top30_buy_users、stat_buy_gap_dist、behavior_dist'],
  ['行为模式','bp_behavior_ratio、bp_hour、bp_hour_weekday、bp_weekday_avg、bp_session_funnel、bp_path_conversion、bp_flow_edges、bp_apriori_rules、bp_top10_pv_items、bp_top10_buy_items'],
  ['RFM','rfm_detail、rfm_cluster_summary、rfm_octant_summary'],
  ['XGBoost','xgb_metrics、xgb_confusion、xgb_feature_importance、xgb_roc、xgb_predict_rank'],
  ['ALS','als_user_recs、als_popular_items、als_metrics'],
  ['汇总','analysis_metrics（标量指标统一汇总）']],
 caption='表 2-3  MySQL 结果表分类（共 31 张）', widths=[2.8,12.2])
table(['字段','含义'],
 [['user_id / item_id / category_id','用户、商品、类目'],['behavior_type','行为类型'],
  ['ts / dt / hour / weekday','时间戳、日期、小时、星期'],['is_weekend','是否周末']],
 caption='表 2-4  user_behavior（清洗后明细，999,530 行）', widths=[6.0,9.0])
table(['表','关键字段'],
 [['rfm_detail','user_id、recency、frequency、monetary、r/f/m_score、cluster、segment、octant、strategy'],
  ['xgb_predict_rank','rank、user_id、item_id、category_id、buy_prob、20 维特征'],
  ['als_user_recs','user_id、rank、item_id、category_id、score、i_pv、i_buy']],
 caption='表 2-5  核心模型结果表结构', widths=[3.6,11.4])

h2('2.4','接口设计')
para('后端遵循 RESTful 风格，统一返回 {code, msg, data} 结构，所有接口以 /api 开头并全局放开跨域。为防止 SQL 注入，结果表名采用白名单校验、排序列逐列加反引号规范化、查询值使用预编译参数。主要接口见表 2-6。')
table(['模块','请求路径','方法','说明'],
 [['总览','/api/overview/metrics','GET','核心 KPI 汇总指标'],
  ['总览','/api/overview/daily、/behavior-ratio','GET','每日概览、行为占比'],
  ['看板','/api/dashboard/nov-pv-cum、/buy-cum、/hour、/hour-weekday','GET','趋势与时段'],
  ['看板','/api/dashboard/funnel、/path-conversion、/flow-edges、/apriori、/top-pv、/top-buy','GET','漏斗/路径/关联/热门'],
  ['RFM','/api/rfm/cluster-summary、/octant、/scatter','GET','分群汇总、八分法、散点'],
  ['RFM','/api/rfm/detail?cluster=&page=&size=','GET','明细分页与分群筛选'],
  ['预测','/api/predict/xgb-metrics、/xgb-confusion、/xgb-feature、/xgb-roc','GET','模型评估数据'],
  ['预测','/api/predict/xgb-rank?page=&size=','GET','购买概率排行榜分页'],
  ['推荐','/api/predict/als-recs?userId=、/als-popular、/als-metrics','GET','个性化推荐与热门兜底']],
 caption='表 2-6  后端主要 REST 接口', widths=[1.8,8.6,1.6,3.0])

# ============================================================
# 3 系统实现
# ============================================================
h1('3','系统实现')
h2('3.1','系统的运行环境')
para('考虑到开发机为 Windows 11、无管理员权限，全部基础软件采用免安装绿色版部署到同一目录并配置用户级环境变量，MySQL 以便携进程方式运行（不安装系统服务）。系统软硬件与软件版本环境如表 3-1、表 3-2 所示。')
table(['项目','配置'],
 [['操作系统','Windows 11 专业版 64 位'],['CPU / 内存','AMD Ryzen 7 6800H / 16GB'],['磁盘','数据与软件部署于数据盘（约 500GB 可用）']],
 caption='表 3-1  硬件环境', widths=[3.5,11.5])
table(['软件','版本','用途'],
 [['JDK (Temurin)','17.0.20','后端运行环境'],['Apache Maven','3.9.16','后端依赖管理与打包（阿里云镜像）'],
  ['Python','3.8.10','数据分析与机器学习运行时'],['Apache Spark','3.5.6 (Hadoop3)','分布式计算（本地多线程）'],
  ['MySQL','8.0.29','结果数据持久化（便携进程，端口 3306）'],['Node.js','20.18.1 / npm 10.8','前端构建（npmmirror 镜像）'],
  ['PySpark / pandas / numpy','3.5.6 / 2.0.3 / 1.24.4','数据处理'],
  ['scikit-learn / xgboost / mlxtend','1.3.2 / 2.0.3 / 0.23.1','KMeans、XGBoost、Apriori'],
  ['Spring Boot / Spring JDBC','3.2.5','后端框架与数据访问'],
  ['Vue / Element Plus / ECharts','3.4 / 2.7 / 5.5','前端框架、组件库、图表库']],
 caption='表 3-2  软件运行环境', widths=[4.6,4.0,6.4])

# 动态结论
ratio = dict(zip(beh.behavior_type, beh.ratio_pct))
seg = {r['segment']: r for _,r in rfm_seg.iterrows()}
h2('3.2','各功能模块的运行效果')

para('3.2.1 仪表盘总览', bold=True, indent=False, size=12.5)
para('仪表盘总览页顶部以 KPI 卡片展示 11 月累计访问量 %s、全周期累计购买量 %s、有购买行为用户 %s 人、高价值客户 %s 人、前 30%% 用户购买占比 %s%%、购买预测模型 AUC 等核心指标；下方以双轴柱线图展示每日访问量与累计访问量、每日购买量与累计购买量，以环形图展示行为类型占比，并以堆叠柱状展示 24 小时行为分布，运行效果如图 3-1，关键趋势如图 3-2~图 3-3。' % (
    f"{int(metrics.get('nov_total_pv',551538)):,}", f"{int(metrics.get('total_buy',20359)):,}",
    f"{int(metrics.get('buy_user_total',6689)):,}", int(metrics.get('rfm_high_value_users',497)),
    metrics.get('top30_buy_share',60.94)))
figure(os.path.join(UISHOT,'01_overview.png'),'图 3-1  仪表盘总览页面',15.5)
figure(os.path.join(FIG,'02_nov_pv_cum.png'),'图 3-2  11 月每日访问量与累计访问量',13.5)
figure(os.path.join(FIG,'03_buy_cum.png'),'图 3-3  每日购买量与累计购买量',13.5)
para('由图可见，访问量在 11 月 25—30 日整体平稳、日均约 9 万 PV，累计 PV 达到 551,538；行为构成中浏览占绝对主导（%.2f%%），加购 %.2f%%、收藏 %.2f%%、购买仅 %.2f%%，符合电商“高浏览、低转化”的漏斗特征。' % (
    ratio.get('pv',89.606), ratio.get('cart',5.547), ratio.get('fav',2.81), ratio.get('buy',2.037)))

para('3.2.2 行为模式分析', bold=True, indent=False, size=12.5)
para('行为模式分析页提供“星期×小时”活跃热力图、各星期日均行为量、会话级漏斗、点击流路径转化率、行为流转桑基图、Top10 商品以及类目关联规则表，运行效果如图 3-4，主要分析图如图 3-5~图 3-8。')
figure(os.path.join(UISHOT,'02_behavior.png'),'图 3-4  行为模式分析页面',15.5)
figure(os.path.join(FIG,'05_heatmap.png'),'图 3-5  用户活跃时段热力图',15.0)
para('热力图显示用户活跃呈现明显的“晚高峰”特征：20—22 点最活跃，且周六、周日整体活跃水平高于工作日（周末日均约 12.1 万条、工作日约 10 万条），说明用户多在晚间和周末进行购物浏览。')
figure(os.path.join(FIG,'07_funnel.png'),'图 3-6  会话级行为漏斗',11.0)
figure(os.path.join(FIG,'08_path_conversion.png'),'图 3-7  不同点击流路径转化率',12.5)
# 路径转化文字
pc = dict(zip(pathc.path, pathc.conversion_pct))
para('以 30 分钟无行为为切分阈值共得到 164,076 个会话。路径转化率分析表明：单纯“浏览→购买”转化率仅 %.2f%%，而经过“浏览→加购→收藏→购买”的深度路径转化率提升至 %.2f%%，“浏览→收藏→购买”“浏览→加购→购买”也分别达到 %.2f%%、%.2f%%，说明收藏与加购是购买的强前置信号，对高意向用户做召回可显著提升转化。' % (
    pc.get('浏览→购买',7.605), pc.get('浏览→加购→收藏→购买',16.399),
    pc.get('浏览→收藏→购买',11.515), pc.get('浏览→加购→购买',11.655)))
figure(os.path.join(FIG,'09_top_items.png'),'图 3-8  浏览量/购买量 Top10 商品对比',15.0)
figure(os.path.join(FIG,'10_apriori.png'),'图 3-9  类目关联规则 Top15（提升度）',13.0)
para('使用 Apriori 算法对会话内类目共现进行关联挖掘（最小支持度 0.01、置信度 0.3），共形成 58,651 个购物篮、451 个频繁项集，筛选出 50 条提升度 Lift>1 的有效规则，最高提升度达 10.38，可用于“搭配购/买了又买”的关联推荐。')

para('3.2.3 RFM 用户分群管理', bold=True, indent=False, size=12.5)
para('RFM 页以分群卡片展示各群人数、占比、R/F/M 均值与差异化运营策略，以 R-F 四象限散点展示用户分布，并提供经典八分法柱状图与可按分群筛选、分页的明细表，运行效果如图 3-10。')
figure(os.path.join(UISHOT,'03_rfm.png'),'图 3-10  RFM 分群管理页面',15.5)
figure(os.path.join(FIG,'11_rfm_cluster.png'),'图 3-11  R-F 散点与 K-Means 分群占比',15.0)
hv = seg.get('高价值客户'); gm = seg.get('一般维持客户'); lv = seg.get('低价值/流失客户')
para('数据集中无金额字段，故 M 以“购买不同商品数”代理（已在报告中注明口径）。对 %s 名有购买行为的用户计算 R/F/M 并做五分位评分，结合轮廓系数（k=2 为 0.5413、k=3 为 0.4721）与业务可解释性取 k=3，得到三类客户：高价值客户 %s 人（%.2f%%）、一般维持客户 %s 人（%.2f%%）、低价值/流失客户 %s 人（%.2f%%），并分别给出 VIP 维护、优惠券召回、流失唤醒策略。' % (
    int(metrics.get('rfm_users',6689)),
    int(hv['users']) if hv is not None else 497, float(hv['ratio_pct']) if hv is not None else 7.43,
    int(gm['users']) if gm is not None else 4167, float(gm['ratio_pct']) if gm is not None else 62.30,
    int(lv['users']) if lv is not None else 2025, float(lv['ratio_pct']) if lv is not None else 30.27))
figure(os.path.join(FIG,'12_rfm_octant.png'),'图 3-12  RFM 经典八分法用户数量',12.5)

para('3.2.4 预测模型监控', bold=True, indent=False, size=12.5)
para('预测模型监控页展示 XGBoost 的 AUC、准确率、精确率、召回率、F1 指标卡、ROC 曲线、混淆矩阵与特征重要性，下方提供按购买概率降序的用户排行榜（分页）以及 ALS 个性化推荐查询，运行效果如图 3-13、图 3-14。')
figure(os.path.join(UISHOT,'04_predict.png'),'图 3-13  预测模型监控页面（模型性能）',15.5)
figure(os.path.join(FIG,'13_xgb.png'),'图 3-14  ROC、混淆矩阵与特征重要性',15.5)
para('XGBoost 以 11-25~12-01 为观察期构造 20 维用户-商品特征、以 12-02~12-03 是否购买为标签，按 1:20 负采样后训练。测试集 AUC=%.4f、准确率=%.4f、召回率=%.4f、F1=%.4f，混淆矩阵为 TN=%s/FP=%s/FN=%s/TP=%s；特征重要性显示“是否加购(has_cart)、加购次数、活跃天数”等对购买预测贡献最大，与业务直觉一致。模型在保证准确率的同时召回了约六成真实购买，可用于高意向人群圈选。' % (
    xgbm.get('auc',0.8506), xgbm.get('accuracy',0.9089), xgbm.get('recall',0.6047), xgbm.get('f1',0.3869),
    int(xgbm.get('tn',3982)), int(xgbm.get('fp',327)), int(xgbm.get('fn',85)), int(xgbm.get('tp',130))))
figure(os.path.join(UISHOT,'05_predict_rank.png'),'图 3-14  购买概率排行榜与 ALS 个性化推荐',15.5)
para('ALS 采用隐式反馈，将浏览/收藏/加购/购买映射为 1/3/4/5 的偏好权重，过滤长尾商品后训练（rank=12、regParam=0.06、alpha=1.0），为每名用户生成 Top10 推荐；对无历史交互的冷启动用户以全局热门商品兜底（共识别 15 名冷启动用户）。需要说明的是，数据集不含价格与优惠字段，故推荐卡片以预测偏好分与历史浏览/购买热度代替价格信息。')

h2('3.3','各功能模块的核心代码')
para('（1）数据加载与清洗：派生时间维度、按时间窗口过滤噪声、去重并缓存为 Parquet。')
code("""
df = spark.read.csv(raw, header=False, sep=',',
    schema='user_id long,item_id long,category_id long,behavior_type string,ts long')
df = (df.withColumn('dt', F.from_unixtime('ts','yyyy-MM-dd'))
        .withColumn('hour', F.hour(F.from_unixtime('ts')))
        .withColumn('weekday', F.dayofweek(F.to_date('dt')))   # 1=周日
        .filter((F.col('dt') >= '2017-11-25') & (F.col('dt') <= '2017-12-03'))
        .dropDuplicates(['user_id','item_id','behavior_type','ts']))
df.write.mode('overwrite').parquet(PARQUET)   # 一次清洗，后续脚本复用
""", '代码 3-1  01_load_clean.py（清洗与缓存）')
para('（2）使用 Spark SQL 窗口函数计算累计访问量。')
code("""
w = Window.orderBy('date').rowsBetween(Window.unboundedPreceding, Window.currentRow)
stat = daily.groupBy('date').agg(F.sum('pv').alias('pv_cnt'))
stat = stat.withColumn('cum_pv', F.sum('pv_cnt').over(w)).orderBy('date')
""", '代码 3-2  02_behavior_stats.py（窗口累计）')
para('（3）RFM 五分位评分与 K-Means 聚类。')
code("""
for col, score in [('recency','r_score'),('frequency','f_score'),('monetary','m_score')]:
    detail[score] = pd.qcut(detail[col].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
km = KMeans(n_clusters=3, random_state=42, n_init=10)
detail['cluster'] = km.fit_predict(detail[['r_score','f_score','m_score']])
""", '代码 3-3  04_rfm.py（五分位评分 + KMeans）')
para('（4）XGBoost 购买意向二分类训练与评估。')
code("""
param = {'objective':'binary:logistic','eval_metric':'auc',
         'max_depth':5,'eta':0.1,'subsample':0.9,'colsample_bytree':0.9}
model = xgb.train(param, xgb.DMatrix(X_tr, label=y_tr), num_boost_round=300,
                  evals=[(xgb.DMatrix(X_va,y_va),'va')], early_stopping_rounds=30)
proba = model.predict(xgb.DMatrix(X_te))
""", '代码 3-4  05_intent_xgboost.py（模型训练）')
para('（5）Spark MLlib ALS 隐式反馈协同过滤。')
code("""
als = ALS(rank=12, maxIter=12, regParam=0.06, alpha=1.0, nonnegative=True,
          implicitPrefs=True, coldStartStrategy='drop',
          userCol='user_id', itemCol='item_id', ratingCol='rating')
model = als.fit(inter)                       # inter: 用户-商品偏好权重
recs  = model.recommendForAllUsers(10)       # 每用户 Top10
""", '代码 3-5  06_als_recommend.py（ALS 推荐）')
para('（6）Spring Boot 控制器以统一响应返回分页结果（表白名单 + 反引号排序防注入）。')
code("""
@GetMapping("/xgb-rank")
public ApiResult<Map<String,Object>> xgbRank(
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int size) {
    return ApiResult.success(service.page("xgb_predict_rank", null, null, "rank asc", page, size));
}
""", '代码 3-6  PredictController.java（REST 接口）')
para('（7）Vue3 组合式 API + ECharts 构建双轴趋势图。')
code("""
const optPv = computed(() => ({
  xAxis: { type:'category', data: pvCum.value.map(d => d.date) },
  yAxis: [{ type:'value', name:'当日PV' }, { type:'value', name:'累计PV' }],
  series: [
    { type:'bar',  data: pvCum.value.map(d => d.pv_cnt) },
    { type:'line', yAxisIndex:1, smooth:true, data: pvCum.value.map(d => d.cum_pv) }]
}))
""", '代码 3-7  Overview.vue（ECharts 配置）')

# ============================================================
# 4 个人负责内容
# ============================================================
h1('4','个人负责内容')
para('本项目由 5 人小组协同完成，组长程少锋（本人），组员陈俊勇、张迅、张致臻、林子涵。小组按“数据层—分析建模层—服务与展示层”进行模块分工：陈俊勇负责数据清洗与行为统计及 MySQL 结果库设计，张迅负责行为模式分析（会话漏斗、路径转化、Apriori 关联），张致臻负责 RFM 分群与 XGBoost 购买预测建模，林子涵负责 ALS 推荐与 Vue3 前端可视化，本人负责总体架构、开发环境、Spring Boot 后端、系统集成联调与报告统稿。下面重点说明本人（程少锋）承担的工作。')
para('（1）总体架构与开发环境。设计“数据源—存储—计算—接口—展示”五层架构，确定 PySpark + MySQL + Spring Boot + Vue3 的技术选型；在无管理员权限、刚重装的 Windows 机器上完成 JDK17、Python3.8、Spark3.5.6（含 winutils）、MySQL8、Maven、Node.js 的免安装绿色部署，配置用户级环境变量与国内镜像，将 MySQL 以便携进程方式运行，并通过 PySpark 冒烟测试打通整条技术链路，为全组提供统一、可复现的开发环境。')
para('（2）公共数据框架与后端服务。设计 common.py 公共框架，统一 SparkSession 构建、JDBC 注入与“MySQL + CSV + JSON”结果三写规范，使各组员产出的分析结果口径一致、自动落库；基于 Spring Boot 3 + JdbcTemplate 实现 Overview/Dashboard/Rfm/Predict 四个 REST 控制器，设计统一响应结构、全局跨域，并通过表名白名单、排序列反引号规范化与预编译参数实现 SQL 注入防护，同时补齐分页与默认排序逻辑。')
para('（3）系统集成、联调与统稿。制定数据表与接口契约，将四位组员的分析结果表逐一接入后端接口与前端页面；负责前后端联调，修复了 MySQL 8 中 rank 保留字导致排序失效、结果表无序导致 ROC 曲线缠绕、ECharts 热力图必须搭配 visualMap 等实际问题；编写一键分析、一键启停脚本，完成系统整体测试，并负责本实践报告的结构设计与统稿。')
para('（4）本人参与攻克的主要技术难点。')
bullets([
 'Windows 无管理员权限：改用绿色软件 + 用户级环境变量 + MySQL 便携进程，形成可逆、可复制、全组统一的部署方案；',
 '多人协作口径统一：通过 common.py 公共框架与统一结果表/接口契约，保证不同成员模块可无缝集成；',
 '多次迭代的计算效率：清洗结果缓存 Parquet，避免各分析模块重复清洗百万行数据；',
 '前后端联调：解决 MySQL 8 保留字排序、结果表无序导致 ROC 缠绕、ECharts 热力图必须搭配 visualMap 等问题，保证图表准确渲染。'])

h1('5','项目贡献度与参与度')
h2('5.1','贡献度')
para('本项目由 5 人小组协同完成，各成员贡献度分工如表 5-1 所示。')
table(['成员','姓名','简述主要负责部分'],
 [['组长','程少锋','总体架构设计、开发环境搭建、Spring Boot 后端开发、系统集成联调与报告统稿'],
  ['组员','陈俊勇','数据加载清洗与行为统计（01–02）、MySQL 结果库与表结构设计'],
  ['组员','张迅','行为模式分析：会话切分、行为漏斗、点击流路径转化与 Apriori 关联规则挖掘（03a/03b）'],
  ['组员','张致臻','RFM 用户价值分群（五分位评分+KMeans+八分法）、XGBoost 购买意向预测建模（04/05）'],
  ['组员','林子涵','ALS 协同过滤推荐（06）、Vue3+Element Plus+ECharts 前端可视化四页面']],
 caption='表 5-1  项目贡献度表', widths=[1.6,2.2,11.2])
h2('5.2','参与度')
para('本人（程少锋）对除本人外其他四位成员的参与度互评分（10 分制）如表 5-2 所示。四位成员均积极参与、按时完成各自模块并主动配合集成联调，故均给予满分。')
table(['除本人外其他成员姓名','互评分（10 分制）'],
 [['陈俊勇','10'],['张迅','10'],['张致臻','10'],['林子涵','10']],
 caption='表 5-2  参与度互评表', widths=[8.0,7.0])

h1('6','项目总结')
h2('6.1','知识点总结')
para('项目综合运用了大数据与全栈开发的多类知识点：')
bullets([
 '大数据计算：PySpark / Spark SQL、DataFrame 算子、窗口函数（累计、排名）、Parquet 列式缓存、JDBC 读写、本地多线程调度；',
 '数据分析：行为漏斗、会话切分、点击流路径、用户活跃时段与周末效应、二八分布（前 30% 用户贡献约 61% 购买）；',
 '数据挖掘：Apriori 频繁项集与关联规则（支持度/置信度/提升度）、RFM 模型、五分位评分、K-Means 聚类与轮廓系数选 k、经典八分法；',
 '机器学习：XGBoost 二分类、观察期/标签期划分、特征工程、负采样、AUC/精确率/召回率/F1/ROC/混淆矩阵、特征重要性；',
 '推荐系统：协同过滤、ALS 矩阵分解、隐式反馈、冷启动与热门兜底、Precision@K/NDCG 排序评估；',
 '后端：Spring Boot 3、分层架构、RESTful、JdbcTemplate、统一响应与全局跨域、SQL 注入防护、分页；',
 '前端：Vue3 组合式 API、Vite、Vue Router、Element Plus、ECharts、Axios 拦截器与开发代理；',
 '工程化：绿色免安装部署、国内镜像加速、一键重跑/启停脚本、结果多份导出、可复现流水线。'])
h2('6.2','项目执行总结')
para('执行过程遵循“探查—约束—证据—实现—验证—交付”的流程：先吃透指导书与数据口径，再搭建并验证环境，随后按 01→07 的顺序逐步实现分析流水线，每个脚本都真实运行、结果落库并导出，最后完成前后端开发与联调，所有页面和接口均在浏览器与接口层做过实测。项目最终得到一系列有业务价值的结论：用户活跃集中在晚间与周末；收藏、加购显著提升购买转化；用户价值呈明显分层，高价值客户仅占 7.43% 却具备最高消费频次；XGBoost 购买预测 AUC 达 0.85，ALS 可生成个性化推荐。')
para('不足与改进方向：其一，受算力与匿名下载限制，本次使用百万行样本，后续可在全量一亿行上以 Spark 集群验证扩展性；其二，数据集缺少金额、价格与优惠字段，RFM 的 M 与推荐卡片价格只能以代理指标或占位呈现，接入订单金额后可进一步做 CLV 与客单价分析；其三，ALS 在极稀疏数据上 Precision@10 偏低，后续可引入内容特征与混合推荐、并做更细的超参与负反馈优化；其四，前端可增加时间范围联动与更多下钻分析。总体而言，项目完整跑通了大数据分析系统从数据到决策的全链路，达到了课程实践的预期目标。')
h2('6.3','团队合作总结')
para('本项目由程少锋、陈俊勇、张迅、张致臻、林子涵五人协作完成。团队按数据工程、行为分析、用户建模、推荐与前端、架构与后端的边界划分模块，既保证每人有明确负责的主线，又通过统一的数据表与接口契约降低耦合：组长先搭建公共环境与 common.py 框架、约定结果表规范，组员在此基础上并行开发各自分析模块，最后由组长统一集成到后端接口与前端页面并统稿。协作过程中，我们通过任务清单跟踪进度、定期对齐数据口径与字段命名，在样本不均衡、ALS 稀疏数据、前后端联调等问题上共同讨论、分头验证，使各模块能够顺利拼接为完整系统。这次实践让我们体会到：清晰的接口契约与统一规范是多人协作的前提，模块化解耦让并行开发成为可能，而及时的集成与测试则是项目按时交付的保障；同时也锻炼了团队沟通、任务拆解与协同交付复杂系统的能力。')

# 页脚页码
def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(); fld1=OxmlElement('w:fldChar'); fld1.set(qn('w:fldCharType'),'begin')
    instr=OxmlElement('w:instrText'); instr.set(qn('xml:space'),'preserve'); instr.text='PAGE'
    fld2=OxmlElement('w:fldChar'); fld2.set(qn('w:fldCharType'),'end')
    run._r.append(fld1); run._r.append(instr); run._r.append(fld2); _font(run,size=9)
add_page_number(sec)

doc.save(OUT_DOCX)
print('REPORT DONE paragraphs=', len(doc.paragraphs), 'tables=', len(doc.tables))
print('FILE:', OUT_DOCX)
