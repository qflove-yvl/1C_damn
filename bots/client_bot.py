import requests
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"
API = "http://127.0.0.1:8000"


async def start(update, context):
    await update.message.reply_text("👋 Напишите вашу заявку одним сообщением.")


async def handle_message(update, context):
    user = update.message.from_user

    payload = {
        "client_name": user.full_name,
        "client_username": user.username or "—",
        "client_chat_id": str(user.id),
        "text": update.message.text
    }

    r = requests.post(f"{API}/orders", json=payload)

    await update.message.reply_text(
        f"✅ Ваша заявка принята!\nНомер: {r.json()['id']}"
    )

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Client bot started")
app.run_polling()