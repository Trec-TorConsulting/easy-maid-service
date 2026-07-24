<template>
  <section class="grid">
    <article class="card" style="grid-column: span 2;">
      <h2>Your Upcoming Visits</h2>
      <p class="muted">Cancel/reschedule rules enforce minimum 24-hour notice unless admin override.</p>
      <p class="muted" v-if="loading">Loading your account snapshot...</p>
      <p class="muted" v-if="error">{{ error }}</p>
      <ul>
        <li v-for="visit in visits" :key="visit.name">
          {{ formatDate(visit.scheduled_start) }} - {{ visit.status }}
          <div class="row" style="margin-top: 0.4rem;">
            <button class="primary" type="button" @click="rescheduleVisit(visit.name)">Reschedule +2 Days</button>
            <button type="button" @click="cancelVisit(visit.name)">Cancel</button>
          </div>
        </li>
      </ul>
      <div class="row">
        <input v-model="serviceAddress" class="select" placeholder="Service address name" />
        <select v-model="bookingType" class="select">
          <option value="One-time">One-time</option>
          <option value="Recurring">Recurring</option>
        </select>
        <select v-if="bookingType === 'Recurring'" v-model="frequency" class="select">
          <option value="Weekly">Weekly</option>
          <option value="Biweekly">Biweekly</option>
          <option value="Monthly">Monthly</option>
        </select>
        <button class="primary" type="button" @click="createBooking">Create Booking</button>
      </div>

      <h3 style="margin-top: 1rem;">Invoices</h3>
      <ul>
        <li v-for="inv in invoices" :key="inv.name">
          {{ inv.name }} - {{ inv.status }} - {{ currency(inv.outstanding_amount) }} due
          <div class="row" style="margin-top: 0.4rem;">
            <button v-if="Number(inv.outstanding_amount || 0) > 0" class="secondary" type="button" @click="payInvoice(inv.name)">Pay / Retry</button>
            <button type="button" @click="refreshInvoice(inv.name)">Refresh Status</button>
            <button v-if="Number(inv.outstanding_amount || 0) <= 0" type="button" @click="downloadReceipt(inv.name)">Receipt PDF</button>
          </div>
        </li>
      </ul>
    </article>
    <KpiTile label="Open Invoices" :value="String(openInvoices)" hint="Invoices with balance" />
    <KpiTile label="Outstanding" :value="outstandingText" hint="Current unpaid amount" />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import KpiTile from '../components/KpiTile.vue';

const loading = ref(false);
const error = ref('');
const visits = ref([]);
const invoices = ref([]);
const serviceAddress = ref('');
const bookingType = ref('One-time');
const frequency = ref('Weekly');

const openInvoices = computed(() => invoices.value.filter((inv) => Number(inv.outstanding_amount || 0) > 0).length);
const outstandingText = computed(() => {
  const total = invoices.value.reduce((sum, inv) => sum + Number(inv.outstanding_amount || 0), 0);
  return currency(total);
});

function currency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0));
}

function formatDate(value) {
  if (!value) {
    return 'Unscheduled';
  }
  return new Date(value).toLocaleString();
}

async function loadSnapshot() {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch('/api/method/easy_maid.easy_maid.api.client_portal_snapshot', {
      credentials: 'include',
    });
    const payload = await response.json();
    visits.value = payload.message?.visits || [];
    invoices.value = payload.message?.invoices || [];
  } catch (_err) {
    error.value = 'Unable to load portal data.';
  } finally {
    loading.value = false;
  }
}

async function createBooking() {
  if (!serviceAddress.value) {
    error.value = 'Enter your service address name first.';
    return;
  }
  try {
    const isRecurring = bookingType.value === 'Recurring';
    await fetch('/api/method/easy_maid.easy_maid.api.client_create_booking', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_address: serviceAddress.value,
        booking_type: bookingType.value,
        scheduled_date: isRecurring ? null : new Date().toISOString().slice(0, 10),
        start_date: isRecurring ? new Date().toISOString().slice(0, 10) : null,
        frequency: isRecurring ? frequency.value : null,
        interval: isRecurring ? 1 : 1,
        services: [{ item_code: 'EMS-STD-CLEAN', item_name: 'Standard Clean', qty: 1, rate: 150 }],
      }),
    });
    await loadSnapshot();
    error.value = '';
  } catch (_err) {
    error.value = 'Unable to create booking.';
  }
}

async function cancelVisit(visitName) {
  try {
    await fetch('/api/method/easy_maid.easy_maid.api.cancel_service_visit', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visit_name: visitName, reason: 'Client requested cancel from portal' }),
    });
    await loadSnapshot();
  } catch (_err) {
    error.value = 'Unable to cancel visit. Check 24-hour policy window.';
  }
}

async function rescheduleVisit(visitName) {
  try {
    const visit = visits.value.find((row) => row.name === visitName);
    if (!visit?.scheduled_start || !visit?.scheduled_end) {
      throw new Error('Missing schedule');
    }
    const start = new Date(visit.scheduled_start);
    const end = new Date(visit.scheduled_end);
    start.setDate(start.getDate() + 2);
    end.setDate(end.getDate() + 2);

    await fetch('/api/method/easy_maid.easy_maid.api.reschedule_service_visit', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        visit_name: visitName,
        scheduled_start: start.toISOString(),
        scheduled_end: end.toISOString(),
      }),
    });
    await loadSnapshot();
  } catch (_err) {
    error.value = 'Unable to reschedule visit.';
  }
}

function openInvoicePortal() {
  window.location.href = '/app/sales-invoice';
}

async function payInvoice(invoiceName) {
  try {
    const response = await fetch('/api/method/easy_maid.easy_maid.api.create_invoice_payment_request', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice_name: invoiceName }),
    });
    const payload = await response.json();
    const paymentUrl = payload.message?.payment_url;
    if (paymentUrl) {
      window.location.href = paymentUrl;
      return;
    }
    await loadSnapshot();
  } catch (_err) {
    error.value = 'Payment request failed. Please retry.';
  }
}

async function refreshInvoice(invoiceName) {
  try {
    await fetch('/api/method/easy_maid.easy_maid.api.invoice_payment_status', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice_name: invoiceName }),
    });
    await loadSnapshot();
  } catch (_err) {
    error.value = 'Unable to refresh invoice status.';
  }
}

async function downloadReceipt(invoiceName) {
  try {
    const response = await fetch('/api/method/easy_maid.easy_maid.api.client_invoice_receipt_url', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice_name: invoiceName }),
    });
    const payload = await response.json();
    const url = payload.message?.receipt_url;
    if (url) {
      window.open(url, '_blank');
    }
  } catch (_err) {
    error.value = 'Unable to download receipt.';
  }
}

onMounted(loadSnapshot);
</script>
