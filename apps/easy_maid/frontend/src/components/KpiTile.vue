<template>
  <article class="card">
    <p class="muted">{{ label }}</p>
    <h3>{{ value }}</h3>
    <p class="muted">{{ hint }}</p>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  hint: { type: String, default: '' },
});
</script>
