import { useAuthStore } from '@/stores/auth';
import router from '@/router';

const BASE_URL = import.meta.env.VITE_API_URL || '';

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string>;
}

export function useApi() {
  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const authStore = useAuthStore();
    const { method = 'GET', body, params } = options;

    let url = `${BASE_URL}${path}`;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (authStore.token) {
      headers['Authorization'] = `Bearer ${authStore.token}`;
    }

    const fetchOptions: RequestInit = {
      method,
      headers,
    };

    if (body && method !== 'GET') {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await fetch(url, fetchOptions);

    if (response.status === 401) {
      authStore.signOut();
      await router.push('/');
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed: ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  function get<T>(path: string, params?: Record<string, string>) {
    return request<T>(path, { method: 'GET', params });
  }

  function post<T>(path: string, body?: unknown) {
    return request<T>(path, { method: 'POST', body });
  }

  function del<T>(path: string) {
    return request<T>(path, { method: 'DELETE' });
  }

  return { request, get, post, del };
}
