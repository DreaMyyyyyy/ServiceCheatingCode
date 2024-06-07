from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Импортируем базовый класс для моделей

# Подключение к базе данных (замените на ваши параметры подключения)
DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Создаем все таблицы, определенные в моделях
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("База данных успешно инициализирована")
