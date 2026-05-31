<template>
  <div class="chart-container">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'

// 注册必须的 ECharts 组件
use([TooltipComponent, LegendComponent, RadarChart, CanvasRenderer])

// 接收父组件传来的维度得分
const props = defineProps<{
  scores: {
    security: number
    performance: number
    style: number
    robustness: number
  }
}>()

const chartOption = ref({})

// 监听数据变化，动态渲染酷炫的雷达图
watch(() => props.scores, (newScores) => {
  chartOption.value = {
    tooltip: { trigger: 'item' },
    radar: {
      radius: '45%',
      indicator: [
        { name: '安全性 (Security)', max: 100 },
        { name: '性能 (Performance)', max: 100 },
        { name: '规范度 (Style)', max: 100 },
        { name: '健壮性 (Robustness)', max: 100 }
      ],
      shape: 'circle',
      splitNumber: 5,
      axisName: { color: '#606266', fontWeight: 'bold' },
      splitLine: {
        lineStyle: { color: ['#e4e7ed', '#ebeef5', '#f2f6fc'].reverse() }
      },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#e4e7ed' } }
    },
    series: [
      {
        name: 'AI 评分',
        type: 'radar',
        data: [
          {
            value: [
              newScores.security || 0,
              newScores.performance || 0,
              newScores.style || 0,
              newScores.robustness || 0
            ],
            name: '当前 PR 质量评分',
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.4)' // 极客蓝半透明填充
            },
            lineStyle: { width: 2, color: '#409EFF' },
            itemStyle: { color: '#409EFF' }
          }
        ]
      }
    ]
  }
}, { immediate: true, deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 350px;
}
.chart {
  width: 100%;
  height: 100%;
}
</style>