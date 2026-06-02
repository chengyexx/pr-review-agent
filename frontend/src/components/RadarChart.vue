<template>
  <div class="chart-container">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

use([TooltipComponent, RadarChart, CanvasRenderer])

const props = defineProps<{
  scores: {
    security: number
    performance: number
    style: number
    robustness: number
  }
}>()

const chartOption = ref({})

watch(() => props.scores, (s) => {
  chartOption.value = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(24, 24, 27, 0.95)',
      borderColor: 'rgba(255,255,255,0.08)',
      textStyle: { color: '#fafafa', fontSize: 12 },
    },
    radar: {
      radius: '58%',
      center: ['50%', '52%'],
      indicator: [
        { name: 'Security', max: 100 },
        { name: 'Performance', max: 100 },
        { name: 'Style', max: 100 },
        { name: 'Robustness', max: 100 },
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#71717a',
        fontSize: 11,
        fontWeight: 600,
      },
      splitLine: {
        lineStyle: { color: 'rgba(255,255,255,0.06)' },
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(99,102,241,0.02)', 'rgba(99,102,241,0.04)'],
        },
      },
      axisLine: {
        lineStyle: { color: 'rgba(255,255,255,0.08)' },
      },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [s.security, s.performance, s.style, s.robustness],
        name: 'Quality Score',
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#818cf8',
        },
        itemStyle: {
          color: '#818cf8',
          borderColor: '#6366f1',
          borderWidth: 2,
        },
        areaStyle: {
          color: {
            type: 'radial',
            x: 0.5, y: 0.5, r: 0.5,
            colorStops: [
              { offset: 0, color: 'rgba(99, 102, 241, 0.35)' },
              { offset: 1, color: 'rgba(34, 211, 238, 0.08)' },
            ],
          },
        },
      }],
    }],
  }
}, { immediate: true, deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 260px;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>
