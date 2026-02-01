<template>
  <canvas ref="canvas"></canvas>
</template>

<script>
import { onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'

export default {
  setup() {
    const canvas = ref(null)
    onMounted(async () => {
      const res = await fetch('/api/estatisticas/uf')
      const json = await res.json()
      const labels = json.totals_by_uf.map(r => r.uf)
      const data = json.totals_by_uf.map(r => Number(r.total_despesas))
      new Chart(canvas.value.getContext('2d'), {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Despesas por UF', data }] }
      })
    })
    return { canvas }
  }
}
</script>
