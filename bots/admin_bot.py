import aiohttp
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import io

TOKEN = "8509144850:AAGzSWbu5d2w7Vr3hWUMrEZ9ZCie8SIr1qA"
API = "http://127.0.0.1:8000"

ADMIN_IDS = [1123838913]

STATUSES = ["Новый", "В работе", "Готово", "Отказ"]


def is_admin(update: Update):
    return update.effective_user.id in ADMIN_IDS


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📋 Заявки", "📊 Excel"],
            ["🌐 Веб панель"],
            ["🆕 Новый", "⚙ В работе", "✅ Готово", "❌ Отказ"]
        ],
        resize_keyboard=True
    )



def order_keyboard(index, total, order_id):
    buttons = []

    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅", callback_data=f"nav:{index-1}"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("➡", callback_data=f"nav:{index+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("⚙ В работе", callback_data=f"status:{order_id}:В работе"),
        InlineKeyboardButton("✅ Готово", callback_data=f"status:{order_id}:Готово")
    ])
    buttons.append([
        InlineKeyboardButton("❌ Отказ", callback_data=f"status:{order_id}:Отказ")
    ])

    return InlineKeyboardMarkup(buttons)


async def fetch_orders(status=None):
    async with aiohttp.ClientSession() as s:
        url = f"{API}/orders"
        if status:
            url += f"?status={status}"
        async with s.get(url) as r:
            return await r.json()


async def render(message, index, status=None):
    orders = await fetch_orders(status)
    if not orders:
        await message.edit_text("❌ Заявок нет")
        return

    index = max(0, min(index, len(orders) - 1))
    o = orders[index]

    text = (
        f"📦 {index+1}/{len(orders)}\n\n"
        f"🆔 #{o['id']}\n"
        f"👤 {o['client_name']} (@{o['client_username']})\n\n"
        f"📝 {o['text']}\n\n"
        f"📌 Статус: {o['status']}"
    )

    await message.edit_text(
        text,
        reply_markup=order_keyboard(index, len(orders), o["id"])
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        "🛠 Админ-панель",
        reply_markup=main_keyboard()
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    text = update.message.text
    context.user_data["status"] = None

    if text == "📋 Заявки":
        msg = await update.message.reply_text("⏳")
        await render(msg, 0)
        return

    if text in ["🆕 Новый", "⚙ В работе", "✅ Готово", "❌ Отказ"]:
        status = text.split()[-1]
        context.user_data["status"] = status
        msg = await update.message.reply_text("⏳")
        await render(msg, 0, status)
        return

    if text == "🌐 Веб панель":
        await update.message.reply_text(
            "🌐 Админ-панель:\nhttp://127.0.0.1:8000/dashboard"
        )
        return

    if text == "📊 Excel":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{API}/excel") as r:
                data = await r.read()

        f = io.BytesIO(data)
        f.name = "orders.xlsx"
        await update.message.reply_document(InputFile(f))
        return


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return

    q = update.callback_query
    await q.answer()

    data = q.data.split(":")
    status_filter = context.user_data.get("status")

    if data[0] == "nav":
        await render(q.message, int(data[1]), status_filter)

    if data[0] == "status":
        _, order_id, new_status = data
        async with aiohttp.ClientSession() as s:
            await s.post(
                f"{API}/status",
                json={"id": int(order_id), "status": new_status}
            )

        await q.answer("✅ Статус обновлён")
        await render(q.message, 0, status_filter)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(callback))
    print("Admin bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
