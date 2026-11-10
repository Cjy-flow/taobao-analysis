<template>
  <div v-loading="loading">
    <div class="bar">
      <span class="page-title">预测模型监控</span>
      <el-tag type="success">XGBoost v1.0（观察期11-25~12-01 / 标签期12-02~12-03）</el-tag>
      <el-button size="small" :icon="Download" @click="exportCsv">导出预测结果CSV</el-button>
    </div>

    <!-- 模型性能指标 -->
    <el-row :gutter="14">
      <el-col :span="4" v-for="m in metricCards" :key="m.name">
        <el-card shadow="hover" class="metric-card">
          <div class="kpi-num" :style="{color:m.color}">{{ m.value }}</div>
          <div class="kpi-label">{{ m.name }}</div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card shadow="hover" class="metric-card">
          <div class="kpi-num" style="color:#925fb3">{{ alsP }}</div>
          <div class="kpi-label">ALS Precision@10</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="section-gap">
      <el-col :span="7">
        <el-card header="ROC 曲线" class="chart-card"><EChart :option="optRoc" class="chart-box sm"/></el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="混淆矩阵" class="chart-card">
          <div class="cm-wrap">
            <div class="cm-corner"></div>
            <div class="cm-colh">预测负</div>
            <div class="cm-colh">预测正</div>
            <div class="cm-rowh">实际负</div>
            <div class="cm-cell ok"><div class="cm-v">{{ cmMap['真负TN'] ?? '—' }}</div><div class="cm-t">TN 真负</div></div>
            <div class="cm-cell bad2"><div class="cm-v">{{ cmMap['假正FP'] ?? '—' }}</div><div class="cm-t">FP 假正</div></div>
            <div class="cm-rowh">实际正</div>
            <div class="cm-cell bad"><div class="cm-v">{{ cmMap['假负FN'] ?? '—' }}</div><div class="cm-t">FN 假负</div></div>
            <div class="cm-cell ok"><div class="cm-v">{{ cmMap['真正TP'] ?? '—' }}</div><div class="cm-t">TP 真正</div></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="9">
        <el-card header="特征重要性 Top12（Gain）" class="chart-card"><EChart :option="optFi" class="chart-box sm"/></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :span="13">
        <el-card header="用户购买概率排行榜（按概率降序）" class="chart-card">
          <el-table :data="rankRows" size="small" stripe height="360">
            <el-table-column prop="rank" label="排名" width="70" sortable/>
            <el-table-column prop="user_id" label="用户ID" width="100"/>
            <el-table-column prop="item_id" label="商品ID" width="110"/>
            <el-table-column prop="category_id" label="类目ID" width="110"/>
            <el-table-column label="购买概率" prop="buy_prob" sortable>
              <template #default="{row}">
                <el-progress :percentage="Math.round(row.buy_prob*100)" :stroke-width="14"
                  :color="row.buy_prob>0.7?'#e15759':(row.buy_prob>0.4?'#f28e2b':'#36a269')"/>
              </template>
            </el-table-column>
            <el-table-column label="行为信号" width="150">
              <template #default="{row}">
                <el-tag v-if="row.has_cart" size="small" type="warning">加购{{row.ui_cart}}</el-tag>
                <el-tag v-if="row.has_fav" size="small" type="success" style="margin-left:4px">收藏</el-tag>
                <el-tag v-if="!row.has_cart&&!row.has_fav" size="small">仅浏览</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination class="pager" background layout="total,prev,pager,next" :total="rankTotal"
            :page-size="rankSize" v-model:current-page="rankPage" @current-change="loadRank"/>
        </el-card>
      </el-col>

      <el-col :span="11">
        <el-card class="chart-card">
          <template #header>
            <div class="tbl-head">
              <span>ALS 个性化推荐（协同过滤）</span>
              <div>
                <el-input-number v-model="userId" :min="1" size="small" controls-position="right" style="width:120px"/>
                <el-button size="small" type="primary" @click="loadRecs">查询推荐</el-button>
              </div>
            </div>
          </template>
          <el-empty v-if="!recs.length" description="输入用户ID查询Top10推荐，冷启动用户走热门兜底" :image-size="60"/>
          <div v-else class="rec-grid">
            <el-card v-for="r in recs" :key="r.rank" shadow="hover" class="rec-item">
              <div class="rec-rank">No.{{ r.rank }}</div>
              <div class="rec-id">商品 {{ r.item_id }}</div>
              <div class="muted">类目 {{ r.category_id }}</div>
              <div class="rec-score">预测偏好分 {{ Number(r.score).toFixed(4) }}</div>
              <div class="muted">历史浏览{{r.i_pv}} / 购买{{r.i_buy}}</div>
            </el-card>
          </div>
          <el-divider>冷启动热门兜底商品</el-divider>
          <el-table :data="popular" size="small">
            <el-table-column prop="item_id" label="商品ID"/>
            <el-table-column prop="hot" label="热度" sortable/>
            <el-table-column prop="buy" label="购买数" sortable/>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import http from '../api/http'
import EChart from '../components/EChart.vue'

