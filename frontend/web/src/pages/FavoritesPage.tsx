import React from 'react';
import FavoritesCard from '@/components/stock/FavoritesCard';

const FavoritesPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6 animate-fade-in pb-24 lg:pb-6 pt-0">
      <div className="flex flex-col space-y-2 mb-4">
        <h2 className="text-foreground font-bold text-lg">我的自选</h2>
        <p className="text-sm text-muted-foreground">
          管理您的自选股分组，实时查看行情动态
        </p>
      </div>

      <div className="border rounded-xl shadow-sm bg-card overflow-hidden">
        <FavoritesCard />
      </div>
    </div>
  );
};

export default FavoritesPage;
