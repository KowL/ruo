import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { KLineData } from '@/types';

interface KLineChartProps {
  data: KLineData[];
  symbol: string;
  name: string;
  aiLayers?: {
    support: boolean;
    pattern: boolean;
    signal: boolean;
  };
}

const KLineChart: React.FC<KLineChartProps> = ({ data, symbol, name, aiLayers }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current || !data.length) return;

    const chart = echarts.init(chartRef.current);

    const dates = data.map((item) => item.date);
    // Map data to ECharts format: [open, close, low, high, volume, amount, change, changePct, turnover]
    const values = data.map((item) => [
      item.open,
      item.close,
      item.low,
      item.high,
      item.volume,
      item.amount || 0,
      item.change || 0,
      item.changePct || 0,
      item.turnover || 0
    ]);
    const volumes = data.map((item, index) => [index, item.volume, item.close > item.open ? 1 : -1]);

    // Format helper
    const formatNumber = (num: number) => {
      if (Math.abs(num) > 100000000) return (num / 100000000).toFixed(2) + '亿';
      if (Math.abs(num) > 10000) return (num / 10000).toFixed(2) + '万';
      return num.toFixed(2);
    };

    const getTextColor = (val: number) => {
      if (val > 0) return '#ef4444';
      if (val < 0) return '#10b981';
      return '#fff';
    };

    // AI Layers Logic
    let markLineData: any[] = [];
    let markPointData: any[] = [];

    // 1. Support/Resistance (Simplified: Lowest/Highest in last 30 days)
    if (aiLayers?.support) {
      const recentLow = Math.min(...data.slice(-30).map(d => d.low));
      const recentHigh = Math.max(...data.slice(-30).map(d => d.high));

      markLineData.push(
        {
          yAxis: recentLow,
          name: '支撑位',
          lineStyle: { type: 'dashed', color: '#9d28d0', width: 2 },
          label: { formatter: '支撑 {c}', position: 'start', color: '#9d28d0' }
        },
        {
          yAxis: recentHigh,
          name: '压力位',
          lineStyle: { type: 'dashed', color: '#ff9500', width: 2 },
          label: { formatter: '压力 {c}', position: 'start', color: '#ff9500' }
        }
      );
    }

    // 2. Signals (Mock Algorithm: RSI-like logic or just simple logic for demo)
    if (aiLayers?.signal) {
      // Simple Demo Logic: If close is higher than open by 5%, mark Buy
      data.forEach((item, index) => {
        // Mock signals for demonstration on recent bars
        if (index > data.length - 10) {
          const change = (item.close - item.open) / item.open;
          if (change > 0.03) {
            markPointData.push({
              coord: [dates[index], item.high],
              value: 'B',
              itemStyle: { color: '#ef4444' },
              label: { show: true, fontSize: 10 }
            });
          } else if (change < -0.03) {
            markPointData.push({
              coord: [dates[index], item.low],
              value: 'S',
              itemStyle: { color: '#10b981' }, // Green for Sell (CN market) or standard coloring
              symbolRotate: 180,
              label: { show: true, fontSize: 10, offset: [0, 10] }
            });
          }
        }
      });
    }

    const option = {
      backgroundColor: 'transparent',
      title: {
        text: `${name} (${symbol})`,
        left: 'center',
        textStyle: { color: '#9ca3af', fontSize: 14 }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { show: true, backgroundColor: '#333' } },
        backgroundColor: 'rgba(20, 20, 20, 0.95)',
        borderColor: '#333',
        textStyle: { color: '#ccc', fontSize: 12 },
        padding: 10,
        confine: true,
        formatter: function (params: any) {
          const item = params.find((p: any) => p.seriesType === 'candlestick');
          if (!item) return '';

          const rawData = item.value;
          // index 0=date(not in value array here but handled by axis), 1=open, 2=close, 3=low, 4=high, 5=volume, 6=amount, 7=change, 8=pct, 9=turnover
          // Note: ECharts adds category axis value at index 0 in the `value` array if dimensions are not fully specified, 
          // or we access it via raw data index.
          // Let's rely on the order we passed: [open, close, low, high, volume, amount, change, changePct, turnover]
          // When using category axis, `item.value` is [index, open, close, low, high, ...] 

          const open = rawData[1];
          const close = rawData[2];
          const low = rawData[3];
          const high = rawData[4];
          const change = rawData[7];
          const changePct = rawData[8];
          const volume = rawData[5];
          const amount = rawData[6];
          const turnover = rawData[9];

          const color = getTextColor(change);

          // Helper for row
          const row = (label: string, val: string, color: string = '#ccc') => {
            return `<div style="display:flex;justify-content:space-between;min-width:140px;line-height:1.8;">
                        <span style="color:#888">${label}</span>
                        <span style="color:${color};font-family:monospace;font-weight:bold">${val}</span>
                      </div>`;
          };

          let html = `<div style="font-size:12px;">`;
          html += `<div style="margin-bottom:4px;color:#fff">${item.name}</div>`; // Date
          html += row('开盘价', open.toFixed(2), getTextColor(open - rawData[2] + change)); // colors are usually relative to prev close, simplified here
          html += row('最高价', high.toFixed(2), getTextColor(high - rawData[2] + change));
          html += row('最低价', low.toFixed(2), getTextColor(low - rawData[2] + change));
          html += row('收盘价', close.toFixed(2), color);
          html += row('涨跌额', (change > 0 ? '+' : '') + change.toFixed(2), color);
          html += row('涨跌幅', (changePct > 0 ? '+' : '') + changePct.toFixed(2) + '%', color);
          html += row('成交量', formatNumber(volume) + '手');
          html += row('成交额', formatNumber(amount));
          html += row('换手率', turnover.toFixed(2) + '%');
          html += `</div>`;

          return html;
        }
      },
      legend: {
        data: ['K线', '成交量'],
        top: 30,
        textStyle: { color: '#9ca3af' }
      },
      grid: [
        { left: '5%', right: '5%', top: '10%', height: '60%' },
        { left: '5%', right: '5%', top: '75%', height: '15%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#374151' } } },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#374151' } } },
      ],
      yAxis: [
        { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#374151', opacity: 0.3 } } },
        { scale: true, gridIndex: 1, splitLine: { show: false } }, // Volume yAxis
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
        { show: true, xAxisIndex: [0, 1], type: 'slider', bottom: '0%', start: 70, end: 100, borderColor: '#374151' },
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
          markLine: {
            symbol: ['none', 'none'],
            data: markLineData,
            animation: false
          },
          markPoint: {
            symbol: 'pin',
            symbolSize: 30,
            data: markPointData,
            animation: true
          }
        },
        {
          name: '成交量',
          type: 'bar',
          data: volumes,
          xAxisIndex: 1,
          yAxisIndex: 1,
          itemStyle: { color: '#60a5fa' },
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
  }, [data, symbol, name, aiLayers]);

  return <div ref={chartRef} className="w-full h-[600px]" />;
};

export default KLineChart;
