import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.models.models import Base # Импортируем базовый класс для моделей
from src.config.config import config

# Подключение к базе данных (замените на ваши параметры подключения)
DATABASE_URL = f"postgresql+asyncpg://{config.db_user}:{config.db_password}"
DATABASE_URL += f"@{config.db_host}:{config.db_port}/{config.db_name}"

# Создание асинхронного движка
engine = create_async_engine(DATABASE_URL)  # echo=True для отладки

# Создание асинхронной фабрики сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Функция для создания всех таблиц
async def create_tables():
    async with engine.begin() as conn:
        logger = logging.getLogger("ServiceCheatingGraphics")
        logger.debug("Initialization of database.")
        await conn.run_sync(Base.metadata.create_all)
        logger.debug("Initialization of database complete.")


# Функция для получения сессии
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


if __name__ == "__main__":
    create_tables()
