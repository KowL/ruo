import { motion } from 'framer-motion';
import { Cloud, Sun, CloudRain, CloudSnow, Wind, Droplets } from 'lucide-react';
import type { Weather } from '@/types';

interface WeatherCardProps {
  weather: Weather;
}

const weatherIcons: Record<string, React.ElementType> = {
  '晴': Sun,
  '多云': Cloud,
  '小雨': CloudRain,
  '雪': CloudSnow,
};

export function WeatherCard({ weather }: WeatherCardProps) {
  const CurrentIcon = weatherIcons[weather.current.condition] || Cloud;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="p-5 rounded-xl bg-gradient-to-br from-[#1E293B] to-[#1E293B]/80 border border-[#334155]"
    >
      {/* Current Weather */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-[#94A3B8] text-sm mb-1">今日天气</p>
          <div className="flex items-baseline gap-2">
            <span className="text-[#F8FAFC] text-4xl font-bold">{weather.current.temp}°</span>
            <span className="text-[#94A3B8] text-lg">{weather.current.condition}</span>
          </div>
        </div>
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#F59E0B]/20 to-[#F59E0B]/5 flex items-center justify-center">
          <CurrentIcon className="w-8 h-8 text-[#F59E0B]" />
        </div>
      </div>

      {/* Details */}
      <div className="flex items-center gap-6 mb-6">
        <div className="flex items-center gap-2">
          <Wind className="w-4 h-4 text-[#94A3B8]" />
          <span className="text-[#94A3B8] text-sm">3级</span>
        </div>
        <div className="flex items-center gap-2">
          <Droplets className="w-4 h-4 text-[#94A3B8]" />
          <span className="text-[#94A3B8] text-sm">45%</span>
        </div>
      </div>

      {/* Forecast */}
      <div className="border-t border-[#334155] pt-4">
        <p className="text-[#94A3B8] text-xs mb-3">未来5天</p>
        <div className="flex justify-between">
          {weather.forecast.map((day, index) => {
            const DayIcon = weatherIcons[day.condition] || Cloud;
            return (
              <div key={index} className="flex flex-col items-center gap-1">
                <span className="text-[#94A3B8] text-xs">{day.day}</span>
                <DayIcon className="w-4 h-4 text-[#94A3B8]" />
                <span className="text-[#F8FAFC] text-sm font-medium">{day.temp}°</span>
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
