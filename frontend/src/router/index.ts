import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import MainLayout from '@/layouts/MainLayout.vue';
import LoginPage from '@/pages/LoginPage.vue';
import DashboardPage from '@/pages/DashboardPage.vue';
import AddMetricPage from '@/pages/AddMetricPage.vue';
import MetricDetailPage from '@/pages/MetricDetailPage.vue';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'metrics/new',
        name: 'add-metric',
        component: AddMetricPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'metrics/:id',
        name: 'metric-detail',
        component: MetricDetailPage,
        meta: { requiresAuth: true },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();

  console.log(`[router] beforeEach to=${String(to.name)} loading=${authStore.loading} isAuth=${authStore.isAuthenticated}`);

  // If auth state is still loading, wait for it to resolve before deciding
  if (authStore.loading) {
    console.log('[router] auth loading, subscribing...');
    const unwatch = authStore.$subscribe((_mutation, state) => {
      if (!state.loading) {
        unwatch();
        console.log(`[router] auth loaded: user=${!!state.user} token=${!!state.token}`);
        if (to.name === 'login' && state.user && state.token) {
          next({ name: 'dashboard' });
        } else if (to.meta.requiresAuth && !(state.user && state.token)) {
          next({ name: 'login' });
        } else {
          next();
        }
      }
    });
    return;
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' });
    return;
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' });
    return;
  }

  next();
});

export default router;
