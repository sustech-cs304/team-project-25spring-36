from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_DRIVER = "postgresql"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ide"
DB_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL, echo=True)
session = sessionmaker(bind=engine)


def database():
    db = session()
    try:
        yield db
    finally:
        db.close()
