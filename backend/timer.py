import time
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models import Order
import requests

BOT_TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"

while True:
    db = SessionLocal()
    limit = datetime.utcnow() - timedelta(minutes=30)

    orders = db.query(Order).filter(
        Order.status == "Новый",
        Order.created_at < limit
    ).all()

    for o in orders:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": o.client_chat_id,
                "text": f"⏰ Ваша заявка №{o.id} ещё в очереди"
            }
        )

    db.close()
    time.sleep(300)
