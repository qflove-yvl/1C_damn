from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import ReplyKeyboardMarkup
import aiohttp

TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"
API = "http://127.0.0.1:8000"

KEYBOARD = ReplyKeyboardMarkup(
    [["📨 Новая заявка"], ["📋 Мои заявки", "ℹ️ О сервисе"]],
    resize_keyboard=True
)

SERVICE_TEXT = (
    "🛠 Сервис заявок\n\n"
    "👨‍💼 Менеджер: @cestlavieq\n"
    "⏰ 24/7"
)

async def start(update, context):
    await update.message.reply_text("Добро пожаловать!", reply_markup=KEYBOARD)

async def handle(update, context):
    text = update.message.text
    user = update.message.from_user

    if text == "📋 Мои заявки":
        user = update.message.from_user
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API}/orders?chat_id={user.id}") as resp:
                orders = await resp.json()

        if not orders:
            await update.message.reply_text("📭 У вас пока нет заявок")
            return

        msg = "📦 *Ваши заявки:*\n\n"
        for o in orders:
            msg += (
                f"🆔 #{o['id']}\n"
                f"📌 Статус: {o['status']}\n"
                f"📝 {o['text']}\n\n"
            )

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text == "ℹ️ О сервисе":
        await update.message.reply_text(SERVICE_TEXT)
        return

    if text == "📨 Новая заявка":
        await update.message.reply_text("Напишите текст заявки одним сообщением!")
        return

    payload = {
        "client_name": user.full_name,
        "client_username": user.username or "-",
        "client_chat_id": str(user.id),
        "text": text
    }

    async with aiohttp.ClientSession() as s:
        async with s.post(f"{API}/orders", json=payload) as r:
            data = await r.json()

    await update.message.reply_text(f"✅ Заявка №{data['id']} создана")



app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()
