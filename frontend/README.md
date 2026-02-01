Frontend (Vue.js) skeleton
---------------------------

This is a minimal Vue 3 skeleton using Chart.js for the distribution chart and simple fetch calls to the FastAPI backend.

Install & run (example with Vite):
1. cd frontend
2. npm install
3. npm run dev

Files provided as starting point: `src/main.js`, `src/components/OperadorasTable.vue`.

Decisions: server-side search (to keep client light) and Pinia/complex state not included for simplicity; use composables if app grows.