const loading = ref(false)
const xgbMetrics = ref([]), roc = ref([]), cm = ref([]), fi = ref([]), alsMetrics = ref([])
const rankRows = ref([]), rankTotal = ref(0), rankPage = ref(1), rankSize = ref(10)
const recs = ref([]), popular = ref([]), userId = ref(1)

const metricMap = computed(() => Object.fromEntries(xgbMetrics.value.map(m => [m.metric, Number(m.value)])))
const metricCards = computed(() => [
  { name: 'AUC', value: (metricMap.value.auc ?? 0).toFixed(4), color: '#2e6be6' },
  { name: '准确率', value: (metricMap.value.accuracy ?? 0).toFixed(4), color: '#36a269' },
  { name: '精确率', value: (metricMap.value.precision ?? 0).toFixed(4), color: '#f28e2b' },
  { name: '召回率', value: (metricMap.value.recall ?? 0).toFixed(4), color: '#e15759' },
  { name: 'F1', value: (metricMap.value.f1 ?? 0).toFixed(4), color: '#925fb3' }
])
const alsP = computed(() => {
  const r = alsMetrics.value.find(m => m.metric === 'als_precision_at10')
  return r ? Number(r.value).toFixed(4) : '-'
})
// 混淆矩阵：cell -> count
const cmMap = computed(() => Object.fromEntries(cm.value.map(x => [x.cell, x.count])))

async function load() {
  loading.value = true
  try {
    const [m, r, c, f, am, pop] = await Promise.all([
      http.get('/predict/xgb-metrics'), http.get('/predict/xgb-roc'),
      http.get('/predict/xgb-confusion'), http.get('/predict/xgb-feature'),
      http.get('/predict/als-metrics'), http.get('/predict/als-popular')
    ])
    xgbMetrics.value = m; roc.value = r; cm.value = c; fi.value = f; alsMetrics.value = am; popular.value = pop
    loadRank(); loadRecs()
  } finally { loading.value = false }
}
async function loadRank() {
  try {
    const res = await http.get('/predict/xgb-rank', { params: { page: rankPage.value, size: rankSize.value } })
    console.log('[loadRank]', res && typeof res, res && Object.keys(res), 'rows=', res && res.rows && res.rows.length)
    rankRows.value = res.rows || []
    rankTotal.value = res.total || 0
  } catch (e) {
    console.error('[loadRank] failed', e)
  }
}
async function loadRecs() {
  recs.value = await http.get('/predict/als-recs', { params: { userId: userId.value } })
}
function exportCsv() {
  const head = 'rank,user_id,item_id,category_id,buy_prob\n'
  const body = rankRows.value.map(r => [r.rank, r.user_id, r.item_id, r.category_id, r.buy_prob].join(',')).join('\n')
  const blob = new Blob(['\ufeff' + head + body], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = '购买概率预测结果.csv'; a.click()
}

const optRoc = computed(() => {
  const pts = [...roc.value].sort((a, b) => (a.fpr - b.fpr) || (a.tpr - b.tpr))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 46, right: 20, top: 20, bottom: 36 },
    xAxis: { type: 'value', name: 'FPR', min: 0, max: 1 },
    yAxis: { type: 'value', name: 'TPR', min: 0, max: 1 },
    series: [
      { type: 'line', data: pts.map(d => [d.fpr, d.tpr]), showSymbol: false, smooth: false, areaStyle: { opacity: .12 }, itemStyle: { color: '#e15759' }, lineStyle: { width: 2 } },
      { type: 'line', data: [[0, 0], [1, 1]], showSymbol: false, lineStyle: { type: 'dashed', color: '#bbb' } }
    ]
  }
})

const optFi = computed(() => {
  const top = fi.value.slice(0, 12)
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 110, right: 30, top: 10, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: top.map(d => d.feature).reverse() },
    series: [{ type: 'bar', data: top.map(d => Number(d.gain)).reverse(), itemStyle: { color: '#36a269' } }]
  }
})

onMounted(load)
</script>

<style scoped>
.bar { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.metric-card { text-align:center; }
.tbl-head { display:flex; justify-content:space-between; align-items:center; }
.pager { margin-top:10px; justify-content:flex-end; }
.rec-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; max-height:300px; overflow:auto; }
.rec-item :deep(.el-card__body){ padding:10px; }
.rec-rank { font-weight:700; color:#2e6be6; }
.rec-id { font-weight:600; margin:2px 0; }
.rec-score { color:#e15759; font-size:12px; margin:2px 0; }
/* 混淆矩阵 2x2 */
.cm-wrap { display:grid; grid-template-columns:48px 1fr 1fr; gap:6px; align-items:stretch; padding:8px 2px; }
.cm-corner { }
.cm-colh { text-align:center; font-weight:600; color:#606266; padding-bottom:4px; font-size:13px; }
.cm-rowh { display:flex; align-items:center; justify-content:center; font-weight:600; color:#606266; font-size:13px; }
.cm-cell { border-radius:8px; padding:14px 4px; text-align:center; color:#fff; }
.cm-cell.ok { background:#2f9e44; }
.cm-cell.bad { background:#e15759; }
.cm-cell.bad2 { background:#f28e2b; }
.cm-v { font-size:22px; font-weight:700; }
.cm-t { font-size:11px; opacity:.92; margin-top:3px; }
</style>
