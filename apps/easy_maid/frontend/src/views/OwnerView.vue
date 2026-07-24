<template>
  <section class="grid">
    <KpiTile label="Upcoming Visits" :value="String(metrics.upcoming_visits)" hint="Scheduled + in progress" />
    <KpiTile label="Unassigned Visits" :value="String(metrics.unassigned_visits)" hint="Needs dispatch assignment" />
    <KpiTile label="Accounts Receivable" :value="formatCurrency(metrics.accounts_receivable)" hint="Open invoice balance" />
    <KpiTile label="Open Invoices" :value="String(finance.open_invoices)" hint="Submitted with outstanding" />
    <KpiTile label="Net Revenue" :value="formatCurrency(finance.net_revenue)" hint="Posted invoices" />
    <KpiTile label="GL Entries" :value="String(finance.gl_entries)" hint="Bookkeeping activity" />

    <article class="card" style="grid-column: span 2;">
      <h3>Dispatch Priorities</h3>
      <p class="muted">Drag-and-drop dispatch UI already exists in Desk page; this route is the unified owner shell.</p>
      <p class="muted" v-if="loading">Loading dashboard metrics...</p>
      <p class="muted" v-if="error">{{ error }}</p>
      <div class="row">
        <a href="/app/crew-desk"><button class="primary" type="button">Open Crew Desk</button></a>
        <a href="/app/dispatch-calendar"><button type="button">Open Calendar</button></a>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue';
import KpiTile from '../components/KpiTile.vue';

const loading = ref(false);
const error = ref('');
const metrics = reactive({
  upcoming_visits: 0,
  unassigned_visits: 0,
  accounts_receivable: 0,
});
const finance = reactive({
  open_invoices: 0,
  net_revenue: 0,
  gl_entries: 0,
});

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);
}

async function loadMetrics() {
  loading.value = true;
  error.value = '';
  try {
    const [metricsResponse, financeResponse] = await Promise.all([
      fetch('/api/method/easy_maid.easy_maid.api.owner_dashboard_metrics', { credentials: 'include' }),
      fetch('/api/method/easy_maid.easy_maid.api.owner_financial_snapshot', { credentials: 'include' }),
    ]);
    const metricsPayload = await metricsResponse.json();
    const financePayload = await financeResponse.json();
    Object.assign(metrics, metricsPayload.message || {});
    Object.assign(finance, financePayload.message || {});
  } catch (_err) {
    error.value = 'Unable to load metrics right now.';
  } finally {
    loading.value = false;
  }
}

onMounted(loadMetrics);
</script>
