<template>
  <section class="grid">
    <article class="card" style="grid-column: span 2;">
      <h2>Portal Entry</h2>
      <p class="muted">Sign in with your ERPNext account, then return to this app.</p>
      <div class="row">
        <a href="/login"><button class="primary" type="button">Go To Login</button></a>
      </div>
      <p class="muted">Developer helper for local demos:</p>
      <div class="row">
        <button class="primary" @click="enter('Owner')">Enter as Owner</button>
        <button class="secondary" @click="enter('Client')">Enter as Client</button>
        <button @click="enter('Cleaner')">Enter as Cleaner</button>
        <button @click="clearDemo">Clear Demo Role</button>
      </div>
    </article>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function enter(role) {
  window.localStorage.setItem('easymaid-role', role);
  const map = {
    Owner: '/owner',
    Client: '/client',
    Cleaner: '/cleaner',
  };
  router.push(map[role]);
}

function clearDemo() {
  window.localStorage.removeItem('easymaid-role');
}
</script>
