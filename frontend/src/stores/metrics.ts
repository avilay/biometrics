import { defineStore } from 'pinia';
import { ref } from 'vue';
import { Notify } from 'quasar';
import { useApi } from '@/composables/useApi';
import { useAuthStore } from '@/stores/auth';

export interface DimensionCategory {
  id: number;
  name: string;
}

export interface DimensionDetail {
  id: number;
  name: string;
  categories: DimensionCategory[];
}

// Simplified dimension for components that only need names
export interface Dimension {
  name: string;
  categories: string[];
}

export interface MetricListItem {
  id: number;
  name: string;
  value_type: 'none' | 'numeric' | 'categorical';
  unit: string | null;
  latest_value: string | null;
  latest_recorded_at: string | null;
  sparkline_data: (number | null)[];
}

export interface MetricDetail {
  id: number;
  name: string;
  value_type: 'none' | 'numeric' | 'categorical';
  unit: string | null;
  categories: string[];
  dimensions: DimensionDetail[];
  created_at: string;
}

// Helper to convert DimensionDetail[] to simplified Dimension[]
export function simplifyDimensions(dims: DimensionDetail[]): Dimension[] {
  return dims.map(d => ({ name: d.name, categories: d.categories.map(c => c.name) }));
}

export interface LogEntry {
  id: string;
  value: string | number | null;
  dimensions: Record<string, string>;
  recorded_at: string;
}

export interface AggregationData {
  labels: string[];
  series: { name: string; data: number[]; color?: string }[];
}

export interface CreateMetricPayload {
  name: string;
  value_type: 'none' | 'numeric' | 'categorical';
  unit?: string;
  categories?: string[];
  dimensions?: Dimension[];
}

export interface CreateLogPayload {
  recorded_at: string;
  numeric_value?: number;
  categorical_value?: string;
  dimensions?: Record<string, string>;
}

function notifyDemoBlock() {
  Notify.create({
    message: 'Demo users cannot modify data. Sign in with Google to use the app.',
    color: 'warning',
    icon: 'info',
    position: 'top',
  });
}

export const useMetricsStore = defineStore('metrics', () => {
  const metrics = ref<MetricListItem[]>([]);
  const currentMetric = ref<MetricDetail | null>(null);
  const aggregationData = ref<AggregationData>({ labels: [], series: [] });
  const loading = ref(false);

  const api = useApi();

  async function fetchMetrics() {
    loading.value = true;
    try {
      metrics.value = await api.get<MetricListItem[]>('/api/metrics');
    } finally {
      loading.value = false;
    }
  }

  async function createMetric(data: CreateMetricPayload) {
    const authStore = useAuthStore();
    if (authStore.isDemo) {
      notifyDemoBlock();
      return;
    }
    loading.value = true;
    try {
      await api.post('/api/metrics', data);
    } finally {
      loading.value = false;
    }
  }

  async function fetchMetric(id: string) {
    loading.value = true;
    try {
      currentMetric.value = await api.get<MetricDetail>(`/api/metrics/${id}`);
    } finally {
      loading.value = false;
    }
  }

  async function deleteMetric(id: string) {
    const authStore = useAuthStore();
    if (authStore.isDemo) {
      notifyDemoBlock();
      return;
    }
    loading.value = true;
    try {
      await api.del(`/api/metrics/${id}`);
    } finally {
      loading.value = false;
    }
  }

  async function createLog(metricId: string, data: CreateLogPayload) {
    const authStore = useAuthStore();
    if (authStore.isDemo) {
      notifyDemoBlock();
      return;
    }
    loading.value = true;
    try {
      await api.post(`/api/metrics/${metricId}/logs`, data);
    } finally {
      loading.value = false;
    }
  }

  async function fetchAggregation(
    metricId: string,
    params: Record<string, string>
  ) {
    loading.value = true;
    try {
      aggregationData.value = await api.get<AggregationData>(
        `/api/metrics/${metricId}/logs`,
        params
      );
    } finally {
      loading.value = false;
    }
  }

  async function deleteLog(metricId: string, logId: string) {
    const authStore = useAuthStore();
    if (authStore.isDemo) {
      notifyDemoBlock();
      return;
    }
    await api.del(`/api/metrics/${metricId}/logs/${logId}`);
  }

  return {
    metrics,
    currentMetric,
    aggregationData,
    loading,
    fetchMetrics,
    createMetric,
    fetchMetric,
    deleteMetric,
    createLog,
    fetchAggregation,
    deleteLog,
  };
});
