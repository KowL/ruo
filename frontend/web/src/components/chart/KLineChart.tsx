import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { KLineData } from '@/types';

interface KLineChartProps {
  data: KLineData[];
  symbol: string;
  name: string;
}

const KLineChart: React.FC<KLineChartProps> = ({ data, symbol, name }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !data.length) return;

    const chart = echarts.init(chartRef.current);

    const dates = data.map((item) => item.date);
    const values = data.map((item) => [item.open, item.close, item.low, item.high]);
    const volumes = data.map((item) => item.volume);

    const option = {
      title: {
        text: `${name} (${symbol})`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['K线', '成交量'],
        top: 30,
      },
      grid: [
        {
          left: '10%',
          right: '10%',
          top: '15%',
          height: '50%',
        },
        {
          left: '10%',
          right: '10%',
          top: '70%',
          height: '15%',
        },
      ],
      xAxis: [
        {
          type: 'category',
          data: dates,
          gridIndex: 0,
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
        },
      ],
      yAxis: [
        {
          scale: true,
          gridIndex: 0,
        },
        {
          scale: true,
          gridIndex: 1,
        },
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 50,
          end: 100,
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          bottom: '5%',
          start: 50,
          end: 100,
        },
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: values,
          xAxisIndex: 0,
          yAxisIndex: 0,
          itemStyle: {
            color: '#ef4444',
            color0: '#10b981',
            borderColor: '#ef4444',
            borderColor0: '#10b981',
          },
        },
        {
          name: '成交量',
          type: 'bar',
          data: volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
          itemStyle: {
            color: '#93c5fd',
          },
        },
      ],
    };

    chart.setOption(option);

    // 响应式
    const handleResize = () => {
      chart.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.dispose();
    };
  }, [data, symbol, name]);

  return <div ref={chartRef} className="w-full h-[600px]" />;
};

export default KLineChart;
