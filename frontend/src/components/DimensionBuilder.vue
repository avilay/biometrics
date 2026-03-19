<template>
  <div>
    <div class="text-subtitle2 text-grey-4 q-mb-sm">Dimensions</div>

    <q-card
      v-for="(dim, index) in modelValue"
      :key="index"
      class="bg-grey-9 q-mb-sm"
      flat
      bordered
    >
      <q-card-section>
        <div class="row q-col-gutter-sm items-start">
          <div class="col">
            <q-input
              :model-value="dim.name"
              @update:model-value="updateDimName(index, $event as string)"
              label="Dimension Name"
              dark
              filled
              dense
            />
          </div>
          <div class="col-auto">
            <q-btn
              flat
              round
              dense
              icon="delete"
              color="negative"
              @click="removeDimension(index)"
            />
          </div>
        </div>
        <q-select
          :model-value="dim.categories"
          @update:model-value="updateDimCategories(index, $event as string[])"
          label="Categories"
          dark
          filled
          dense
          multiple
          use-chips
          use-input
          new-value-mode="add-unique"
          hide-dropdown-icon
          hint="Type and press Enter"
          class="q-mt-sm"
        />
      </q-card-section>
    </q-card>

    <q-btn
      outline
      color="teal"
      label="Add Dimension"
      icon="add"
      no-caps
      @click="addDimension"
      class="q-mt-sm"
    />
  </div>
</template>

<script setup lang="ts">
import type { Dimension } from '@/stores/metrics';

const props = defineProps<{
  modelValue: Dimension[];
}>();

const emit = defineEmits<{
  'update:modelValue': [value: Dimension[]];
}>();

function addDimension() {
  const updated = [...props.modelValue, { name: '', categories: [] }];
  emit('update:modelValue', updated);
}

function removeDimension(index: number) {
  const updated = props.modelValue.filter((_, i) => i !== index);
  emit('update:modelValue', updated);
}

function updateDimName(index: number, name: string) {
  const updated = [...props.modelValue];
  updated[index] = { ...updated[index], name };
  emit('update:modelValue', updated);
}

function updateDimCategories(index: number, categories: string[]) {
  const updated = [...props.modelValue];
  updated[index] = { ...updated[index], categories };
  emit('update:modelValue', updated);
}
</script>
