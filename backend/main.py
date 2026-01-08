from fastapi import FastAPI
from pydantic import BaseModel
from backend.database import SessionLocal, engine
from backend.models import Base, Order
import requests

BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Universal CRM API")


class OrderCreate(BaseModel):
    client_name: str
    client_username: str
    client_chat_id: str
    text: str


class StatusUpdate(BaseModel):
    id: int
    status: str


@app.post("/orders")
def create_order(order: OrderCreate):
    db = SessionLocal()

    o = Order(
        client_name=order.client_name,
        client_username=order.client_username,
        client_chat_id=order.client_chat_id,
        text=order.text,
        status="Новый"
    )

    db.add(o)
    db.commit()
    db.refresh(o)
    db.close()

    return {"id": o.id}


@app.get("/orders")
def get_orders():
    db = SessionLocal()
    orders = db.query(Order).all()
    db.close()
    return [
        {
            "id": o.id,
            "client": o.client,
            "text": o.text,
            "status": o.status
        } for o in orders
    ]


@app.post("/status")
def update_status(data: StatusUpdate):
    db = SessionLocal()

    order = db.query(Order).get(data.id)
    order.status = data.status
    db.commit()
    db.refresh(order)

    # 👉 УВЕДОМЛЕНИЕ В TELEGRAM КЛИЕНТУ
    if order.client_chat_id:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": order.client_chat_id,
                "text": f"📦 Ваш заказ №{order.id}\nСтатус: {data.status}"
            }
        )

    db.close()
    return {"ok": True}