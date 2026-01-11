from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from backend.database import SessionLocal, engine
from backend.models import Base, Order, Admin
from openpyxl import Workbook
from tempfile import NamedTemporaryFile
import requests

CLIENT_BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CRM CORE")


# ---------- SCHEMAS ----------
class OrderCreate(BaseModel):
    client_name: str
    client_username: str
    client_chat_id: str
    text: str


class StatusUpdate(BaseModel):
    id: int
    status: str


# ---------- INIT ADMIN (ОДИН РАЗ) ----------
@app.on_event("startup")
def create_admin():
    db = SessionLocal()
    if not db.query(Admin).first():
        db.add(Admin(username="admin", password="1234"))
        db.commit()
    db.close()


# ---------- ORDERS ----------
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
    orders = db.query(Order).order_by(Order.id.desc()).all()
    db.close()
    return [
        {
            "id": o.id,
            "client_name": o.client_name,
            "client_username": o.client_username,
            "text": o.text,
            "status": o.status
        }
        for o in orders
    ]


@app.post("/status")
def update_status(data: StatusUpdate):
    db = SessionLocal()
    order = db.get(Order, data.id)
    if not order:
        raise HTTPException(404, "Order not found")

    order.status = data.status
    db.commit()
    db.close()
    return {"ok": True}

@app.post("/orders/{order_id}/status")
def set_order_status(order_id: int, data: StatusUpdate):
    db = SessionLocal()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")

    order.status = data.status
    db.commit()
    db.refresh(order)

    # уведомление клиенту
    requests.post(
        f"https://api.telegram.org/bot{CLIENT_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": order.client_chat_id,
            "text": (
                f"📦 Ваша заявка №{order.id}\n"
                f"Новый статус: {order.status}"
            )
        }
    )

    db.close()
    return {
        "id": order.id,
        "status": order.status,
        "client_username": order.client_username,
        "text": order.text
    }


# ---------- EXCEL ----------
@app.get("/excel")
def export_excel():
    db = SessionLocal()
    orders = db.query(Order).all()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "Имя", "Username", "Текст", "Статус"])

    for o in orders:
        ws.append([o.id, o.client_name, o.client_username, o.text, o.status])

    tmp = NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)

    return FileResponse(tmp.name, filename="orders.xlsx")

@app.get("/my-orders/{chat_id}")
def my_orders(chat_id: str):
    db = SessionLocal()
    orders = (
        db.query(Order)
        .filter(Order.client_chat_id == chat_id)
        .order_by(Order.id.desc())
        .all()
    )
    db.close()

    return [
        {
            "id": o.id,
            "text": o.text,
            "status": o.status
        }
        for o in orders
    ]


# ---------- WEB ----------
@app.get("/", response_class=HTMLResponse)
def admin_panel():
    return open("backend/admin.html", encoding="utf-8").read()
