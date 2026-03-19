<template>
  <q-btn-group spread>
    <q-btn
      v-for="option in options"
      :key="option"
      :label="option"
      no-caps
      :color="modelValue === option ? 'teal' : 'grey-9'"
      :text-color="modelValue === option ? 'white' : 'grey-4'"
      @click="$emit('update:modelValue', option)"
    />
  </q-btn-group>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string;
}>();

defineEmits<{
  'update:modelValue': [value: string];
}>();

const options = ['D', 'W', 'M', '6M', 'Y'];
</script>
