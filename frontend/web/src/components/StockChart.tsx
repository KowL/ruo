import { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface StockChartProps {
  data: Array<{
    time: string;
    price: number;
    volume: number;
  }>;
}

export function StockChart({ data }: StockChartProps) {
  const [timeRange, setTimeRange] = useState('1D');

  const minPrice = Math.min(...data.map(d => d.price));
  const maxPrice = Math.max(...data.map(d => d.price));
  const priceRange = maxPrice - minPrice;

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <Tabs value={timeRange} onValueChange={setTimeRange}>
          <TabsList className="bg-[#334155]">
            {['1D', '5D', '1M', '3M', '1Y'].map((range) => (
              <TabsTrigger
                key={range}
                value={range}
                className="data-[state=active]:bg-[#2563EB] data-[state=active]:text-white text-[#94A3B8]"
              >
                {range}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-[#94A3B8]">最高:</span>
            <span className="text-[#F8FAFC] font-mono">{maxPrice.toFixed(2)}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#94A3B8]">最低:</span>
            <span className="text-[#F8FAFC] font-mono">{minPrice.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#94A3B8"
              tick={{ fill: '#94A3B8', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />
            <YAxis
              domain={[minPrice - priceRange * 0.1, maxPrice + priceRange * 0.1]}
              stroke="#94A3B8"
              tick={{ fill: '#94A3B8', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => value.toFixed(2)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1E293B',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#F8FAFC',
              }}
              labelStyle={{ color: '#94A3B8' }}
              formatter={(value: any) => [`¥${Number(value).toFixed(2)}`, '价格']}
            />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#2563EB"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrice)"
              animationDuration={500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
