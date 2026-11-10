<template>
  <div ref="el" class="chart-box" :class="size"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  size: { type: String, default: '' }
})
const el = ref(null)
let chart = null
const resize = () => chart && chart.resize()

onMounted(() => {
  chart = echarts.init(el.value)
  chart.setOption(props.option)
  window.addEventListener('resize', resize)
})
watch(() => props.option, async (val) => {
  await nextTick()
  if (chart) { chart.clear(); chart.setOption(val, true) }
}, { deep: true })
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})
</script>
