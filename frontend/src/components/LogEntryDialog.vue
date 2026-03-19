<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    position="bottom"
  >
    <q-card class="bg-grey-10" style="width: 100%; max-width: 500px">
      <q-card-section>
        <div class="text-h6 text-white">Log Entry</div>
      </q-card-section>

      <q-card-section class="q-gutter-md">
        <!-- Numeric value input -->
        <q-input
          v-if="metric.value_type === 'numeric'"
          v-model.number="form.value"
          type="number"
          label="Value"
          dark
          filled
          :suffix="metric.unit || undefined"
        />

        <!-- Categorical value select -->
        <q-select
          v-if="metric.value_type === 'categorical'"
          v-model="form.value"
          :options="metric.categories"
          label="Value"
          dark
          filled
          emit-value
          map-options
        />

        <!-- Dimension selects -->
        <q-select
          v-for="dim in metric.dimensions"
          :key="dim.name"
          v-model="form.dimensions[dim.name]"
          :options="dim.categories.map((c: any) => typeof c === 'string' ? c : c.name)"
          :label="dim.name"
          dark
          filled
          emit-value
          map-options
        />

        <!-- Date picker -->
        <q-input
          v-model="form.date"
          label="Date"
          dark
          filled
          type="date"
        />

        <!-- Time picker -->
        <q-input
          v-model="form.time"
          label="Time"
          dark
          filled
          type="time"
        />
      </q-card-section>

      <q-card-actions align="right" class="q-px-md q-pb-md">
        <q-btn
          flat
          label="Cancel"
          color="grey-4"
          no-caps
          v-close-popup
        />
        <q-btn
          label="Save"
          color="teal"
          no-caps
          :loading="saving"
          @click="handleSave"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useMetricsStore, type MetricDetail, type CreateLogPayload } from '@/stores/metrics';

const props = defineProps<{
  metric: MetricDetail;
  modelValue: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  saved: [];
}>();

const metricsStore = useMetricsStore();
const saving = ref(false);

const now = new Date();
const form = reactive<{
  value: string | number | null;
  dimensions: Record<string, string>;
  date: string;
  time: string;
}>({
  value: null,
  dimensions: {},
  date: now.toISOString().split('T')[0],
  time: now.toTimeString().slice(0, 5),
});

async function handleSave() {
  saving.value = true;
  try {
    const recordedAt = new Date(`${form.date}T${form.time}:00`).toISOString();

    const payload: CreateLogPayload = {
      recorded_at: recordedAt,
    };

    if (props.metric.value_type === 'numeric' && form.value != null) {
      payload.numeric_value = Number(form.value);
    } else if (props.metric.value_type === 'categorical' && form.value != null) {
      payload.categorical_value = String(form.value);
    }

    if (Object.keys(form.dimensions).length > 0) {
      payload.dimensions = form.dimensions;
    }

    await metricsStore.createLog(props.metric.id, payload);
    emit('saved');
  } catch (error) {
    console.error('Failed to save log:', error);
  } finally {
    saving.value = false;
  }
}
</script>
