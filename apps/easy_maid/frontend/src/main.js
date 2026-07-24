import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import './styles.css';

const OwnerView = () => import('./views/OwnerView.vue');
const ClientView = () => import('./views/ClientView.vue');
const CleanerView = () => import('./views/CleanerView.vue');
const LoginView = () => import('./views/LoginView.vue');

const routes = [
  { path: '/', component: LoginView },
  { path: '/owner', component: OwnerView },
  { path: '/client', component: ClientView },
  { path: '/cleaner', component: CleanerView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

async function getSessionRole() {
  const devRole = window.localStorage.getItem('easymaid-role');
  if (devRole) {
    return devRole;
  }

  const response = await fetch('/api/method/easy_maid.easy_maid.api.current_portal_role', {
    credentials: 'include',
  });
  const payload = await response.json();
  const role = payload?.message?.role;
  if (!role) {
    return null;
  }
  return role;
}

router.beforeEach(async (to) => {
  if (to.path === '/') {
    return true;
  }

  const role = await getSessionRole();
  if (!role) {
    return '/';
  }

  const map = {
    'Easy Maid Owner': '/owner',
    'Easy Maid Client': '/client',
    'Easy Maid Cleaner': '/cleaner',
    Owner: '/owner',
    Client: '/client',
    Cleaner: '/cleaner',
  };

  if (map[role] && map[role] !== to.path) {
    return map[role];
  }

  return true;
});

createApp(App).use(router).mount('#app');
