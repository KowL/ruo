import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { KLineData } from '@/types';


interface KLineChartProps {
  data: any[]; // KLineData[] | TimeShareData[]
  symbol: string;
  name: string;
  period?: string; // daily, weekly, monthly, min
  preClose?: number; // Pre-close price for min chart
  aiLayers?: {
    support: boolean;
  };
  aiAnalysis?: any;
}

const KLineChart: React.FC<KLineChartProps> = ({ data, symbol, name, period = 'daily', preClose = 0, aiLayers, aiAnalysis }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // Custom Legend State
  const [legendData, setLegendData] = useState<{
    ma5: string | number;
    ma10: string | number;
    ma20: string | number;
    ma60: string | number;
    diff: string | number; // For demo purpose or others
  }>({ ma5: '-', ma10: '-', ma20: '-', ma60: '-', diff: '-' });

  // 1. Initialization and Resize
  useEffect(() => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, []);

  // 2. Clear chart when switching periods (e.g. Min -> Day) to prevent artifacts
  useEffect(() => {
    chartInstance.current?.clear();
    setLegendData({ ma5: '-', ma10: '-', ma20: '-', ma60: '-', diff: '-' });
  }, [period]);

  // 3. Update Options
  useEffect(() => {
    if (!chartInstance.current || !data.length) return;
    const chart = chartInstance.current;
    const isMin = period === 'min';

    // Data validation
    if (data.length > 0) {
      const firstItem = data[0];
      if (isMin && !('time' in firstItem)) return;
      if (!isMin && !('date' in firstItem)) return;
    }

    let option: any = {};

    if (isMin) {
      // --- Time Sharing Mode ---
      // (Simplified: keeping existing logic mostly, but removing default legend if we want custom one)
      // For min chart, usually we have Price and AvgPrice. The user request "MA needs to show price" likely refers to K-line MAs.
      // But let's keep consistent.

      const dates = data.map((item: any) => item.time);
      const prices = data.map((item: any) => item.price);
      const avgPrices = data.map((item: any) => item.avgPrice);
      const volumes = data.map((item: any, index: number) => [index, item.volume, item.price > (data[index - 1]?.price || item.price) ? 1 : -1]);

      let basePrice = preClose && preClose > 0 ? preClose : prices[0];
      if (!basePrice || isNaN(basePrice)) basePrice = prices[0] || 0;
      if (isNaN(basePrice)) basePrice = 0;

      const maxPrice = Math.max(...prices, basePrice);
      const minPrice = Math.min(...prices, basePrice);
      const maxDiff = Math.max(Math.abs(maxPrice - basePrice), Math.abs(minPrice - basePrice));
      const range = maxDiff * 1.02;
      const safeRange = range === 0 ? (basePrice * 0.01 || 1) : range;

      const yMin = basePrice - safeRange;
      const yMax = basePrice + safeRange;
      const percentMax = (safeRange / basePrice) * 100;
      const percentMin = -percentMax;

      option = {
        backgroundColor: 'transparent',
        animation: false,
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', label: { show: false } },
          backgroundColor: 'rgba(20, 20, 20, 0.9)',
          borderColor: '#333',
          textStyle: { color: '#ccc', fontSize: 12 },
          position: (pos: any, _params: any, _dom: any, _rect: any, size: any) => {
            const obj: any = { top: 10 };
            // Keep tooltip on sides
            obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 5;
            return obj;
          },
          formatter: (params: any) => {
            // Simpler tooltip for min chart
            const item = params[0];
            if (!item) return '';
            const idx = item.dataIndex;
            const d = data[idx];
            const change = d.price - basePrice;
            const changePct = (change / basePrice) * 100;
            const color = change >= 0 ? '#ef4444' : '#10b981';

            return `
                    <div class="text-xs font-mono">
                        <div class="text-gray-400 mb-1">${d.time.split(' ')[1] || d.time}</div>
                        <div class="flex justify-between gap-4"><span class="text-gray-500">价格</span><span style="color:${color}">${d.price.toFixed(2)}</span></div>
                        <div class="flex justify-between gap-4"><span class="text-gray-500">幅%</span><span style="color:${color}">${changePct.toFixed(2)}%</span></div>
                        <div class="flex justify-between gap-4"><span class="text-gray-500">均价</span><span class="text-yellow-500">${d.avgPrice.toFixed(2)}</span></div>
                        <div class="flex justify-between gap-4"><span class="text-gray-500">量</span><span class="text-gray-300">${d.volume}</span></div>
                    </div>
                `;
          }
        },
        grid: [
          { left: '50', right: '10', top: '20', bottom: '20%' }, // Left reserved for Y-axis labels
          { left: '50', right: '10', top: '80%', bottom: '0' },
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              show: true,
              color: '#9ca3af',
              interval: (index: number, value: string) => {
                return ['09:30', '10:30', '11:30', '14:00', '15:00'].some(t => value.endsWith(t));
              },
              formatter: (value: string) => value.substring(value.length - 5)
            },
            splitLine: { show: false }
          },
          { type: 'category', data: dates, gridIndex: 1, show: false },
        ],
        yAxis: [
          {
            scale: true,
            min: yMin,
            max: yMax,
            interval: safeRange / 2,
            position: 'left',
            splitLine: { lineStyle: { color: '#333', type: 'dashed' } },
            axisLabel: {
              show: true,
              inside: false, // Move outside
              margin: 4,
              formatter: (val: number) => val.toFixed(2),
              color: (val: number) => val > basePrice ? '#ef4444' : val < basePrice ? '#10b981' : '#9ca3af'
            }
          },
          {
            min: percentMin,
            max: percentMax,
            interval: Math.abs(percentMax) / 2,
            position: 'right',
            axisLabel: { show: false }, // Hide percent axis logic for simplicity or overlay it
            splitLine: { show: false }
          },
          { gridIndex: 1, show: false }
        ],
        series: [
          {
            name: 'Price',
            type: 'line',
            data: prices,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 1.5, color: '#3b82f6' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0)' }
              ])
            },
            markLine: {
              symbol: 'none',
              silent: true,
              data: [{ yAxis: basePrice, lineStyle: { type: 'dashed', color: '#6b7280', opacity: 0.8 } }],
              label: { show: false }
            }
          },
          {
            name: 'Avg',
            type: 'line',
            data: avgPrices,
            smooth: true,
            symbol: 'none',
            lineStyle: { width: 1, color: '#eab308', opacity: 0.8 }
          },
          {
            name: 'Vol',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 2,
            data: volumes.map(v => ({
              value: v[1],
              itemStyle: { color: v[2] > 0 ? '#ef4444' : '#10b981' }
            }))
          }
        ]
      };

      // Update Legend for Min Chart (Price, Avg)
      const last = data[data.length - 1];
      if (last) {
        setLegendData({
          ma5: last.price.toFixed(2), // Reusing slots
          ma10: last.avgPrice.toFixed(2),
          ma20: '-', ma60: '-', diff: '-'
        });
      }

    } else {
      // --- Candlestick Mode ---
      const dates = data.map((item) => item.date);
      // Map extra data for tooltip: [open, close, low, high, volume, change, changePct, turnover, amount]
      const values = data.map((item) => [
        item.open,
        item.close,
        item.low,
        item.high,
        item.volume,
        item.change || 0,
        item.changePct || 0,
        item.turnover || 0,
        item.amount || 0
      ]);
      const volumes = data.map((item, index) => ({
        value: item.volume,
        itemStyle: { color: item.close >= item.open ? '#ef4444' : '#10b981' }
      }));

      // Calculate MAs
      const calculateMA = (dayCount: number) => {
        const result = [];
        for (let i = 0, len = data.length; i < len; i++) {
          if (i < dayCount - 1) {
            result.push('-');
            continue;
          }
          let sum = 0;
          for (let j = 0; j < dayCount; j++) {
            sum += data[i - j].close;
          }
          result.push(+(sum / dayCount).toFixed(2));
        }
        return result;
      };

      const ma5 = calculateMA(5);
      const ma10 = calculateMA(10);
      const ma20 = calculateMA(20);
      const ma60 = calculateMA(60);

      // Support levels
      let markLineData: any[] = [];
      if (aiLayers?.support) {
        if (aiAnalysis && aiAnalysis.support_resistance) {
          const { support, resistance } = aiAnalysis.support_resistance;
          if (support) markLineData.push({ yAxis: support, lineStyle: { color: '#d946ef', type: 'dashed' }, label: { show: false } });
          if (resistance) markLineData.push({ yAxis: resistance, lineStyle: { color: '#f97316', type: 'dashed' }, label: { show: false } });
        } else {
          // Fallback local min/max
          const lows = data.slice(-30).map(d => d.low);
          const highs = data.slice(-30).map(d => d.high);
          markLineData.push({ yAxis: Math.min(...lows), lineStyle: { color: '#d946ef', opacity: 0.5 } });
          markLineData.push({ yAxis: Math.max(...highs), lineStyle: { color: '#f97316', opacity: 0.5 } });
        }
      }

      // Calculate Zoom Start to show last 60 bars
      const totalBars = data.length;
      const zoomCount = 60;
      let zoomStart = 0;
      if (totalBars > zoomCount) {
        zoomStart = 100 - (zoomCount / totalBars) * 100;
      }

      const formatNumber = (num: number, unit: string = '') => {
        if (!num) return '--';
        if (num > 100000000) return (num / 100000000).toFixed(2) + '亿' + unit;
        if (num > 10000) return (num / 10000).toFixed(2) + '万' + unit;
        return num.toFixed(2) + unit;
      };

      option = {
        animation: false,
        backgroundColor: 'transparent',
        grid: [
          { left: '50', right: '10', top: '25', height: '65%' }, // Main chart extended down
          { left: '50', right: '10', top: '80%', height: '15%' }, // Volume chart
        ],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', label: { show: false } },
          backgroundColor: 'rgba(10, 10, 10, 0.9)', // Dark background
          borderColor: '#374151',
          borderWidth: 1,
          textStyle: { fontSize: 12, color: '#9ca3af' },
          extraCssText: 'backdrop-filter: blur(4px); padding: 8px;', // Compact padding
          position: (pos: any, _params: any, _dom: any, _rect: any, size: any) => {
            const obj: any = { top: 40 };
            // Smart positioning safety check
            if (!size || !size.viewSize) return obj;

            // Smart positioning: if mouse is on the left half, show tooltip on the right; otherwise left.
            const isLeft = pos[0] < size.viewSize[0] / 2;
            obj[isLeft ? 'right' : 'left'] = 10;
            return obj;
          },
          formatter: (params: any) => {
            const item = params.find((p: any) => p.seriesType === 'candlestick');
            if (!item) return '';

            // value: [index, open, close, low, high, volume, change, changePct, turnover, amount]
            const [open, close, low, high, vol, change, pct, turnover, amount] = item.value.slice(1);

            const color = close >= open ? '#ef4444' : '#10b981';
            const colorChange = (change || 0) >= 0 ? '#ef4444' : '#10b981';

            const volStr = formatNumber(vol / 100, '手');
            const amtStr = formatNumber(amount);

            // Compact row
            const row = (label: string, val: string | number, color: string = '#d1d5db') => `
               <div class="flex justify-between items-center gap-4 text-xs leading-5">
                   <span class="text-gray-500">${label}</span>
                   <span class="font-mono" style="color: ${color}">${val}</span>
               </div>
            `;

            return `
                 <div class="min-w-[140px]">
                     <div class="text-gray-400 text-xs mb-1 border-b border-gray-700 pb-1">${item.name}</div>
                     ${row('开盘', open, close >= open ? '#10b981' : '#ef4444')} 
                     ${row('最高', high, '#ef4444')}
                     ${row('最低', low, '#10b981')}
                     ${row('收盘', close, color)}
                     ${row('涨跌', change ? change.toFixed(2) : '--', colorChange)}
                     ${row('幅%', (pct ? pct.toFixed(2) : '--') + '%', colorChange)}
                     ${row('成交', volStr)}
                     ${row('金额', amtStr)}
                     ${row('换手', (turnover ? turnover.toFixed(2) : '--') + '%')}
                 </div>
               `;
          }
        },
        xAxis: [
          {
            type: 'category',
            data: dates,
            axisLine: { lineStyle: { color: '#333' } },
            axisLabel: { show: false }, // Hide middle labels
            splitLine: { show: false },
          },
          {
            type: 'category',
            data: dates,
            gridIndex: 1,
            show: true, // Show bottom X-axis
            axisLine: { lineStyle: { color: '#333' } },
            axisLabel: { show: true, color: '#9ca3af', showMaxLabel: true },
            splitLine: { show: false }
          },
        ],
        yAxis: [
          {
            scale: true,
            position: 'left',
            splitLine: { lineStyle: { color: '#333', type: 'dashed', opacity: 0.5 } },
            axisLabel: { show: true, color: '#6b7280', margin: 4 }
          },
          {
            scale: true,
            gridIndex: 1,
            splitLine: { show: false },
            axisLabel: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: zoomStart,
            end: 100,
            zoomOnMouseWheel: true,
            moveOnMouseWheel: true,
            moveOnMouseMove: true
          },
          {
            show: false,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '0%',
            height: 20,
            start: zoomStart,
            end: 100,
            borderColor: '#374151',
            textStyle: { color: '#9ca3af' }
          },
        ],
        series: [
          {
            name: 'KLine',
            type: 'candlestick',
            data: values,
            itemStyle: {
              color: '#ef4444',
              color0: '#10b981',
              borderColor: '#ef4444',
              borderColor0: '#10b981',
            },
            markLine: {
              symbol: 'none',
              data: markLineData,
              silent: true,
              label: { show: true, position: 'insideEndTop', color: 'inherit', fontSize: 10 }
            }
          },
          { name: 'MA5', type: 'line', data: ma5, smooth: true, symbol: 'none', lineStyle: { width: 1, color: '#3b82f6' } },
          { name: 'MA10', type: 'line', data: ma10, smooth: true, symbol: 'none', lineStyle: { width: 1, color: '#eab308' } },
          { name: 'MA20', type: 'line', data: ma20, smooth: true, symbol: 'none', lineStyle: { width: 1, color: '#d946ef' } },
          { name: 'MA60', type: 'line', data: ma60, smooth: true, symbol: 'none', lineStyle: { width: 1, color: '#10b981' } },
          {
            name: 'Vol',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
          }
        ]
      };

      // Set initial (latest) legend values
      const lastIdx = data.length - 1;
      setLegendData({
        ma5: ma5[lastIdx] || '-',
        ma10: ma10[lastIdx] || '-',
        ma20: ma20[lastIdx] || '-',
        ma60: ma60[lastIdx] || '-',
        diff: '-'
      });

      // Setup event listener for mouse move to update legend
      // We use 'updateAxisPointer' event which fires when mouse moves
      chart.getZr().off('mousemove'); // Clean up potentially? ECharts handles internal events

      // PROBLEM: 'updateAxisPointer' event usage in React loop.
      // Better: bind event handler once.
      // Since `useEffect` re-runs on `data` change, we can re-bind.

      chart.off('updateAxisPointer');
      chart.on('updateAxisPointer', (event: any) => {
        const dataIndex = event.dataIndex; // This might be null or inside axesInfo
        if (dataIndex != null) {
          // event.dataIndex might be undefined for 'updateAxisPointer', need to check batch
        }

        // Safer way: user params from axisPointer
        const axisInfo = event.axesInfo?.[0]; // x axis
        if (axisInfo) {
          const idx = axisInfo.value;
          if (typeof idx === 'number' && data[idx]) {
            setLegendData({
              ma5: ma5[idx] || '-',
              ma10: ma10[idx] || '-',
              ma20: ma20[idx] || '-',
              ma60: ma60[idx] || '-',
              diff: '-'
            });
          }
        }
      });

      // Reset to last value on mouse out?
      chart.getZr().on('globalout', () => {
        const last = data.length - 1;
        setLegendData({
          ma5: ma5[last] || '-',
          ma10: ma10[last] || '-',
          ma20: ma20[last] || '-',
          ma60: ma60[last] || '-',
          diff: '-'
        });
      });
    }

    chart.setOption(option, { notMerge: true }); // Reset option for clean switch

  }, [data, symbol, name, period, preClose, aiLayers, aiAnalysis]);

  const isMin = period === 'min';

  return (
    <div className="relative w-full h-[600px] group">
      {/* Custom Legend Overlay */}
      <div className="absolute top-0 left-12 z-10 text-xs font-mono flex gap-4 pointer-events-none select-none">
        {isMin ? (
          <>
            <div className="flex items-center gap-1">
              <span className="text-[#3b82f6] font-bold">价格:</span>
              <span className="text-[#3b82f6]">{legendData.ma5}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#eab308] font-bold">均价:</span>
              <span className="text-[#eab308]">{legendData.ma10}</span>
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-1">
              <span className="text-[#3b82f6]">MA5:</span>
              <span className="text-gray-300">{legendData.ma5}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#eab308]">MA10:</span>
              <span className="text-gray-300">{legendData.ma10}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#d946ef]">MA20:</span>
              <span className="text-gray-300">{legendData.ma20}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[#10b981]">MA60:</span>
              <span className="text-gray-300">{legendData.ma60}</span>
            </div>
          </>
        )}
      </div>

      <div ref={chartRef} className="w-full h-full" />
    </div>
  );
};

export default KLineChart;
