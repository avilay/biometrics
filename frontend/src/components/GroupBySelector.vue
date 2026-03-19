<template>
  <q-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :options="options"
    label="Group By"
    dark
    filled
    dense
    emit-value
    map-options
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Dimension } from '@/stores/metrics';

const props = defineProps<{
  dimensions: Dimension[];
  valueType: string;
  modelValue: string;
}>();

defineEmits<{
  'update:modelValue': [value: string];
}>();

const options = computed(() => {
  const opts = [{ label: 'None', value: 'none' }];

  for (const dim of props.dimensions) {
    opts.push({ label: dim.name, value: dim.name });
  }

  if (props.valueType === 'categorical') {
    opts.push({ label: 'Value', value: 'value' });
  }

  return opts;
});
</script>
