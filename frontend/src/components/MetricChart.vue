<template>
  <v-chart :option="chartOption" :style="{ height: '250px', width: '100%' }" autoresize />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { colorFor } from '@/utils/colors';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const props = defineProps<{
  labels: string[];
  series: { name: string; data: number[]; color?: string }[];
  grouped: boolean;
  metricName?: string;
}>();

const chartOption = computed(() => {
  const seriesData = props.series.map((s) => ({
    type: 'bar' as const,
    name: s.name,
    data: s.data,
    stack: props.grouped ? 'stack' : undefined,
    itemStyle: {
      color: props.grouped ? colorFor(s.name) : colorFor(props.metricName || s.name),
      borderRadius: [2, 2, 0, 0],
    },
  }));

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis' as const,
    },
    legend: props.grouped
      ? {
          show: true,
          textStyle: { color: '#bdbdbd' },
          bottom: 0,
        }
      : { show: false },
    grid: {
      left: 50,
      right: 16,
      top: 16,
      bottom: props.grouped ? 40 : 24,
    },
    xAxis: {
      type: 'category' as const,
      data: props.labels,
      axisLine: { lineStyle: { color: '#616161' } },
      axisLabel: { color: '#9e9e9e', fontSize: 11 },
    },
    yAxis: {
      type: 'value' as const,
      axisLine: { show: false },
      axisLabel: { color: '#9e9e9e' },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: seriesData,
  };
});
</script>
