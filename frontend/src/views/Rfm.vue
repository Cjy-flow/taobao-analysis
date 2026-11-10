<template>
  <div v-loading="loading">
    <div class="bar">
      <span class="page-title">RFM分群管理</span>
      <span class="muted">R/F/M 五分位评分 · K-Means(k=3)聚类 · 经典八分法</span>
    </div>

    <!-- 分群结果卡片 -->
    <el-row :gutter="14">
      <el-col :span="8" v-for="c in summary" :key="c.cluster">
        <el-card shadow="hover" class="seg-card">
          <div class="seg-head" :style="{borderTopColor: colorOf(c.cluster)}">
            <span class="seg-name">{{ c.segment }}</span>
            <el-tag effect="dark" :color="colorOf(c.cluster)" style="border:none">{{ c.ratio_pct }}%</el-tag>
          </div>
          <div class="seg-users">用户数：<b>{{ c.users }}</b></div>
          <div class="seg-avg">平均 R={{ c.recency_avg }} 天 ｜ F={{ c.frequency_avg }} ｜ M={{ c.monetary_avg }}</div>
          <div class="seg-strategy">运营策略：{{ c.strategy }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14" class="section-gap">
      <el-col :span="14">
        <el-card header="R-F 用户价值四象限散点（颜色区分分群）" class="chart-card">
          <EChart :option="optScatter" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card header="RFM 经典八分法用户数量" class="chart-card">
          <EChart :option="optOctant" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card">
      <template #header>
        <div class="tbl-head">
          <span>分群明细（支持分群筛选与分页）</span>
          <div>
            <el-select v-model="clusterFilter" placeholder="全部分群" clearable size="small" style="width:160px" @change="page=1;loadDetail()">
              <el-option v-for="c in summary" :key="c.cluster" :label="c.segment" :value="c.cluster"/>
            </el-select>
            <el-slider v-model="rThreshold" :min="1" :max="5" :marks="{1:'R≥1',5:'R≥5'}" style="width:200px;margin-left:16px" @change="page=1"/>
          </div>
        </div>
      </template>
      <el-table :data="filteredRows" size="small" stripe height="380">
        <el-table-column prop="user_id" label="用户ID" width="110" sortable/>
        <el-table-column prop="recency" label="R最近间隔(天)" width="110" sortable/>
        <el-table-column prop="frequency" label="F购买次数" width="100" sortable/>
        <el-table-column prop="monetary" label="M购买商品数" width="110" sortable/>
        <el-table-column label="R/F/M得分" width="120">
          <template #default="{row}">{{ row.r_score }}/{{ row.f_score }}/{{ row.m_score }}</template>
        </el-table-column>
        <el-table-column prop="segment" label="聚类分群"/>
        <el-table-column prop="octant" label="八分法标签"/>
      </el-table>
      <el-pagination class="pager" background layout="total, prev, pager, next"
        :total="total" :page-size="size" v-model:current-page="page" @current-change="loadDetail"/>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../api/http'
import EChart from '../components/EChart.vue'

const loading = ref(false)
const summary = ref([])
const scatter = ref([])
const octant = ref([])
const rows = ref([])
const total = ref(0), page = ref(1), size = ref(20)
const clusterFilter = ref(null)
const rThreshold = ref(1)

const colorOf = c => ['#e15759', '#f28e2b', '#36a269'][c] || '#2e6be6'
const segName = c => (summary.value.find(s => s.cluster === c) || {}).segment || ('分群' + c)

async function load() {
  loading.value = true
  try {
    const [s, sc, o] = await Promise.all([
      http.get('/rfm/cluster-summary'), http.get('/rfm/scatter'), http.get('/rfm/octant')
    ])
    summary.value = s; scatter.value = sc; octant.value = o
    loadDetail()
  } finally { loading.value = false }
}
async function loadDetail() {
  const q = { page: page.value, size: size.value }
  if (clusterFilter.value !== null && clusterFilter.value !== '') q.cluster = clusterFilter.value
  const res = await http.get('/rfm/detail', { params: q })
  rows.value = res.rows; total.value = res.total
}
// 阈值滑块前端演示：按 R 得分过滤当前页
const filteredRows = computed(() => rows.value.filter(r => r.r_score >= rThreshold.value))

const optScatter = computed(() => {
  const groups = {}
  scatter.value.forEach(r => {
    const k = r.cluster
    ;(groups[k] = groups[k] || []).push([r.recency, r.frequency])
  })
  return {
    tooltip: { formatter: p => `${segName(p.seriesIndex)}<br/>R=${p.value[0]}天, F=${p.value[1]}` },
    legend: { top: 0, data: Object.keys(groups).map(k => segName(Number(k))) },
    grid: { left: 50, right: 20, top: 36, bottom: 40 },
    xAxis: { name: 'Recency 最近购买间隔(天)', type: 'value' },
    yAxis: { name: 'Frequency', type: 'value' },
    series: Object.keys(groups).map(k => ({
      name: segName(Number(k)), type: 'scatter', symbolSize: 5,
      itemStyle: { color: colorOf(Number(k)), opacity: 0.55 },
      data: groups[k]
    }))
  }
})

const optOctant = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 80 },
  xAxis: { type: 'category', data: octant.value.map(d => d.octant), axisLabel: { rotate: 30, fontSize: 10, interval: 0 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: octant.value.map(d => d.users), itemStyle: { color: '#2e6be6' }, label: { show: true, position: 'top', fontSize: 10 } }]
}))

onMounted(load)
</script>

<style scoped>
.bar { display:flex; align-items:center; gap:12px; margin-bottom:14px; }
.seg-card { margin-bottom: 4px; }
.seg-head { display:flex; justify-content:space-between; align-items:center; border-top:4px solid #eee; padding-top:8px; }
.seg-name { font-weight:700; font-size:15px; }
.seg-users { margin-top:8px; }
.seg-avg { color:#606266; font-size:12px; margin-top:4px; }
.seg-strategy { color:#909399; font-size:12px; margin-top:6px; line-height:1.5; }
.tbl-head { display:flex; justify-content:space-between; align-items:center; }
.pager { margin-top:12px; justify-content:flex-end; }
</style>
