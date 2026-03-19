<template>
  <q-page padding>
    <div v-if="metricsStore.loading" class="flex flex-center" style="min-height: 300px">
      <q-spinner-dots color="teal" size="40px" />
    </div>

    <div v-else-if="metricsStore.metrics.length === 0" class="flex flex-center" style="min-height: 300px">
      <div class="text-center text-grey-6">
        <q-icon name="show_chart" size="64px" class="q-mb-md" />
        <div class="text-h6">No metrics yet</div>
        <div class="text-body2 q-mb-md">Tap + to create your first metric</div>
      </div>
    </div>

    <div v-else class="row q-col-gutter-md">
      <div
        v-for="metric in metricsStore.metrics"
        :key="metric.id"
        class="col-12 col-sm-6"
      >
        <MetricCard :metric="metric" />
      </div>
    </div>

    <q-page-sticky position="bottom-right" :offset="[18, 18]">
      <q-btn fab icon="add" color="teal" @click="$router.push('/metrics/new')" />
    </q-page-sticky>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useMetricsStore } from '@/stores/metrics';
import MetricCard from '@/components/MetricCard.vue';

const metricsStore = useMetricsStore();

onMounted(() => {
  metricsStore.fetchMetrics();
});
</script>
