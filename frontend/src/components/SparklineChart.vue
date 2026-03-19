<template>
  <v-chart :option="chartOption" :style="{ height: '80px', width: '100%' }" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, BarChart, GridComponent]);

const props = defineProps<{
  data: number[];
  color: string;
}>();

const chartOption = computed(() => ({
  grid: {
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  xAxis: {
    type: 'category' as const,
    show: false,
    data: props.data.map((_, i) => i),
  },
  yAxis: {
    type: 'value' as const,
    show: false,
  },
  series: [
    {
      type: 'bar' as const,
      data: props.data,
      itemStyle: {
        color: props.color,
        borderRadius: [2, 2, 0, 0],
      },
      barWidth: '60%',
    },
  ],
  animation: false,
}));
</script>
