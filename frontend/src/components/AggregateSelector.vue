<template>
  <q-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :options="filteredOptions"
    label="Aggregate"
    dark
    filled
    dense
    emit-value
    map-options
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  modelValue: string;
  valueType: string;
}>();

defineEmits<{
  'update:modelValue': [value: string];
}>();

const filteredOptions = computed(() => {
  switch (props.valueType) {
    case 'numeric':
      return [
        { label: 'Sum', value: 'sum' },
        { label: 'Mean', value: 'mean' },
      ];
    case 'categorical':
    case 'none':
    default:
      return [{ label: 'Count', value: 'count' }];
  }
});
</script>
