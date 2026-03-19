import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  signInWithRedirect,
  getRedirectResult,
  GoogleAuthProvider,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth } from '@/boot/firebase';

interface UserInfo {
  id: string;
  email: string;
  displayName: string;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null);
  const token = ref<string | null>(null);
  const loading = ref(true);
  const isDemo = ref(false);

  const isAuthenticated = computed(() => !!user.value && !!token.value);

  // Process any pending redirect result before trusting onAuthStateChanged
  console.log('[auth] store init, calling getRedirectResult...');
  const redirectResultHandled = getRedirectResult(auth).then(async (result) => {
    console.log('[auth] getRedirectResult resolved:', result ? `user=${result.user?.email}` : 'null');
    if (result?.user) {
      await setFirebaseUser(result.user);
    }
  }).catch((err) => {
    console.error('[auth] getRedirectResult error:', err);
  });

  async function setFirebaseUser(firebaseUser: import('firebase/auth').User) {
    const idToken = await firebaseUser.getIdToken();

    const BASE_URL = import.meta.env.VITE_API_URL || '';
    await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`,
      },
      body: JSON.stringify({ id_token: idToken }),
    });

    user.value = {
      id: firebaseUser.uid,
      email: firebaseUser.email || '',
      displayName: firebaseUser.displayName || '',
    };
    token.value = idToken;
    isDemo.value = false;
  }

  onAuthStateChanged(auth, async (firebaseUser) => {
    console.log('[auth] onAuthStateChanged fired:', firebaseUser ? `user=${firebaseUser.email}` : 'null');
    if (isDemo.value) return; // Don't override demo session
    // Wait for any pending redirect to be processed first
    console.log('[auth] waiting for redirectResultHandled...');
    await redirectResultHandled;
    console.log('[auth] redirectResultHandled done');
    if (firebaseUser) {
      await setFirebaseUser(firebaseUser);
      console.log('[auth] user set, loading=false');
    } else {
      user.value = null;
      token.value = null;
      console.log('[auth] no user, loading=false');
    }
    loading.value = false;
  });

  async function signInWithGoogle() {
    loading.value = true;
    const provider = new GoogleAuthProvider();
    await signInWithRedirect(auth, provider);
    // Page redirects to Google — onAuthStateChanged handles the return
  }

  async function signInAsDemo() {
    loading.value = true;
    try {
      const BASE_URL = import.meta.env.VITE_API_URL || '';
      const resp = await fetch(`${BASE_URL}/api/auth/demo-login`, {
        method: 'POST',
      });
      if (!resp.ok) {
        throw new Error('Demo login failed');
      }
      const data = await resp.json();

      user.value = {
        id: String(data.id),
        email: data.email || '',
        displayName: data.display_name || 'Demo User',
      };
      token.value = 'demo';
      isDemo.value = true;
    } finally {
      loading.value = false;
    }
  }

  async function signOut() {
    if (!isDemo.value) {
      await firebaseSignOut(auth);
    }
    user.value = null;
    token.value = null;
    isDemo.value = false;
  }

  async function refreshToken() {
    if (isDemo.value) return; // Demo token doesn't expire
    const currentUser = auth.currentUser;
    if (currentUser) {
      token.value = await currentUser.getIdToken(true);
    }
  }

  return {
    user,
    token,
    loading,
    isDemo,
    isAuthenticated,
    signInWithGoogle,
    signInAsDemo,
    signOut,
    refreshToken,
  };
});
