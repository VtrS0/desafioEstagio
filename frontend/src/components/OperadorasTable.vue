<template>
  <div>
    <input v-model="q" placeholder="Buscar por CNPJ ou razão social" @keyup.enter="load(1)" />
    <button @click="load(1)">Buscar</button>
    <DespesasChart />
    <table>
      <thead>
        <tr><th>CNPJ</th><th>Razão Social</th><th>UF</th></tr>
      </thead>
      <tbody>
        <tr v-for="op in operadoras" :key="op.cnpj">
          <td>{{op.cnpj}}</td><td>{{op.razao_social}}</td><td>{{op.uf}}</td>
        </tr>
      </tbody>
    </table>
    <div>
      <button @click="prev" :disabled="page<=1">Prev</button>
      <span>Page {{page}}</span>
      <button @click="next">Next</button>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import DespesasChart from './DespesasChart.vue'

export default {
  setup() {
    const operadoras = ref([])
    const page = ref(1)
    const limit = ref(20)
    const q = ref('')

    async function load(p = 1) {
      page.value = p
      const url = new URL('/api/operadoras', window.location.origin)
      url.searchParams.set('page', page.value)
      url.searchParams.set('limit', limit.value)
      if (q.value) url.searchParams.set('q', q.value)
      const res = await fetch(url.toString())
      const json = await res.json()
      operadoras.value = json.data
    }
    function prev(){ if(page.value>1) load(page.value-1) }
    function next(){ load(page.value+1) }

    load(1)
    return { operadoras, page, q, load, prev, next }
  }
}
</script>

<style scoped>
table { width: 100%; border-collapse: collapse }
td, th { border: 1px solid #ddd; padding: 6px }
</style>
