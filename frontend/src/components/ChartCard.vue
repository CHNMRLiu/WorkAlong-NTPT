<template>
  <div class="app-card chart-card">
    <h3 class="app-card__title">{{ title }}</h3>
    <div ref="el" class="chart-card__body" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, default: '' },
  option: { type: Object, required: true },
  height: { type: Number, default: 320 }
})

const el = ref(null)
let chart = null

function render() {
  if (!chart) return
  chart.setOption(props.option, true)
}

function resize() {
  if (chart) chart.resize()
}

onMounted(async () => {
  await nextTick()
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})

watch(() => props.option, () => render(), { deep: true })
</script>

<style scoped>
.chart-card__body { width: 100%; }
</style>
