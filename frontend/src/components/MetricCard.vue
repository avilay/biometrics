<template>
  <q-card
    class="bg-grey-10 cursor-pointer"
    @click="$router.push(`/metrics/${metric.id}`)"
    flat
    bordered
  >
    <q-card-section>
      <div class="row items-center justify-between q-mb-sm">
        <div class="text-subtitle1 text-grey-4">{{ metric.name }}</div>
        <q-icon name="chevron_right" color="grey-6" />
      </div>
      <div class="text-h4 text-white q-mb-xs">
        {{ formattedValue }}
      </div>
      <div class="text-caption text-grey-6">
        {{ formattedTime }}
      </div>
    </q-card-section>
    <q-card-section class="q-pt-none">
      <SparklineChart
        :data="metric.sparkline_data || []"
        :color="colorFor(metric.name)"
      />
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { MetricListItem } from '@/stores/metrics';
import SparklineChart from '@/components/SparklineChart.vue';
import { colorFor } from '@/utils/colors';

const props = defineProps<{
  metric: MetricListItem;
}>();

const formattedValue = computed(() => {
  if (props.metric.latest_value == null) return '--';
  const val = props.metric.latest_value;
  if (props.metric.unit) {
    return `${val} ${props.metric.unit}`;
  }
  return String(val);
});

const formattedTime = computed(() => {
  if (!props.metric.latest_recorded_at) return 'No data';
  const date = new Date(props.metric.latest_recorded_at);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
});
</script>
