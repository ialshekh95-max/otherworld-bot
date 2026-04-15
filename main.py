import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔮 قراءة فنجان - 5$", callback_data="fanjan")],
        [InlineKeyboardButton("🌙 تفسير حلم - 4$", callback_data="dream")],
        [InlineKeyboardButton("💬 استشارة - 7$", callback_data="consult")]
    ]

    await update.message.reply_text(
        "✨ أهلاً بك في العالم الآخر 🔮\nاختر الخدمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "💳 الدفع:\n\nUSDT BEP20:\n0x9Cd3FeB3D8BA5da497d7D09084aB5AcC9309a535\n\nأو شام كاش 📩"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 طلب جديد من المستخدم: {query.from_user.id}"
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id == ADMIN_ID:
        parts = text.split("|")
        if len(parts) == 2:
            target = int(parts[0])
            msg = parts[1]
            await context.bot.send_message(chat_id=target, text=msg)
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🧠 رسالة جديدة:\n{text}"
        )
        await update.message.reply_text("⏳ تم الاستلام 🔮")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
