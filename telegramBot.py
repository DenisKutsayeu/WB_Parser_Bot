from typing import Optional, Dict
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models import Product
from config import Config

API_TOKEN = Config.API_TOKEN

# Настройка бота
bot = Bot(
    token=API_TOKEN,
    session=AiohttpSession(),
    default=DefaultBotProperties(parse_mode="HTML"),
)
dp = Dispatcher()

# Настройки базы данных
ASYNC_SQLALCHEMY_DATABASE_URL = Config.ASYNC_SQLALCHEMY_DATABASE_URL
engine = create_async_engine(ASYNC_SQLALCHEMY_DATABASE_URL, echo=True, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Настройка клавиатуры
keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Получить данные по товару")]], resize_keyboard=True
)


async def get_product_by_artikul(artikul: str, session: AsyncSession) -> Optional[Dict]:
    """
    Получить информацию о товаре по артикулу.
    """
    result = await session.execute(
        Product.__table__.select().where(Product.artikul == artikul)
    )
    product = result.fetchone()
    if product:
        return {
            "artikul": product.artikul,
            "title": product.title,
            "price": product.price,
            "rating": product.rating,
            "total_quantity": product.total_quantity,
        }
    return None


@dp.message(Command("start"))
async def send_welcome(message):
    """
    Обработчик команды /start.
    """
    await message.answer(
        "Привет! Я бот для получения данных о товаре. Нажмите кнопку ниже, чтобы начать.",
        reply_markup=keyboard,
    )


@dp.message(F.text == "Получить данные по товару")
async def ask_for_artikul(message):
    """
    Обработчик нажатия кнопки "Получить данные по товару".
    """
    await message.answer("Отправьте артикул товара, чтобы получить информацию.")


@dp.message(F.text.func(lambda text: text.isdigit()))
async def get_product_info(message):
    """
    Обработчик получения артикула от пользователя.
    """
    artikul = message.text

    # Работа с асинхронной сессией SQLAlchemy
    async with async_session() as session:
        product_data = await get_product_by_artikul(artikul, session)

    if product_data:
        await message.answer(
            f"<b>Данные по товару</b> (артикул: <code>{product_data['artikul']}</code>):\n"
            f"Название: <b>{product_data['title']}</b>\n"
            f"Цена: <b>{product_data['price']} руб.</b>\n"
            f"Рейтинг: <b>{product_data['rating']}</b>\n"
            f"Количество: <b>{product_data['total_quantity']}</b>"
        )
    else:
        await message.answer(f"Товар с артикулом <code>{artikul}</code> не найден.")


@dp.message()
async def unknown_message(message):
    """
    Обработчик неизвестных сообщений.
    """
    await message.answer("Пожалуйста, отправьте корректный артикул (только цифры).")


if __name__ == "__main__":

    async def main():
        try:
            print("Бот запущен...")
            await dp.start_polling(bot)
        finally:
            await bot.session.close()

    asyncio.run(main())
