<template>
  <q-layout view="hHh lpR fFf">
    <q-header bordered class="bg-dark">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="arrow_back"
          @click="$router.back()"
          v-if="$route.name !== 'dashboard'"
        />
        <q-toolbar-title class="text-weight-bold">
          Metrics Tracker
        </q-toolbar-title>
        <q-btn flat round dense>
          <q-avatar size="32px" color="teal" text-color="white">
            {{ userInitial }}
          </q-avatar>
          <q-menu>
            <q-list style="min-width: 150px">
              <q-item>
                <q-item-section>
                  <q-item-label>{{ authStore.user?.displayName }}</q-item-label>
                  <q-item-label caption>{{ authStore.user?.email }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator />
              <q-item clickable v-close-popup @click="handleSignOut">
                <q-item-section avatar>
                  <q-icon name="logout" />
                </q-item-section>
                <q-item-section>Sign Out</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();

const userInitial = computed(() => {
  const name = authStore.user?.displayName || authStore.user?.email || '?';
  return name.charAt(0).toUpperCase();
});

async function handleSignOut() {
  await authStore.signOut();
  router.push('/');
}
</script>
