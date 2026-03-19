<template>
  <q-page padding>
    <div v-if="metricsStore.loading && !metricsStore.currentMetric" class="flex flex-center" style="min-height: 300px">
      <q-spinner-dots color="teal" size="40px" />
    </div>

    <template v-else-if="metricsStore.currentMetric">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h5 text-white">
          {{ metricsStore.currentMetric.name }}
        </div>
        <q-btn
          flat
          round
          icon="delete"
          color="red-4"
          @click="showDeleteConfirm = true"
        />
      </div>

      <!-- Delete Confirmation Dialog -->
      <q-dialog v-model="showDeleteConfirm">
        <q-card class="bg-grey-10" style="min-width: 320px">
          <q-card-section>
            <div class="text-h6 text-white">Delete metric?</div>
          </q-card-section>
          <q-card-section class="text-grey-4">
            This will permanently delete <strong>{{ metricsStore.currentMetric.name }}</strong> and all its logged data. This action cannot be undone.
          </q-card-section>
          <q-card-actions align="right">
            <q-btn flat label="Cancel" color="grey-4" v-close-popup />
            <q-btn flat label="Delete" color="red" @click="onDeleteMetric" :loading="deleting" />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <!-- Time Range Selector -->
      <TimeRangeSelector v-model="timeRange" class="q-mb-md" />

      <!-- Filters Row -->
      <div class="row q-col-gutter-sm q-mb-md">
        <div class="col-12 col-sm-6">
          <DimensionFilters
            v-if="simpleDimensions.length > 0"
            :dimensions="simpleDimensions"
            v-model="filters"
          />
        </div>
        <div class="col-6 col-sm-3">
          <AggregateSelector
            v-model="aggregate"
            :value-type="metricsStore.currentMetric.value_type"
          />
        </div>
        <div class="col-6 col-sm-3">
          <GroupBySelector
            v-model="groupBy"
            :dimensions="simpleDimensions"
            :value-type="metricsStore.currentMetric.value_type"
          />
        </div>
      </div>

      <!-- Chart -->
      <MetricChart
        :labels="metricsStore.aggregationData.labels"
        :series="metricsStore.aggregationData.series"
        :grouped="groupBy !== 'none'"
        :metric-name="metricsStore.currentMetric.name"
        class="q-mb-md"
      />

      <!-- Table -->
      <MetricTable
        :labels="metricsStore.aggregationData.labels"
        :series="metricsStore.aggregationData.series"
        :grouped="groupBy !== 'none'"
        :aggregate="aggregate"
      />
    </template>

    <!-- FAB for logging -->
    <q-page-sticky position="bottom-right" :offset="[18, 18]">
      <q-btn fab icon="add" color="teal" @click="showLogDialog = true" />
    </q-page-sticky>

    <!-- Log Entry Dialog -->
    <LogEntryDialog
      v-if="metricsStore.currentMetric"
      v-model="showLogDialog"
      :metric="metricsStore.currentMetric"
      @saved="onLogSaved"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Notify } from 'quasar';
import { useMetricsStore, simplifyDimensions } from '@/stores/metrics';
import TimeRangeSelector from '@/components/TimeRangeSelector.vue';
import DimensionFilters from '@/components/DimensionFilters.vue';
import AggregateSelector from '@/components/AggregateSelector.vue';
import GroupBySelector from '@/components/GroupBySelector.vue';
import MetricChart from '@/components/MetricChart.vue';
import MetricTable from '@/components/MetricTable.vue';
import LogEntryDialog from '@/components/LogEntryDialog.vue';

const route = useRoute();
const router = useRouter();
const metricsStore = useMetricsStore();

const timeRange = ref('W');
const filters = ref<Record<string, string>>({});
const aggregate = ref('count');
const groupBy = ref('none');
const showLogDialog = ref(false);
const showDeleteConfirm = ref(false);
const deleting = ref(false);

const metricId = route.params.id as string;

const simpleDimensions = computed(() =>
  metricsStore.currentMetric ? simplifyDimensions(metricsStore.currentMetric.dimensions) : []
);

function buildParams(): Record<string, string> {
  const params: Record<string, string> = {
    range: timeRange.value,
    aggregate: aggregate.value,
  };
  if (groupBy.value !== 'none') {
    params.group_by = groupBy.value;
  }
  for (const [key, value] of Object.entries(filters.value)) {
    if (value && value !== 'all') {
      params[`filter_${key}`] = value;
    }
  }
  return params;
}

function loadAggregation() {
  metricsStore.fetchAggregation(metricId, buildParams());
}

onMounted(async () => {
  await metricsStore.fetchMetric(metricId);

  // Set default aggregate based on value_type
  if (metricsStore.currentMetric) {
    const vt = metricsStore.currentMetric.value_type;
    aggregate.value = vt === 'numeric' ? 'sum' : 'count';
  }

  loadAggregation();
});

watch([timeRange, filters, aggregate, groupBy], () => {
  loadAggregation();
}, { deep: true });

function onLogSaved() {
  showLogDialog.value = false;
  loadAggregation();
}

async function onDeleteMetric() {
  deleting.value = true;
  try {
    await metricsStore.deleteMetric(metricId);
    Notify.create({
      message: 'Metric deleted',
      color: 'positive',
      icon: 'check',
      position: 'top',
    });
    router.replace('/');
  } catch {
    Notify.create({
      message: 'Failed to delete metric',
      color: 'negative',
      icon: 'error',
      position: 'top',
    });
  } finally {
    deleting.value = false;
    showDeleteConfirm.value = false;
  }
}
</script>
