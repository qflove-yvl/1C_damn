import aiohttp
import io
import requests

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= НАСТРОЙКИ =================

TOKEN = "8509144850:AAGzSWbu5d2w7Vr3hWUMrEZ9ZCie8SIr1qA"
API = "http://127.0.0.1:8000"

ADMIN_IDS = [1123838913]  # ← ТВОЙ TG ID

# ============================================


def admin_only(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📋 Заявки", "📊 Excel"],
            ["🆕 Новый", "⚙ В работе", "✅ Готово", "❌ Отказ"],
        ],
        resize_keyboard=True,
    )


def order_keyboard(index: int, total: int, order_id: int):
    buttons = []

    nav = []
    if index > 0:
        nav.append(
            InlineKeyboardButton("⬅️", callback_data=f"nav:{index-1}")
        )
    if index < total - 1:
        nav.append(
            InlineKeyboardButton("➡️", callback_data=f"nav:{index+1}")
        )

    if nav:
        buttons.append(nav)

    buttons.append(
        [
            InlineKeyboardButton(
                "🟡 В работе", callback_data=f"status:{order_id}:in_progress"
            ),
            InlineKeyboardButton(
                "✅ Готово", callback_data=f"status:{order_id}:done"
            ),
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                "❌ Отказ", callback_data=f"status:{order_id}:rejected"
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


async def fetch_orders(status=None):
    url = f"{API}/orders"
    if status:
        url += f"?status={status}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return await r.json()


async def render(message, index: int, status=None):
    orders = await fetch_orders(status)

    if not orders:
        await message.edit_text("❌ Заявок нет")
        return

    index = max(0, min(index, len(orders) - 1))
    o = orders[index]

    text = (
        f"📦 Заявка {index+1}/{len(orders)}\n\n"
        f"🆔 {o['id']}\n"
        f"👤 {o['client_name']} (@{o['client_username']})\n\n"
        f"📝 {o['text']}\n\n"
        f"📌 Статус: {o['status']}"
    )

    await message.edit_text(
        text,
        reply_markup=order_keyboard(index, len(orders), o["id"]),
    )


# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return
    await update.message.reply_text(
        "🛠 Админ-панель",
        reply_markup=main_keyboard(),
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return

    text = update.message.text
    context.user_data["status"] = None

    if text == "📋 Заявки":
        msg = await update.message.reply_text("⏳")
        await render(msg, 0)

    elif text in ["🆕 Новый", "⚙ В работе", "✅ Готово", "❌ Отказ"]:
        status = text.split()[-1]
        context.user_data["status"] = status
        msg = await update.message.reply_text("⏳")
        await render(msg, 0, status)

    elif text == "📊 Excel":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{API}/excel") as r:
                data = await r.read()

        file = io.BytesIO(data)
        file.name = "orders.xlsx"
        await update.message.reply_document(InputFile(file))


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin_only(update):
        return

    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    status_filter = context.user_data.get("status")

    if data[0] == "nav":
        await render(query.message, int(data[1]), status_filter)

    elif data[0] == "status":
        _, order_id, status = data

        r = requests.post(
            f"{API}/orders/{order_id}/status",
            json={"status": status},
        )

        if r.status_code != 200:
            await query.answer("Ошибка")
            return

        await query.answer("Статус обновлён")
        await render(query.message, 0, status_filter)


# ================== MAIN ==================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("✅ Admin bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
