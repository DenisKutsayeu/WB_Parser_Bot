from sqlite3 import IntegrityError

import requests
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from models import Product, SessionLocal, ProductRequest, Subscription, ProductInfo
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
import uvicorn

app = FastAPI()
scheduler = BackgroundScheduler()


def save_product_to_db(artikul: str, product_info: ProductInfo) -> None:
    """
    Сохранение данных о продукте в базу данных с использованием модели Pydantic.
    """
    db = SessionLocal()
    try:
        db_product = db.query(Product).filter_by(artikul=artikul).first()

        if db_product:
            db_product.title = product_info.name
            db_product.price = product_info.salePriceU
            db_product.rating = product_info.rating or 0
            db_product.total_quantity = product_info.totalQuantity
        else:
            db_product = Product(
                artikul=artikul,
                title=product_info.name,
                price=product_info.salePriceU,
                rating=product_info.rating or 0,
                total_quantity=product_info.totalQuantity,
            )
            db.add(db_product)

        db.commit()
        db.refresh(db_product)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Ошибка при сохранении в БД: {str(e)}"
        )
    finally:
        db.close()


def get_art_info(article: str) -> ProductInfo:
    response = requests.get(
        f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
    )

    if response.status_code != 200:
        raise Exception(f"Ошибка запроса: статус {response.status_code}")

    data = response.json()

    product = data.get("data", {}).get("products", [{}])[0]

    try:
        validated_product = ProductInfo(**product)
        return validated_product
    except ValidationError as e:
        raise HTTPException(
            status_code=422, detail=f"Ошибка валидации данных: {e.json()}"
        )


def launch_data_gather():
    """
    Периодический сбор данных.
    """
    db = SessionLocal()
    try:
        subscriptions = db.query(Subscription).all()
        for subscription in subscriptions:
            artikul = subscription.artikul
            try:
                product_info = get_art_info(artikul)
                save_product_to_db(artikul, product_info)
                logger.info(f"Данные для артикула - {artikul} успешно обновлены!")
            except Exception as e:
                logger.error(f"Ошибка для артикула {artikul}: {str(e)}")
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    scheduler.add_job(
        launch_data_gather, "interval", minutes=30
    )  # Запуск каждые 30 минут
    scheduler.start()


@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


@app.post("/api/v1/products")
async def create_product(product_request: ProductRequest):
    try:
        article = product_request.artikul
        if not article:
            raise HTTPException(status_code=400, detail="Артикул не указан")

        product_info = get_art_info(article)

        save_product_to_db(article, product_info)

        return {
            "message": "Данные успешно сохранены",
            "product": product_info.dict(),  # Возвращаем данные в виде словаря
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/subscribe/{artikul}")
async def subscribe(artikul: str) -> None:
    """
    Добавляет артикул в таблицу подписок.
    """
    db = SessionLocal()
    try:
        subscription = db.query(Subscription).filter_by(artikul=artikul).first()
        if subscription:
            return {"message": f"Артикул {artikul} уже был добавлен в подписку ранее"}

        subscription = Subscription(artikul=artikul)
        db.add(subscription)
        db.commit()
        return {"message": f"Артикул {artikul} добавлен в подписку"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail=f"Артикул {artikul} уже существует в подписке"
        )
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
