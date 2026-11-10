<template>
  <div v-loading="loading">
    <div class="bar">
      <span class="page-title">仪表盘总览</span>
      <el-date-picker v-model="dateRange" type="daterange" size="small" range-separator="至"
        start-placeholder="开始日期" end-placeholder="结束日期" style="width:260px" @change="filterTrend"/>
      <el-button size="small" type="primary" :icon="Refresh" @click="loadAll">刷新数据</el-button>
    </div>

    <!-- KPI -->
    <el-row :gutter="14">
      <el-col :span="4" v-for="k in kpis" :key="k.label">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-num" :style="{color:k.color}">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="section-gap">
      <el-col :span="14">
        <el-card header="2017年11月 每日访问量与累计访问量" class="chart-card">
          <EChart :option="optPv" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card header="用户行为类型占比" class="chart-card">
          <EChart :option="optRatio" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :span="14">
        <el-card header="每日购买量与累计购买量（11月/12月）" class="chart-card">
          <EChart :option="optBuy" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card header="各行为24小时分布（堆叠）" class="chart-card">
          <EChart :option="optHour" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import http from '../api/http'
import EChart from '../components/EChart.vue'

const loading = ref(false)
const dateRange = ref(null)
const metrics = ref({})
const pvCum = ref([])
const buyCum = ref([])
const ratio = ref([])
const hour = ref([])

const fmt = (v, d = 0) => (v == null ? '-' : Number(v).toLocaleString('en-US', { maximumFractionDigits: d }))
const kpis = computed(() => [
  { label: '11月累计访问量(PV)', value: fmt(metrics.value.nov_total_pv), color: '#2e6be6' },
  { label: '全周期累计购买量', value: fmt(metrics.value.total_buy), color: '#e15759' },
  { label: '有购买行为用户', value: fmt(metrics.value.buy_user_total), color: '#36a269' },
  { label: '高价值客户数', value: fmt(metrics.value.rfm_high_value_users), color: '#f28e2b' },
  { label: '前30%用户购买占比', value: fmt(metrics.value.top30_buy_share, 2) + '%', color: '#925fb3' },
  { label: '购买预测模型AUC', value: fmt(metrics.value.xgb_auc, 4), color: '#17a2b8' }
])

async function loadAll() {
  loading.value = true
  try {
    const [m, p, b, r, h] = await Promise.all([
      http.get('/overview/metrics'),
      http.get('/dashboard/nov-pv-cum'),
      http.get('/dashboard/buy-cum'),
      http.get('/overview/behavior-ratio'),
      http.get('/dashboard/hour')
    ])
    metrics.value = m; pvCum.value = p; buyCum.value = b; ratio.value = r; hour.value = h
  } finally { loading.value = false }
}
function filterTrend() { /* 时间范围筛选在前端对趋势数据切片 */ }

const BEH_COLOR = { pv: '#4e79a7', fav: '#59a14f', cart: '#f28e2b', buy: '#e15759' }
const BEH_CN = { pv: '浏览', fav: '收藏', cart: '加购', buy: '购买' }

const optPv = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['当日访问量', '累计访问量'], top: 0 },
  grid: { left: 56, right: 56, top: 36, bottom: 48 },
  xAxis: { type: 'category', data: pvCum.value.map(d => d.date), axisLabel: { rotate: 30 } },
  yAxis: [
    { type: 'value', name: '当日PV' },
    { type: 'value', name: '累计PV' }
  ],
  series: [
    { name: '当日访问量', type: 'bar', data: pvCum.value.map(d => d.pv_cnt), itemStyle: { color: '#2e6be6' } },
    { name: '累计访问量', type: 'line', yAxisIndex: 1, smooth: true, data: pvCum.value.map(d => d.cum_pv), itemStyle: { color: '#e15759' } }
  ]
}))

const optBuy = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['当日购买', '全局累计', '当月累计'], top: 0 },
  grid: { left: 56, right: 30, top: 36, bottom: 48 },
  xAxis: { type: 'category', data: buyCum.value.map(d => d.date), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value' },
  series: [
    { name: '当日购买', type: 'bar', data: buyCum.value.map(d => d.buy_cnt), itemStyle: { color: '#36a269' } },
    { name: '全局累计', type: 'line', smooth: true, data: buyCum.value.map(d => d.total_cum_buy), itemStyle: { color: '#e15759' } },
    { name: '当月累计', type: 'line', smooth: true, lineStyle: { type: 'dashed' }, data: buyCum.value.map(d => d.month_cum_buy), itemStyle: { color: '#f28e2b' } }
  ]
}))

const optRatio = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie', radius: ['42%', '68%'], center: ['50%', '46%'],
    label: { formatter: '{b}\n{d}%' },
    data: ratio.value.map(d => ({ name: d.behavior_cn, value: d.cnt, itemStyle: { color: BEH_COLOR[d.behavior_type] } }))
  }]
}))

const optHour = computed(() => {
  const hs = hour.value.map(d => d.hour)
  const mk = (k) => hour.value.map(d => d[k])
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { top: 0, data: ['浏览', '收藏', '加购', '购买'] },
    grid: { left: 56, right: 20, top: 36, bottom: 30 },
    xAxis: { type: 'category', data: hs },
    yAxis: { type: 'value' },
    series: ['pv', 'fav', 'cart', 'buy'].map(k => ({
      name: BEH_CN[k], type: 'bar', stack: 'total', data: mk(k), itemStyle: { color: BEH_COLOR[k] }
    }))
  }
})

onMounted(loadAll)
</script>

<style scoped>
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.kpi-card { text-align: center; }
:deep(.el-card__body) { padding: 16px; }
</style>
