from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from openpyxl import Workbook
from datetime import datetime
import requests

from backend.database import SessionLocal, engine
from backend.models import Base, Order

# ================== НАСТРОЙКИ ==================

ADMIN_LOGIN = "ilaz17"
ADMIN_PASSWORD = "Ilaz_2008"
CLIENT_BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

# ==============================================

app = FastAPI()

# 🔐 Сессии (НЕ ТРОГАТЬ)
app.add_middleware(
    SessionMiddleware,
    secret_key="ULTRA_SUPER_SECRET_KEY_123",
    max_age=60 * 60 * 24
)

# 📁 Статика и шаблоны
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

# 🗄️ База
Base.metadata.create_all(bind=engine)

# ================== УТИЛИТЫ ==================

def admin_required(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/login", status_code=302)


# ================== АВТОРИЗАЦИЯ ==================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request,
          username: str = Form(...),
          password: str = Form(...)):
    if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse("/dashboard", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Неверный логин или пароль"}
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# ================== ВЕБ-ПАНЕЛЬ ==================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse("dashboard.html", {"request": request})



@app.get("/panel/orders", response_class=HTMLResponse)
def panel_orders(request: Request):
    admin_required(request)
    db = SessionLocal()
    orders = db.query(Order).order_by(Order.id.desc()).all()
    db.close()
    return templates.TemplateResponse(
        "orders.html",
        {"request": request, "orders": orders}
    )

# ================== API ЗАЯВОК ==================

class OrderCreate(BaseModel):
    client_name: str
    client_username: str
    client_chat_id: str
    text: str


class StatusUpdate(BaseModel):
    id: int
    status: str


@app.post("/orders")
def create_order(data: OrderCreate):
    db = SessionLocal()
    order = Order(
        client_name=data.client_name,
        client_username=data.client_username,
        client_chat_id=data.client_chat_id,
        text=data.text,
        status="Новый",
        created_at=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    db.close()
    return {"id": order.id}


@app.get("/orders")
def get_orders(status: str | None = None,
               chat_id: str | None = None):
    db = SessionLocal()
    q = db.query(Order)

    if status:
        q = q.filter(Order.status == status)
    if chat_id:
        q = q.filter(Order.client_chat_id == chat_id)

    orders = q.order_by(Order.id.desc()).all()
    db.close()
    return orders


@app.post("/status")
def update_status(data: StatusUpdate):
    db = SessionLocal()
    order = db.get(Order, data.id)
    if not order:
        db.close()
        raise HTTPException(404)

    order.status = data.status
    db.commit()

    # 📬 Уведомление клиенту
    requests.post(
        f"https://api.telegram.org/bot{CLIENT_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": order.client_chat_id,
            "parse_mode": "HTML",
            "text": (
                f"📦 <b>Заявка №{order.id}</b>\n"
                f"🕒 <i>{order.created_at.strftime('%d.%m.%Y %H:%M')}</i>\n\n"
                f"📝 <b>Текст заявки:</b>\n"
                f"{order.text}\n\n"
                f"📌 <b>Новый статус:</b> <u>{order.status}</u>\n\n"
                f"👨‍💼 Менеджер: @cestlavieq"
            )
        }
    )

    # ❌ Удаляем из БД если финальный статус
    if data.status in ["Готово", "Отказ"]:
        db.delete(order)
        db.commit()

    db.close()
    return {"ok": True}

# ================== EXCEL ==================

@app.get("/excel")
def export_excel():
    db = SessionLocal()
    orders = db.query(Order).all()
    db.close()

    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "Имя", "Username", "Текст", "Статус", "Дата"])

    for o in orders:
        ws.append([
            o.id,
            o.client_name,
            o.client_username,
            o.text,
            o.status,
            o.created_at.strftime("%d.%m.%Y %H:%M")
        ])

    path = "orders.xlsx"
    wb.save(path)
    return FileResponse(path)
