import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ===== STORAGE =====
gift_codes = set()
used_codes = set()
free_users = set()

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔮 قراءة فنجان - 5$", callback_data="fanjan")],
        [InlineKeyboardButton("🌙 تفسير حلم - 4$", callback_data="dream")],
        [InlineKeyboardButton("💬 استشارة - 7$", callback_data="consult")],
        [InlineKeyboardButton("🎁 كود هدية", callback_data="gift")]
    ]

    await update.message.reply_text(
        "✨ أهلاً بك في العالم الآخر 🔮\nاختر الخدمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== BUTTON =====
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "gift":
        context.user_data["gift_mode"] = True
        await query.message.reply_text("🎁 أرسل كود الهدية الآن:")
        return

    if user_id in free_users:
        free_users.remove(user_id)
        await query.message.reply_text("🎉 لديك خدمة مجانية واحدة! اكتب طلبك 🔮")
        return

    await query.message.reply_text(
        "💳 الدفع مطلوب:\n\n"
        "USDT BEP20:\n"
        "0x9Cd3FeB3D8BA5da497d7D09084aB5AcC9309a535\n\n"
        "أو شام كاش 📩"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 طلب جديد من {user_id}"
    )

# ===== MESSAGE HANDLER =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # ===== DEBUG (مهم) =====
    print("MESSAGE RECEIVED:", text)

    # ===== GIFT MODE =====
    if context.user_data.get("gift_mode") == True:
        context.user_data["gift_mode"] = False

        print("GIFT CODE RECEIVED:", text)

        if text in used_codes:
            await update.message.reply_text("❌ الكود مستخدم مسبقاً")
            return

        if text in gift_codes:
            gift_codes.remove(text)
            used_codes.add(text)
            free_users.add(user_id)

            await update.message.reply_text("🎉 تم قبول كود الهدية!")
        else:
            await update.message.reply_text("❌ كود غير صحيح")

        return

    # ===== ADMIN =====
    if user_id == ADMIN_ID:

        if text.startswith("code "):
            code = text.replace("code ", "").strip()
            gift_codes.add(code)
            await update.message.reply_text(f"🎁 تم إنشاء كود: {code}")
            return

        parts = text.split("|")
        if len(parts) == 2:
            target = int(parts[0])
            msg = parts[1]
            await context.bot.send_message(chat_id=target, text=f"🔮 {msg}")
        return

    # ===== NORMAL USERS =====
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🧠 طلب:\n{text}"
    )

    await update.message.reply_text("⏳ تم الاستلام 🔮")

# ===== APP =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
