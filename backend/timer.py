import time
from datetime import datetime, timedelta
import requests
from backend.database import SessionLocal
from backend.models import Order

BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

while True:
    db = SessionLocal()
    limit = datetime.utcnow() - timedelta(minutes=15)

    orders = db.query(Order).filter(
        Order.status == "Новый",
        Order.created_at < limit
    ).all()

    for o in orders:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": o.client_chat_id,
                "text": f"⏳ Ваша заявка №{o.id} всё ещё в обработке."
            }
        )

    db.close()
    time.sleep(300)
