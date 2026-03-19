<template>
  <q-table
    :rows="rows"
    :columns="columns"
    row-key="period"
    dark
    flat
    bordered
    dense
    :rows-per-page-options="[0]"
    hide-bottom
    class="bg-grey-10"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { QTableColumn } from 'quasar';

const props = defineProps<{
  labels: string[];
  series: { name: string; data: number[]; color?: string }[];
  grouped: boolean;
  aggregate: string;
}>();

const columns = computed<QTableColumn[]>(() => {
  const cols: QTableColumn[] = [
    {
      name: 'period',
      label: 'Period',
      field: 'period',
      align: 'left',
      sortable: true,
    },
  ];

  if (props.grouped && props.series.length > 1) {
    for (const s of props.series) {
      cols.push({
        name: s.name,
        label: s.name,
        field: s.name,
        align: 'right',
        sortable: true,
      });
    }
  } else {
    cols.push({
      name: 'value',
      label: props.aggregate.charAt(0).toUpperCase() + props.aggregate.slice(1),
      field: 'value',
      align: 'right',
      sortable: true,
    });
  }

  return cols;
});

const rows = computed(() => {
  return props.labels.map((label, i) => {
    const row: Record<string, string | number> = { period: label };
    if (props.grouped && props.series.length > 1) {
      for (const s of props.series) {
        row[s.name] = s.data[i] ?? 0;
      }
    } else {
      row.value = props.series[0]?.data[i] ?? 0;
    }
    return row;
  });
});
</script>
