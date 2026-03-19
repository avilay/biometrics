<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <q-page class="flex flex-center" style="background-color: #121212">
        <div class="text-center">
          <div class="text-h3 text-weight-bold text-white q-mb-sm">
            Metrics Tracker
          </div>
          <div class="text-subtitle1 text-grey-6 q-mb-xl">
            Track and visualize your biometrics
          </div>
          <div class="column q-gutter-sm">
            <q-btn
              color="teal"
              size="lg"
              label="Sign in with Google"
              icon="login"
              no-caps
              :loading="authStore.loading"
              @click="handleSignIn"
            />
            <q-btn
              outline
              color="grey-5"
              size="lg"
              label="Try Demo"
              icon="visibility"
              no-caps
              :loading="authStore.loading"
              @click="handleDemoSignIn"
            />
          </div>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { Notify } from 'quasar';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();

async function handleSignIn() {
  try {
    await authStore.signInWithGoogle();
    // Page redirects to Google — router guard handles return navigation
  } catch (error) {
    console.error('Sign in failed:', error);
  }
}

async function handleDemoSignIn() {
  try {
    await authStore.signInAsDemo();
    router.push('/dashboard');
  } catch (error: any) {
    console.error('Demo sign in failed:', error);
    Notify.create({
      message: error?.message || 'Demo sign in failed',
      color: 'negative',
      position: 'top',
    });
  }
}
</script>
