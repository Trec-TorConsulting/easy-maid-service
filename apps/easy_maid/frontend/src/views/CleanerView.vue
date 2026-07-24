<template>
  <section class="grid">
    <article class="card" style="grid-column: span 2;">
      <h2>Today\'s Route</h2>
      <p class="muted">Live statuses sync with Service Visit state machine.</p>
      <p class="muted" v-if="loading">Loading assigned jobs...</p>
      <p class="muted" v-if="error">{{ error }}</p>
      <ol>
        <li v-for="job in jobs" :key="job.name">
          {{ formatTime(job.scheduled_start) }} - {{ job.customer }} - {{ job.status }}
          <div class="row" style="margin-top: 0.4rem;">
            <button class="primary" type="button" @click="setStatus(job.name, 'In Progress')">Start</button>
            <button class="secondary" type="button" @click="setStatus(job.name, 'Completed')">Complete</button>
          </div>
        </li>
      </ol>
    </article>
    <KpiTile label="Visits Today" :value="String(jobs.length)" hint="Assigned jobs" />
    <KpiTile label="Completed" :value="String(completedCount)" hint="Updated in real time" />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import KpiTile from '../components/KpiTile.vue';

const loading = ref(false);
const error = ref('');
const jobs = ref([]);
const completedCount = computed(() => jobs.value.filter((job) => job.status === 'Completed').length);

function formatTime(value) {
  if (!value) {
    return '--:--';
  }
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function loadJobs() {
  loading.value = true;
  error.value = '';
  try {
    const response = await fetch('/api/method/easy_maid.easy_maid.api.cleaner_today_jobs', {
      credentials: 'include',
    });
    const payload = await response.json();
    jobs.value = payload.message?.jobs || [];
  } catch (_err) {
    error.value = 'Unable to load assigned jobs.';
  } finally {
    loading.value = false;
  }
}

async function setStatus(visitName, status) {
  try {
    await fetch('/api/method/easy_maid.easy_maid.api.mark_visit_status', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visit_name: visitName, status }),
    });
    await loadJobs();
  } catch (_err) {
    error.value = 'Unable to update status.';
  }
}

onMounted(loadJobs);
</script>
