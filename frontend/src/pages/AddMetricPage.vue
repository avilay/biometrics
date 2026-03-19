<template>
  <q-page padding>
    <div class="text-h5 text-white q-mb-lg">Create Metric</div>

    <q-form @submit.prevent="handleSubmit" class="q-gutter-md">
      <q-input
        v-model="form.name"
        label="Metric Name"
        dark
        filled
        :rules="[val => !!val || 'Name is required']"
      />

      <q-select
        v-model="form.value_type"
        :options="valueTypeOptions"
        label="Value Type"
        dark
        filled
        emit-value
        map-options
      />

      <q-input
        v-if="form.value_type === 'numeric'"
        v-model="form.unit"
        label="Unit"
        dark
        filled
        hint="e.g., mg/dL, lbs, bpm"
      />

      <div v-if="form.value_type === 'categorical'">
        <div class="text-subtitle2 text-grey-4 q-mb-sm">Categories</div>
        <q-select
          v-model="form.categories"
          label="Add categories"
          dark
          filled
          multiple
          use-chips
          use-input
          new-value-mode="add-unique"
          hide-dropdown-icon
          hint="Type a category and press Enter"
        />
      </div>

      <DimensionBuilder v-model="form.dimensions" />

      <q-btn
        type="submit"
        color="teal"
        label="Create Metric"
        no-caps
        size="lg"
        class="full-width q-mt-lg"
        :loading="metricsStore.loading"
      />
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useMetricsStore, type CreateMetricPayload, type Dimension } from '@/stores/metrics';
import DimensionBuilder from '@/components/DimensionBuilder.vue';

const metricsStore = useMetricsStore();
const router = useRouter();

const valueTypeOptions = [
  { label: 'None', value: 'none' },
  { label: 'Numeric', value: 'numeric' },
  { label: 'Categorical', value: 'categorical' },
];

const form = reactive<{
  name: string;
  value_type: 'none' | 'numeric' | 'categorical';
  unit: string;
  categories: string[];
  dimensions: Dimension[];
}>({
  name: '',
  value_type: 'none',
  unit: '',
  categories: [],
  dimensions: [],
});

async function handleSubmit() {
  const payload: CreateMetricPayload = {
    name: form.name,
    value_type: form.value_type,
  };

  if (form.value_type === 'numeric' && form.unit) {
    payload.unit = form.unit;
  }

  if (form.value_type === 'categorical' && form.categories.length > 0) {
    payload.categories = form.categories;
  }

  if (form.dimensions.length > 0) {
    payload.dimensions = form.dimensions;
  }

  try {
    await metricsStore.createMetric(payload);
    router.push('/dashboard');
  } catch (error) {
    console.error('Failed to create metric:', error);
  }
}
</script>
