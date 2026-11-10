<template>
  <div v-loading="loading">
    <div class="page-title">行为模式分析</div>
    <el-row :gutter="14">
      <el-col :span="15">
        <el-card header="用户活跃时段热力图（星期 × 小时）" class="chart-card">
          <EChart :option="optHeat" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="9">
        <el-card header="各星期平均每日行为量" class="chart-card">
          <EChart :option="optWeekday" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :span="9">
        <el-card header="会话级行为漏斗" class="chart-card">
          <EChart :option="optFunnel" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="不同点击流路径转化率" class="chart-card">
          <EChart :option="optPath" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="7">
        <el-card header="行为流转桑基图" class="chart-card">
          <EChart :option="optSankey" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="14">
      <el-col :span="12">
        <el-card header="浏览量 Top10 商品（标注购买次数）" class="chart-card">
          <EChart :option="optTopPv" class="chart-box"/>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card header="购买量 Top10 商品（标注浏览次数）" class="chart-card">
          <EChart :option="optTopBuy" class="chart-box"/>
        </el-card>
      </el-col>
    </el-row>

    <el-card header="商品类目关联规则（Apriori，按提升度Top20）" class="chart-card">
      <el-table :data="apriori" size="small" stripe height="320">
        <el-table-column type="index" label="#" width="50"/>
        <el-table-column prop="antecedents" label="前项类目" sortable/>
        <el-table-column prop="consequents" label="后项类目" sortable/>
        <el-table-column prop="support" label="支持度" sortable :formatter="r=>Number(r.support).toFixed(4)"/>
        <el-table-column prop="confidence" label="置信度" sortable :formatter="r=>Number(r.confidence).toFixed(4)"/>
        <el-table-column prop="lift" label="提升度" sortable>
          <template #default="{row}"><el-tag :type="row.lift>1?'success':'info'">{{ Number(row.lift).toFixed(3) }}</el-tag></template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../api/http'
import EChart from '../components/EChart.vue'

const loading = ref(false)
const hw = ref([]), wd = ref([]), funnel = ref([]), path = ref([])
const flow = ref([]), topPv = ref([]), topBuy = ref([]), apriori = ref([])

async function load() {
  loading.value = true
  try {
    const [a, b, c, d, e, f, g, h] = await Promise.all([
      http.get('/dashboard/hour-weekday'), http.get('/dashboard/weekday-avg'),
      http.get('/dashboard/funnel'), http.get('/dashboard/path-conversion'),
      http.get('/dashboard/flow-edges'), http.get('/dashboard/top-pv'),
      http.get('/dashboard/top-buy'), http.get('/dashboard/apriori')
    ])
    hw.value = a; wd.value = b; funnel.value = c; path.value = d
    flow.value = e; topPv.value = f; topBuy.value = g; apriori.value = h
  } finally { loading.value = false }
}

const WN = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']
const optHeat = computed(() => {
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const data = []
  let max = 1
  hw.value.forEach(r => { const v = Number(r.cnt); max = Math.max(max, v); data.push([Number(r.hour), Number(r.weekday) - 1, v]) })
  return {
    tooltip: { formatter: p => `${WN[p.value[1] + 1]} ${p.value[0]}时<br/>行为量：${p.value[2]}` },
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
    xAxis: { type: 'category', data: hours, name: '小时' },
    yAxis: { type: 'category', data: WN.slice(1) },
    visualMap: { min: 0, max, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#fff7ec', '#fdb863', '#b30000'] } },
    series: [{ type: 'heatmap', data, label: { show: false } }]
  }
})

const optWeekday = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 56, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: wd.value.map(d => d.weekday_cn) },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: wd.value.map(d => Math.round(d.avg_cnt)), itemStyle: { color: '#2e6be6' }, label: { show: true, position: 'top', fontSize: 10 } }]
}))

const optFunnel = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c}' },
  series: [{
    type: 'funnel', left: '8%', width: '84%', top: 10, bottom: 10,
    label: { formatter: '{b}\n{c}' },
    data: funnel.value.map(d => ({ name: d.stage, value: d.sessions }))
  }]
}))

const optPath = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 90 },
  xAxis: { type: 'category', data: path.value.map(d => d.path), axisLabel: { rotate: 35, fontSize: 10, interval: 0 } },
  yAxis: { type: 'value', name: '转化率%' },
  series: [{ type: 'bar', data: path.value.map(d => d.conversion_pct), itemStyle: { color: '#36a269' }, label: { show: true, position: 'top', formatter: '{c}%' } }]
}))

const optSankey = computed(() => {
  const names = new Set()
  flow.value.forEach(e => { names.add(e.source); names.add(e.target) })
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'sankey', left: 10, right: 80, top: 10, bottom: 10, nodeWidth: 14,
      data: [...names].map(n => ({ name: n })),
      links: flow.value.map(e => ({ source: e.source, target: e.target, value: e.value })),
      label: { fontSize: 11 }
    }]
  }
})

const barH = (arr, valKey, color) => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 90, right: 40, top: 20, bottom: 20 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: arr.map(d => String(d.item_id)).reverse() },
  series: [{ type: 'bar', data: arr.map(d => d[valKey]).reverse(), itemStyle: { color }, label: { show: true, position: 'right', fontSize: 10 } }]
})
const optTopPv = computed(() => barH(topPv.value, 'pv', '#4e79a7'))
const optTopBuy = computed(() => barH(topBuy.value, 'buy', '#e15759'))

onMounted(load)
</script>
