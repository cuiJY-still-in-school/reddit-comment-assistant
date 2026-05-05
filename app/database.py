from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from app.models.user import User
    from app.models.persona import Persona
    from app.models.post_record import PostRecord
    from app.models.comment_result import CommentResult
    from app.models.style_sample import StyleSample
    from app.models.style_profile import StyleProfile

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
