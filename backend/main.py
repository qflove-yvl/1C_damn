from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from backend.database import SessionLocal, engine
from backend.models import Base, Order

from openpyxl import Workbook
import requests

# ================== APP ==================

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="SUPER_SECRET_KEY_123"
)

app.mount("/static", StaticFiles(directory="backend/static"), name="static")
templates = Jinja2Templates(directory="backend/templates")

CLIENT_BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

Base.metadata.create_all(bind=engine)

# ================== HELPERS ==================

def admin_required(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(status_code=401)

# ================== AUTH ==================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == "ilaz17" and password == "Ilaz_2008":
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

# ================== WEB PANEL ==================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    admin_required(request)
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


# ================== API ==================

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
    order = Order(**data.dict(), status="Новый")
    db.add(order)
    db.commit()
    db.refresh(order)
    db.close()

    # автоответ клиенту
    requests.post(
        f"https://api.telegram.org/bot{CLIENT_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": data.client_chat_id,
            "text": (
                f"✅ Заявка №{order.id} принята!\n\n"
                "📌 Статус: Новый\n"
                "⏳ Менеджер скоро ответит"
            )
        }
    )

    return {"id": order.id}

@app.get("/orders")
def get_orders(status: str | None = None, chat_id: str | None = None):
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
        raise HTTPException(404)

    order.status = data.status
    db.commit()

    # уведомление клиенту
    requests.post(
        f"https://api.telegram.org/bot{CLIENT_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": order.client_chat_id,
            "text": f"📦 Заявка №{order.id}\nСтатус: {order.status}"
        }
    )

    # ❗ УДАЛЯЕМ ИЗ БАЗЫ
    if data.status in ["Готово", "Отказ"]:
        db.delete(order)
        db.commit()

    db.close()
    return {"ok": True}

# ================== EXCEL ==================

@app.get("/excel")
def excel():
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
            getattr(o, "created_at", "")
        ])

    path = "orders.xlsx"
    wb.save(path)
    return FileResponse(path)
