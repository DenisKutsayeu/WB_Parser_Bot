from typing import Optional, Union

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, field_validator
from config import Config

SQLALCHEMY_DATABASE_URL = Config.SQLALCHEMY_DATABASE_URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(String, unique=True, index=True)
    title = Column(String)
    price = Column(Float)
    rating = Column(Float)
    total_quantity = Column(Integer)


class ProductRequest(BaseModel):
    artikul: str


class ProductInfo(BaseModel):
    name: Optional[str] = "Название не найдено"
    salePriceU: int
    rating: Union[int, float, None] = 0
    totalQuantity: Optional[int] = 0

    @field_validator("salePriceU", mode="before")
    @classmethod
    def format_price(cls, salePriceU: Optional[str]) -> int:
        if salePriceU is None:
            return 0
        return int(salePriceU) / 100


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    artikul = Column(String, unique=True, index=True, nullable=False)


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
