import requests
import pandas as pd
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler


TOKEN = "8509144850:AAGzSWbu5d2w7Vr3hWUMrEZ9ZCie8SIr1qA"
API = "http://127.0.0.1:8000"

keyboard = ReplyKeyboardMarkup(
    [["📋 Заявки", "📄 Excel"]],
    resize_keyboard=True
)


async def start(update, context):
    await update.message.reply_text(
        "👨‍💼 CRM админ-панель",
        reply_markup=keyboard
    )


async def show_orders(update, context):
    data = requests.get(f"{API}/orders").json()

    for o in data:
        text = (
            f"🆔 {o['id']}\n"
            f"👤 {o['client_name']} (@{o['client_username']})\n"
            f"💬 {o['text']}\n"
            f"📌 {o['status']}"
        )

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🛠 В работу", callback_data=f"work_{o['id']}"),
                InlineKeyboardButton("✅ Готово", callback_data=f"done_{o['id']}")
            ]
        ])

        await update.message.reply_text(text, reply_markup=kb)

async def export_excel(update, context):
    data = requests.get(f"{API}/orders").json()

    if not data:
        await update.message.reply_text("Нет данных")
        return

    df = pd.DataFrame(data)
    df.to_excel("orders.xlsx", index=False)

    await update.message.reply_document(open("orders.xlsx", "rb"))


async def handle_buttons(update, context):
    query = update.callback_query
    await query.answer()

    action, order_id = query.data.split("_")

    status = "В работе" if action == "work" else "Готов"

    requests.post(f"{API}/status", json={
        "id": int(order_id),
        "status": status
    })

    await query.edit_message_text(f"Статус заказа {order_id}: {status}")


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("📋"), show_orders))
app.add_handler(MessageHandler(filters.Regex("📄"), export_excel))

print("Admin bot started")
app.run_polling()
app.add_handler(CallbackQueryHandler(handle_buttons))