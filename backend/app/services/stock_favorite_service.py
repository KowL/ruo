"""
自选股票服务 - Stock Favorite Service
功能：自选分组和自选股票的 CRUD 操作
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.models.stock_group import StockGroup
from app.models.stock_favorite import StockFavorite

logger = logging.getLogger(__name__)


class StockFavoriteService:
    """自选股票服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 分组管理 ====================

    def create_group(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False
    ) -> Dict:
        """创建自选分组"""
        try:
            # 如果设为默认分组，先取消其他默认分组
            if is_default:
                self.db.query(StockGroup).filter(
                    StockGroup.user_id == user_id,
                    StockGroup.is_default == True
                ).update({'is_default': False})

            group = StockGroup(
                user_id=user_id,
                name=name,
                description=description,
                is_default=is_default
            )
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)

            return self._build_group_response(group)

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建分组失败: {e}")
            raise

    def get_groups(self, user_id: int) -> List[Dict]:
        """获取用户自选分组列表"""
        try:
            groups = self.db.query(StockGroup).filter(
                StockGroup.user_id == user_id
            ).order_by(StockGroup.is_default.desc(), StockGroup.created_at.desc()).all()

            return [self._build_group_response(g) for g in groups]

        except Exception as e:
            logger.error(f"获取分组列表失败: {e}")
            raise

    def get_group(self, group_id: int, user_id: int) -> Optional[Dict]:
        """获取分组详情"""
        try:
            group = self.db.query(StockGroup).filter(
                StockGroup.id == group_id,
                StockGroup.user_id == user_id
            ).first()

            if not group:
                return None

            return self._build_group_response(group)

        except Exception as e:
            logger.error(f"获取分组详情失败: {e}")
            raise

    def update_group(
        self,
        group_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> Dict:
        """更新分组"""
        try:
            group = self.db.query(StockGroup).filter(
                StockGroup.id == group_id,
                StockGroup.user_id == user_id
            ).first()

            if not group:
                raise ValueError(f"分组不存在: {group_id}")

            # 如果设为默认分组，先取消其他默认分组
            if is_default is True and not group.is_default:
                self.db.query(StockGroup).filter(
                    StockGroup.user_id == user_id,
                    StockGroup.is_default == True,
                    StockGroup.id != group_id
                ).update({'is_default': False})

            if name is not None:
                group.name = name
            if description is not None:
                group.description = description
            if is_default is not None:
                group.is_default = is_default

            self.db.commit()
            self.db.refresh(group)

            return self._build_group_response(group)

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新分组失败: {e}")
            raise

    def delete_group(self, group_id: int, user_id: int) -> bool:
        """删除分组（同时删除组内自选股票）"""
        try:
            group = self.db.query(StockGroup).filter(
                StockGroup.id == group_id,
                StockGroup.user_id == user_id
            ).first()

            if not group:
                raise ValueError(f"分组不存在: {group_id}")

            # 删除组内自选股票
            self.db.query(StockFavorite).filter(
                StockFavorite.group_id == group_id,
                StockFavorite.user_id == user_id
            ).delete()

            # 删除分组
            self.db.delete(group)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除分组失败: {e}")
            raise

    # ==================== 自选股票管理 ====================

    def add_stock(
        self,
        user_id: int,
        group_id: int,
        symbol: str,
        name: str
    ) -> Dict:
        """添加自选股票"""
        try:
            # 检查分组是否存在
            group = self.db.query(StockGroup).filter(
                StockGroup.id == group_id,
                StockGroup.user_id == user_id
            ).first()

            if not group:
                raise ValueError(f"分组不存在: {group_id}")

            # 检查股票是否已存在于该分组
            existing = self.db.query(StockFavorite).filter(
                StockFavorite.user_id == user_id,
                StockFavorite.group_id == group_id,
                StockFavorite.symbol == symbol
            ).first()

            if existing:
                raise ValueError(f"股票 {symbol} 已存在于该分组")

            favorite = StockFavorite(
                user_id=user_id,
                group_id=group_id,
                symbol=symbol,
                name=name
            )
            self.db.add(favorite)
            self.db.commit()
            self.db.refresh(favorite)

            return self._build_favorite_response(favorite)

        except Exception as e:
            self.db.rollback()
            logger.error(f"添加自选股票失败: {e}")
            raise

    def get_stocks(
        self,
        user_id: int,
        group_id: Optional[int] = None
    ) -> List[Dict]:
        """获取自选股票列表"""
        try:
            query = self.db.query(StockFavorite).filter(
                StockFavorite.user_id == user_id
            )

            if group_id:
                query = query.filter(StockFavorite.group_id == group_id)

            favorites = query.order_by(StockFavorite.added_at.desc()).all()

            return [self._build_favorite_response(f) for f in favorites]

        except Exception as e:
            logger.error(f"获取自选股票列表失败: {e}")
            raise

    def get_all_stocks(self, user_id: int) -> List[Dict]:
        """获取用户所有自选股票"""
        try:
            favorites = self.db.query(StockFavorite).filter(
                StockFavorite.user_id == user_id
            ).order_by(StockFavorite.added_at.desc()).all()

            return [self._build_favorite_response(f) for f in favorites]

        except Exception as e:
            logger.error(f"获取所有自选股票失败: {e}")
            raise

    def get_stock_symbols(self, user_id: int, group_id: Optional[int] = None) -> List[str]:
        """获取自选股票代码列表"""
        try:
            query = self.db.query(StockFavorite.symbol).filter(
                StockFavorite.user_id == user_id
            )

            if group_id:
                query = query.filter(StockFavorite.group_id == group_id)

            results = query.all()
            return [r[0] for r in results]

        except Exception as e:
            logger.error(f"获取自选股票代码列表失败: {e}")
            raise

    def delete_stock(self, favorite_id: int, user_id: int) -> bool:
        """删除自选股票"""
        try:
            favorite = self.db.query(StockFavorite).filter(
                StockFavorite.id == favorite_id,
                StockFavorite.user_id == user_id
            ).first()

            if not favorite:
                raise ValueError(f"自选股票不存在: {favorite_id}")

            self.db.delete(favorite)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除自选股票失败: {e}")
            raise

    def move_stock(
        self,
        favorite_id: int,
        user_id: int,
        new_group_id: int
    ) -> Dict:
        """移动自选股票到其他分组"""
        try:
            favorite = self.db.query(StockFavorite).filter(
                StockFavorite.id == favorite_id,
                StockFavorite.user_id == user_id
            ).first()

            if not favorite:
                raise ValueError(f"自选股票不存在: {favorite_id}")

            # 检查新分组是否存在
            group = self.db.query(StockGroup).filter(
                StockGroup.id == new_group_id,
                StockGroup.user_id == user_id
            ).first()

            if not group:
                raise ValueError(f"目标分组不存在: {new_group_id}")

            # 检查目标分组是否已有该股票
            existing = self.db.query(StockFavorite).filter(
                StockFavorite.user_id == user_id,
                StockFavorite.group_id == new_group_id,
                StockFavorite.symbol == favorite.symbol
            ).first()

            if existing:
                raise ValueError(f"股票 {favorite.symbol} 已存在于目标分组")

            favorite.group_id = new_group_id
            self.db.commit()
            self.db.refresh(favorite)

            return self._build_favorite_response(favorite)

        except Exception as e:
            self.db.rollback()
            logger.error(f"移动自选股票失败: {e}")
            raise

    # ==================== 搜索股票 ====================

    def search_stocks(self, keyword: str, user_id: int, limit: int = 20) -> List[Dict]:
        """搜索股票（从数据库）"""
        try:
            from app.models.stock import Stock

            query = self.db.query(Stock).filter(
                or_(
                    Stock.symbol.like(f"%{keyword}%"),
                    Stock.name.like(f"%{keyword}%")
                ),
                Stock.is_active == True
            ).limit(limit)

            stocks = query.all()

            # 获取用户已有的自选股票
            existing = self.db.query(StockFavorite.symbol).filter(
                StockFavorite.user_id == user_id
            ).all()
            existing_symbols = {s[0] for s in existing}

            result = []
            for stock in stocks:
                result.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'sector': stock.sector,
                    'industry': stock.industry,
                    'market': stock.market,
                    'isFavorited': stock.symbol in existing_symbols
                })

            return result

        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            raise

    # ==================== 辅助方法 ====================

    def _build_group_response(self, group: StockGroup) -> Dict:
        """构建分组响应"""
        # 获取股票数量
        stock_count = self.db.query(StockFavorite).filter(
            StockFavorite.group_id == group.id,
            StockFavorite.user_id == group.user_id
        ).count()

        return {
            'id': group.id,
            'userId': group.user_id,
            'name': group.name,
            'description': group.description,
            'isDefault': group.is_default,
            'stockCount': stock_count,
            'createdAt': group.created_at.isoformat() if group.created_at else None,
            'updatedAt': group.updated_at.isoformat() if group.updated_at else None
        }

    def _build_favorite_response(self, favorite: StockFavorite) -> Dict:
        """构建自选股票响应"""
        return {
            'id': favorite.id,
            'userId': favorite.user_id,
            'groupId': favorite.group_id,
            'symbol': favorite.symbol,
            'name': favorite.name,
            'addedAt': favorite.added_at.isoformat() if favorite.added_at else None
        }
