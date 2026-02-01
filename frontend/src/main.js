import { createApp } from 'vue'
import OperadorasTable from './components/OperadorasTable.vue'

const app = createApp({})
app.component('OperadorasTable', OperadorasTable)
app.mount('#app')
