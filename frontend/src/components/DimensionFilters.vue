<template>
  <div class="row q-col-gutter-sm">
    <div v-for="dim in dimensions" :key="dim.name" class="col">
      <q-select
        :model-value="modelValue[dim.name] || 'all'"
        @update:model-value="updateFilter(dim.name, $event as string)"
        :options="['all', ...dim.categories]"
        :label="dim.name"
        dark
        filled
        dense
        emit-value
        map-options
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Dimension } from '@/stores/metrics';

const props = defineProps<{
  dimensions: Dimension[];
  modelValue: Record<string, string>;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, string>];
}>();

function updateFilter(dimName: string, value: string) {
  const updated = { ...props.modelValue, [dimName]: value };
  emit('update:modelValue', updated);
}
</script>
