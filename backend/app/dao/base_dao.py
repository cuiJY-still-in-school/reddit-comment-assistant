from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    """Base DAO with common CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, db: AsyncSession, model_instance: ModelType) -> Optional[ModelType]:
        try:
            db.add(model_instance)
            await db.commit()
            await db.refresh(model_instance)
            logger.info(f"DAO: Created {self.model.__name__} id={getattr(model_instance, 'id', 'unknown')}")
            return model_instance
        except Exception as e:
            await db.rollback()
            logger.error(f"DAO: Failed to create {self.model.__name__}: {e}")
            return None

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"DAO: Failed to get {self.model.__name__} by id {id}: {e}")
            return None

    async def get_all(self, db: AsyncSession, limit: int = 100, offset: int = 0) -> List[ModelType]:
        try:
            result = await db.execute(
                select(self.model).limit(limit).offset(offset)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"DAO: Failed to get all {self.model.__name__}: {e}")
            return []

    async def count(self, db: AsyncSession) -> int:
        try:
            result = await db.execute(select(func.count()).select_from(self.model))
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"DAO: Failed to count {self.model.__name__}: {e}")
            return 0

    async def update(self, db: AsyncSession, id: int, **kwargs) -> Optional[ModelType]:
        try:
            instance = await self.get_by_id(db, id)
            if not instance:
                return None
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await db.commit()
            await db.refresh(instance)
            return instance
        except Exception as e:
            await db.rollback()
            logger.error(f"DAO: Failed to update {self.model.__name__} id {id}: {e}")
            return None

    async def delete(self, db: AsyncSession, id: int) -> bool:
        try:
            result = await db.execute(delete(self.model).where(self.model.id == id))
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error(f"DAO: Failed to delete {self.model.__name__} id {id}: {e}")
            return False

    async def delete_batch(self, db: AsyncSession, ids: List[int]) -> int:
        if not ids:
            return 0
        try:
            result = await db.execute(delete(self.model).where(self.model.id.in_(ids)))
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            logger.error(f"DAO: Failed to batch delete {self.model.__name__}: {e}")
            return 0