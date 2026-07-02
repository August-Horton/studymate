<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ mindmapJson: String })
const chartRef = ref(null)
let chartInstance = null

const renderChart = () => {
  if (!chartRef.value) return

  let data = { name: "课堂笔记", children: [] }
  if (props.mindmapJson) {
    try {
      data = JSON.parse(props.mindmapJson)
    } catch (e) {
      console.warn("思维导图数据解析失败")
    }
  }

  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  chartInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'tree',
      data: [data],
      top: '5%',
      left: '8%',
      bottom: '5%',
      right: '15%',
      symbol: 'roundRect',
      symbolSize: 10,
      orient: 'LR',
      expandAndCollapse: true,
      initialTreeDepth: 2,
      label: {
        position: 'left',
        verticalAlign: 'middle',
        align: 'right',
        fontSize: 11,
        overflow: 'truncate',
        width: 100
      },
      leaves: {
        label: {
          position: 'right',
          verticalAlign: 'middle',
          align: 'left',
          fontSize: 11,
          overflow: 'truncate',
          width: 120
        }
      },
      emphasis: { focus: 'descendant' }
    }]
  })
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  nextTick(renderChart)
  window.addEventListener('resize', handleResize)
})

watch(() => props.mindmapJson, () => nextTick(renderChart))

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 500px;
  overflow-x: auto;
  background: #fefefe;
  border-radius: 8px;
}
</style>
