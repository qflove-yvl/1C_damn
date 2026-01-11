from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram import ReplyKeyboardMarkup
import aiohttp

TOKEN = "8279684714:AAFW2cIyug91fE6kArn9GsC55M0tASyu6Mg"
API = "http://127.0.0.1:8000"

# ---------- КНОПКИ ----------
def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📨 Новая заявка"],
            ["📋 Мои заявки", "ℹ️ О сервисе"]
        ],
        resize_keyboard=True
    )

# ---------- ТЕКСТ О СЕРВИСЕ ----------
SERVICE_TEXT = (
    "🛠 *Сервис заявок*\n\n"
    "👨‍💼 Менеджер: @manager_username\n"
    "⏰ Работаем ежедневно\n"
    "📞 Поддержка 24/7"
)

# ---------- START ----------
async def start(update, context):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Нажмите «📨 Новая заявка» и опишите проблему.",
        reply_markup=main_keyboard()
    )

# ---------- ОБРАБОТКА СООБЩЕНИЙ ----------
async def handle_message(update, context):
    text = update.message.text

    # 🔘 КНОПКИ (НЕ ЗАЯВКИ)
    if text == "📨 Новая заявка":
        await update.message.reply_text(
            "✍️ Напишите текст заявки одним сообщением."
        )
        await update.message.reply_text(
            "✅ Заявка принята!\n\n"
            "📌 Менеджер скоро свяжется с вами.\n"
            "⏳ Среднее время ответа — 15 минут."
        )

        context.user_data["waiting_order"] = True
        return


    if text == "📋 Мои заявки":
        user = update.message.from_user

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API}/my-orders/{user.id}") as resp:
                orders = await resp.json()

        if not orders:
            await update.message.reply_text("📭 У вас пока нет заявок.")
            return

        msg = "📦 *Ваши заявки:*\n\n"
        for o in orders[:5]:
            msg += f"№{o['id']} — {o['status']}\n{o['text']}\n\n"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if text == "ℹ️ О сервисе":
        await update.message.reply_text(
            SERVICE_TEXT,
            parse_mode="Markdown"
        )
        return

    # ❌ ЕСЛИ НЕ ЖДЁМ ЗАЯВКУ — ИГНОР
    if not context.user_data.get("waiting_order"):
        await update.message.reply_text(
            "ℹ️ Нажмите «📨 Новая заявка», чтобы создать заявку."
        )
        return

    # ✅ СОЗДАНИЕ ЗАЯВКИ
    user = update.message.from_user

    payload = {
        "client_name": user.full_name,
        "client_username": user.username or "—",
        "client_chat_id": str(user.id),
        "text": text,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API}/orders", json=payload) as resp:
            data = await resp.json()

    context.user_data["waiting_order"] = False

    await update.message.reply_text(
        f"✅ Заявка принята!\n"
        f"📦 Номер: {data['id']}",
        reply_markup=main_keyboard()
    )

# ---------- ЗАПУСК ----------
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Client bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
