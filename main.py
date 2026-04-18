import os
import json
import time
import random
import aiohttp
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== AI RESPONSE ENGINE =====

FANJAN_SYMBOLS = [
    ("طائر يحلق", "سفر أو خبر من بعيد"),
    ("نجمة لامعة", "توفيق وفرصة ذهبية"),
    ("طريق طويل", "مرحلة جديدة تبدأ قريباً"),
    ("شجرة متجذرة", "استقرار واطمئنان في حياتك"),
    ("قمر منير", "وضوح وانكشاف أمر كان غامضاً"),
    ("بحر هادئ", "سلام داخلي وراحة تقترب"),
    ("جبل شامخ", "عقبة ستتجاوزها بقوة"),
    ("زهرة تتفتح", "بداية جديدة في علاقة أو مشروع"),
    ("مفتاح", "باب موصد سيُفتح لك قريباً"),
    ("نهر جارٍ", "تدفق الرزق والخير في طريقك"),
    ("شمس مشرقة", "انتهاء مرحلة صعبة وبداية مضيئة"),
    ("سمكة", "رزق وفير يقترب منك"),
]

FANJAN_ENDINGS = [
    "الفنجان لا يكذب، استعد لما هو قادم 🔮",
    "هذا ما تخبرنا به البقايا في فنجانك ✨",
    "الطاقة حولك إيجابية، ثق بنفسك 🌙",
    "الأيام القادمة ستحمل لك إجابات كثيرة 💫",
    "احتفظ بهذه الرسالة، ستتذكرها لاحقاً 🔮",
]

DREAM_SYMBOLS = {
    "ماء": "الماء في الأحلام يرمز إلى المشاعر والتحولات الداخلية",
    "طيران": "الطيران يدل على الحرية والرغبة في التخلص من قيد ما",
    "موت": "الموت في الحلم لا يعني الوفاة، بل نهاية مرحلة وبداية جديدة",
    "أسنان": "الأسنان ترمز إلى القوة والثقة بالنفس أو الخوف من الخسارة",
    "بيت": "البيت يمثل ذاتك الداخلية وحالتك النفسية",
    "مطر": "المطر يبشر بالرحمة والرزق والتجديد",
    "نار": "النار تمثل الطاقة والتحول، وقد تكون إشارة لانفعالات مكبوتة",
    "حيوان": "الحيوانات في الأحلام ترمز لغرائزك وطاقتك الداخلية",
    "طفل": "الطفل يرمز للبراءة أو بداية جديدة أو جانب من شخصيتك",
    "مشي": "المشي يدل على مسيرة حياتك ووتيرة تقدمك",
}

DREAM_INTROS = [
    "🌙 تفسير حلمك:",
    "✨ ما رأيته له دلالة عميقة:",
    "🔮 الأحلام لغة الروح، وهذا ما يقوله حلمك:",
    "🌌 رسالة من عالم الأحلام:",
]

DREAM_ENDINGS = [
    "تذكر أن الأحلام مرآة روحك، وهذا التفسير هو بوصلتك 🌙",
    "الحلم الذي يتكرر هو رسالة لم تُفهم بعد، فكّر فيها 💫",
    "الروح تتكلم في النوم بما يعجز عنه اللسان في اليقظة ✨",
    "هذا التفسير مبني على علم الأحلام وطاقة رسالتك 🔮",
]

GENERAL_INTROS = [
    "✨ أحسست بطاقتك وهذا ما تقوله:",
    "🔮 بعد التأمل في رسالتك:",
    "💫 الكون يرسل لك هذه الإشارة:",
    "🌙 انتبه لهذه الرسالة المهمة:",
]

GENERAL_RESPONSES = [
    "هناك تحوّل قادم في حياتك، والصبر هو مفتاحك الآن",
    "طاقتك قوية لكنها بحاجة لتوجيه، ركّز على هدف واحد",
    "شخص قريب منك يؤثر في مسارك، انتبه لمن تثق",
    "فرصة ستطرق بابك قريباً، لا تتركها تمر دون اهتمام",
    "الجواب الذي تبحث عنه موجود داخلك، هدّئ عقلك واستمع",
    "مرحلة التعب على وشك الانتهاء، النور قريب",
    "قرار تفكر فيه الآن هو الصحيح، ثق بحدسك",
    "الكون يرتّب لك أشياء خلف الكواليس، استمر",
]

GENERAL_ENDINGS = [
    "الكون لا يرسل رسائل بلا سبب 🌌",
    "ثق بالتوقيت حتى لو لم يبدُ مناسباً الآن ✨",
    "الطاقة لا تكذب، ما شعرت به حقيقي 🔮",
    "استمع لهذه الإشارة جيداً 💫",
]


def generate_fanjan_response(text: str) -> str:
    symbol, meaning = random.choice(FANJAN_SYMBOLS)
    extra_symbol, extra_meaning = random.choice(
        [s for s in FANJAN_SYMBOLS if s[0] != symbol]
    )
    ending = random.choice(FANJAN_ENDINGS)

    opening_options = [
        f"🔮 فنجانك يكشف لي صورة واضحة...\n\nأرى *{symbol}* — وهذا يدل على {meaning}.",
        f"🔮 تأملت في فنجانك بعمق...\n\nظهر لي *{symbol}*، وهو يُشير إلى {meaning}.",
        f"🔮 بقايا فنجانك تحكي قصة...\n\n*{symbol}* يبرز بوضوح، ومعناه {meaning}.",
    ]

    return (
        random.choice(opening_options)
        + f"\n\nوفي الجهة الأخرى أرى *{extra_symbol}*، وهذا يعني {extra_meaning}."
        + f"\n\n{ending}"
    )


def generate_dream_response(text: str) -> str:
    text_lower = text.lower()
    matched_symbol = None
    matched_meaning = None

    for keyword, meaning in DREAM_SYMBOLS.items():
        if keyword in text_lower:
            matched_symbol = keyword
            matched_meaning = meaning
            break

    intro = random.choice(DREAM_INTROS)
    ending = random.choice(DREAM_ENDINGS)

    if matched_symbol:
        core = (
            f"ذكرت *{matched_symbol}* في حلمك، و{matched_meaning}.\n\n"
            + random.choice([
                "هذا الحلم يعكس حالة داخلية تمر بها الآن، والرسالة واضحة: لا تتجاهل مشاعرك.",
                "ما رأيته ليس مجرد صور عشوائية، بل انعكاس لما تعيشه في أعماقك.",
                "روحك تحاول التواصل معك من خلال هذا الرمز، استمع لها.",
            ])
        )
    else:
        elements = random.sample(list(DREAM_SYMBOLS.items()), 2)
        core = (
            f"حلمك يحمل طبقات متعددة من المعنى.\n\n"
            f"الجانب الأول يشير إلى {elements[0][1]}.\n"
            f"والجانب الثاني يلمح إلى {elements[1][1]}.\n\n"
            "هذان البُعدان معاً يرسمان صورة دقيقة لما تمر به."
        )

    return f"{intro}\n\n{core}\n\n{ending}"


def generate_general_response(text: str) -> str:
    intro = random.choice(GENERAL_INTROS)
    body = random.choice(GENERAL_RESPONSES)
    ending = random.choice(GENERAL_ENDINGS)
    return f"{intro}\n\n{body}.\n\n{ending}"



# ===== PAYMENT CONFIG =====
USDT_WALLET   = "0x9Cd3FeB3D8BA5da497d7D09084aB5AcC9309a535"
SHAMCASH_CODE = "29c94bfb247e745ec50dffd528706f36"
FALLBACK_RATE = 14000        # ليرة سورية لكل دولار (احتياطي)
PRICES_USD    = {"fanjan": 5, "dream": 4, "consult": 7}

current_rate: float = FALLBACK_RATE

def syp(usd: int) -> str:
    return f"{int(usd * current_rate):,}"

def fmt_price(service: str) -> str:
    usd = PRICES_USD[service]
    return f"💵 {usd}$ | 🇸🇾 {syp(usd)} ل.س"

async def rate_updater_job(context) -> None:
    pass   # السعر يُضبط يدوياً عبر /setrate أو يبقى الاحتياطي

# ===== ANTI-SPAM =====
RATE_LIMIT_MESSAGES = 5
RATE_LIMIT_WINDOW  = 60

user_message_times = defaultdict(list)

def is_rate_limited(user_id: int) -> bool:
    now = time.time()
    timestamps = user_message_times[user_id]
    timestamps[:] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MESSAGES:
        return True
    timestamps.append(now)
    return False

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ===== PERSISTENCE =====
DATA_FILE = "data.json"

def load_data():
    global gift_codes, used_codes, free_users, all_users, banned_users
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        gift_codes   = set(data.get("gift_codes", []))
        used_codes   = set(data.get("used_codes", []))
        free_users   = set(data.get("free_users", []))
        all_users    = set(data.get("all_users", []))
        banned_users = set(data.get("banned_users", []))
    else:
        gift_codes   = set()
        used_codes   = set()
        free_users   = set()
        all_users    = set()
        banned_users = set()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "gift_codes":   list(gift_codes),
            "used_codes":   list(used_codes),
            "free_users":   list(free_users),
            "all_users":    list(all_users),
            "banned_users": list(banned_users),
        }, f)

load_data()

# ===== STORAGE (loaded from file above) =====

# ===== HELPERS =====
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔮 قراءة فنجان  {fmt_price('fanjan')}", callback_data="fanjan")],
        [InlineKeyboardButton(f"🌙 تفسير حلم  {fmt_price('dream')}",    callback_data="dream")],
        [InlineKeyboardButton(f"💬 استشارة  {fmt_price('consult')}",     callback_data="consult")],
    ])

def payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 محفظة إلكترونية (USDT)", callback_data="pay_wallet")],
        [InlineKeyboardButton("💵 شام كاش",                 callback_data="pay_shamcash")],
        [InlineKeyboardButton("🎁 كود هدية",                callback_data="pay_gift")],
    ])

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id in banned_users:
        await update.message.reply_text("🚫 تم حظرك من استخدام هذا البوت.")
        return

    # مسح أي حالة نشطة عند العودة للقائمة الرئيسية
    context.user_data.clear()

    is_new = user.id not in all_users
    all_users.add(user.id)
    save_data()

    if is_new:
        name     = user.full_name or "بدون اسم"
        username = f"@{user.username}" if user.username else "بدون يوزرنيم"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🆕 مستخدم جديد!\n\n"
                f"👤 الاسم: {name}\n"
                f"🔗 يوزرنيم: {username}\n"
                f"🆔 المعرف: {user.id}\n"
                f"👥 إجمالي المستخدمين: {len(all_users)}"
            )
        )

    await update.message.reply_text(
        "✨ أهلاً بك في العالم الآخر 🔮\n\n"
        "اختر الخدمة التي تريدها:",
        reply_markup=main_menu_keyboard()
    )

# ===== BUTTONS =====
SERVICE_NAMES = {
    "fanjan": "قراءة فنجان 🔮",
    "dream":  "تفسير حلم 🌙",
    "consult": "استشارة 💬",
}

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # ── Service selected ──────────────────────────────
    if query.data in SERVICE_NAMES:
        svc_key = query.data
        context.user_data["selected_service"] = svc_key

        # Admin-granted free session: activate state immediately
        if user_id in free_users:
            free_users.remove(user_id)
            save_data()
            context.user_data["state"] = svc_key   # ← تفعيل الحالة
            prompts = {
                "fanjan":  "🎉 جلسة مجانية!\n\n🔮 أرسل وصف فنجانك أو صورة منه:",
                "dream":   "🎉 جلسة مجانية!\n\n🌙 أرسل تفاصيل حلمك وسأفسره لك:",
                "consult": "🎉 جلسة مجانية!\n\n💬 اكتب موضوع استشارتك:",
            }
            await query.message.reply_text(prompts[svc_key])
            return

        # Show payment methods
        usd = PRICES_USD[svc_key]
        await query.message.reply_text(
            f"✅ اخترت: {SERVICE_NAMES[svc_key]}\n\n"
            f"💵 السعر: {usd}$  |  🇸🇾 {syp(usd)} ل.س\n\n"
            "💳 اختر طريقة الدفع:",
            reply_markup=payment_keyboard()
        )
        return

    # ── Payment via USDT wallet ───────────────────────
    if query.data == "pay_wallet":
        svc_key = context.user_data.get("selected_service", "")
        service  = SERVICE_NAMES.get(svc_key, "الخدمة المطلوبة")
        usd      = PRICES_USD.get(svc_key, 0)
        await query.message.reply_text(
            f"💳 الدفع بالمحفظة الإلكترونية لـ {service}:\n\n"
            f"🌐 الشبكة: *BNB BEP20*\n"
            f"📋 العنوان:\n`{USDT_WALLET}`\n\n"
            f"💵 المبلغ: {usd}$  |  🇸🇾 {syp(usd)} ل.س\n\n"
            "بعد التحويل أرسل إيصالاً وسيتم تفعيل خدمتك.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 طلب دفع (محفظة)\n"
                f"👤 المستخدم: {user_id}\n"
                f"🛎 الخدمة: {service}\n"
                f"💵 المبلغ: {usd}$ | 🇸🇾 {syp(usd)} ل.س"
            )
        )
        context.user_data["state"] = "awaiting_receipt"
        context.user_data["pay_service"] = svc_key
        context.user_data["pay_method"] = "wallet"
        return

    # ── Payment via ShaamCash ─────────────────────────
    if query.data == "pay_shamcash":
        svc_key = context.user_data.get("selected_service", "")
        service  = SERVICE_NAMES.get(svc_key, "الخدمة المطلوبة")
        usd      = PRICES_USD.get(svc_key, 0)
        await query.message.reply_text(
            f"💵 الدفع عبر شام كاش لـ {service}:\n\n"
            f"🔑 كود الدفع:\n`{SHAMCASH_CODE}`\n\n"
            f"💵 المبلغ: {usd}$  |  🇸🇾 {syp(usd)} ل.س\n\n"
            "بعد الدفع أرسل إيصالاً وسيتم تفعيل خدمتك.",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 طلب دفع (شام كاش)\n"
                f"👤 المستخدم: {user_id}\n"
                f"🛎 الخدمة: {service}\n"
                f"💵 المبلغ: {usd}$ | 🇸🇾 {syp(usd)} ل.س"
            )
        )
        context.user_data["state"] = "awaiting_receipt"
        context.user_data["pay_service"] = svc_key
        context.user_data["pay_method"] = "shamcash"
        return

    # ── Payment via gift code ─────────────────────────
    if query.data == "pay_gift":
        context.user_data["state"] = "gift_code"
        await query.message.reply_text("🎁 أرسل كود الهدية الآن:")

# ===== STATS =====
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "📊 لوحة الإحصائيات:\n\n"
        f"👥 إجمالي المستخدمين: {len(all_users)}\n"
        f"🎁 أكواد نشطة: {len(gift_codes)}\n"
        f"✅ أكواد مستخدمة: {len(used_codes)}\n"
        f"👤 مستخدمون مجانيون: {len(free_users)}\n\n"
        f"🗝️ الأكواد النشطة:\n" +
        ("\n".join(gift_codes) if gift_codes else "لا توجد أكواد")
    )

# ===== DELCODE =====
async def delcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /delcode <الكود>")
        return

    code = context.args[0].strip()

    if code in gift_codes:
        gift_codes.remove(code)
        save_data()
        await update.message.reply_text(f"🗑️ تم حذف الكود: {code}")
    else:
        await update.message.reply_text(f"❌ الكود غير موجود: {code}")

# ===== ADDUSER =====
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /adduser <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    free_users.add(target_id)
    all_users.add(target_id)
    save_data()

    await update.message.reply_text(f"✅ تم منح جلسة مجانية للمستخدم: {target_id}")

# ===== BAN / UNBAN =====
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /ban <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    if target_id == ADMIN_ID:
        await update.message.reply_text("❌ لا يمكن حظر الأدمن")
        return

    banned_users.add(target_id)
    free_users.discard(target_id)
    save_data()
    await update.message.reply_text(f"🚫 تم حظر المستخدم: {target_id}")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /unban <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    if target_id in banned_users:
        banned_users.remove(target_id)
        save_data()
        await update.message.reply_text(f"✅ تم رفع الحظر عن المستخدم: {target_id}")
    else:
        await update.message.reply_text(f"❌ المستخدم {target_id} غير محظور")

# ===== SEARCH =====
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /search <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    if target_id not in all_users:
        await update.message.reply_text(f"❓ المستخدم {target_id} غير موجود في قاعدة البيانات")
        return

    status_lines = []
    if target_id in banned_users:
        status_lines.append("🚫 محظور")
    if target_id in free_users:
        status_lines.append("🎁 لديه جلسة مجانية نشطة")
    if not status_lines:
        status_lines.append("👤 مستخدم عادي")

    await update.message.reply_text(
        f"🔍 نتيجة البحث:\n\n"
        f"🆔 المعرف: {target_id}\n"
        f"الحالة: {' | '.join(status_lines)}"
    )

# ===== LISTBANNED =====
async def listbanned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if banned_users:
        banned_list = "\n".join(str(uid) for uid in banned_users)
        await update.message.reply_text(
            f"🚫 المستخدمون المحظورون ({len(banned_users)}):\n\n{banned_list}"
        )
    else:
        await update.message.reply_text("✅ لا يوجد مستخدمون محظورون حالياً")

# ===== RESETSPAM =====
async def resetspam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /resetspam <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    user_message_times.pop(target_id, None)
    await update.message.reply_text(f"✅ تم إعادة تعيين حد الرسائل للمستخدم: {target_id}")

# ===== HELP =====
async def help_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "📋 *أوامر الأدمن:*\n\n"
        "🔹 `code <الكود>` — إنشاء كود هدية جديد\n"
        "🔹 `/stats` — لوحة الإحصائيات\n"
        "🔹 `/delcode <الكود>` — حذف كود هدية\n"
        "🔹 `/adduser <id>` — منح جلسة مجانية لمستخدم\n"
        "🔹 `/removeuser <id>` — إلغاء الجلسة المجانية\n"
        "🔹 `/listusers` — عرض المستخدمين ذوي الجلسات المجانية\n"
        "🔹 `/broadcast <رسالة>` — إرسال رسالة لجميع المستخدمين\n"
        "🔹 `/search <id>` — البحث عن مستخدم وعرض حالته\n"
        "🔹 `/ban <id>` — حظر مستخدم نهائياً\n"
        "🔹 `/unban <id>` — رفع الحظر عن مستخدم\n"
        "🔹 `/listbanned` — عرض جميع المستخدمين المحظورين\n"
        "🔹 `/resetspam <id>` — إعادة تعيين حد الرسائل لمستخدم\n"
        "🔹 `/setrate <رقم>` — تعديل سعر صرف الدولار (مثال: /setrate 14500)\n"
        "🔹 `/rate` — عرض سعر الصرف الحالي والأسعار\n"
        "🔹 `/cancel` — إلغاء الجلسة النشطة والعودة للقائمة\n"
        "🔹 `<id>|<رسالة>` — الرد مباشرة على مستخدم بمعرفه\n"
        "🔹 `/help` — عرض هذه القائمة",
        parse_mode="Markdown"
    )

# ===== LISTUSERS =====
async def listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if free_users:
        users_list = "\n".join(str(uid) for uid in free_users)
        await update.message.reply_text(
            f"👤 المستخدمون الذين لديهم جلسة مجانية ({len(free_users)}):\n\n{users_list}"
        )
    else:
        await update.message.reply_text("📭 لا يوجد مستخدمون لديهم جلسة مجانية حالياً")

# ===== REMOVEUSER =====
async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /removeuser <user_id>")
        return

    try:
        target_id = int(context.args[0].strip())
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً")
        return

    if target_id in free_users:
        free_users.remove(target_id)
        save_data()
        await update.message.reply_text(f"✅ تم إلغاء الجلسة المجانية للمستخدم: {target_id}")
    else:
        await update.message.reply_text(f"❌ المستخدم {target_id} لا يملك جلسة مجانية")

# ===== BROADCAST =====
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /broadcast <الرسالة>")
        return

    msg = " ".join(context.args)
    sent = 0
    failed = 0

    await update.message.reply_text(f"📡 جاري الإرسال إلى {len(all_users)} مستخدم...")

    for uid in list(all_users):
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {msg}")
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ تم الإرسال بنجاح: {sent}\n❌ فشل: {failed}"
    )

# ===== SETRATE =====
async def setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❗ استخدم: /setrate <السعر>\nمثال: /setrate 14000")
        return

    try:
        new_rate = float(context.args[0].strip())
        if new_rate <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ السعر يجب أن يكون رقماً موجباً")
        return

    global current_rate
    current_rate = new_rate
    await update.message.reply_text(
        f"✅ تم تحديث سعر الصرف:\n\n"
        f"💵 1$ = 🇸🇾 {int(current_rate):,} ل.س\n\n"
        f"📋 الأسعار الجديدة:\n"
        f"🔮 فنجان: {fmt_price('fanjan')}\n"
        f"🌙 حلم:   {fmt_price('dream')}\n"
        f"💬 استشارة: {fmt_price('consult')}"
    )

# ===== RATE =====
async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        f"💱 سعر الصرف الحالي:\n\n"
        f"💵 1$ = 🇸🇾 {int(current_rate):,} ل.س\n\n"
        f"📋 الأسعار:\n"
        f"🔮 فنجان: {fmt_price('fanjan')}\n"
        f"🌙 حلم:   {fmt_price('dream')}\n"
        f"💬 استشارة: {fmt_price('consult')}\n\n"
        f"لتغيير السعر: /setrate <الرقم>"
    )

# ===== CANCEL =====
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ تم إلغاء الجلسة الحالية.\n\n"
        "اختر خدمة جديدة:",
        reply_markup=main_menu_keyboard()
    )

# ===== HANDLE =====
# نظام الحالات (State Machine):
#   "gift_code" → ينتظر كود الهدية
#   "fanjan"    → ينتظر وصف/صورة الفنجان
#   "dream"     → ينتظر وصف الحلم (أي نص)
#   "consult"   → ينتظر موضوع الاستشارة
#   None        → لا توجد جلسة نشطة

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    msg      = update.message
    user_id  = msg.from_user.id
    text     = (msg.text or "").strip()
    is_photo = bool(msg.photo)

    # تجاهل ما ليس نصاً ولا صورة
    if not text and not is_photo:
        return

    # ── تسجيل المستخدم ───────────────────────────────
    all_users.add(user_id)
    save_data()

    # ── الأولوية 1: فحص الحظر ────────────────────────
    if user_id in banned_users:
        await msg.reply_text("🚫 تم حظرك من استخدام هذا البوت.")
        return

    # ── الأولوية 2: فحص السبام ───────────────────────
    if user_id != ADMIN_ID and is_rate_limited(user_id):
        await msg.reply_text("⏳ أرسلت رسائل كثيرة، انتظر دقيقة ثم حاول مجدداً.")
        return
    # ===== استقبال الإيصال =====
    state = context.user_data.get("state")

    if state == "awaiting_receipt":
        if not (text or is_photo):
            return

        service = context.user_data.get("pay_service", "غير معروف")
        method  = context.user_data.get("pay_method", "غير معروف")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 إيصال دفع جديد\n\n"
                f"👤 المستخدم: {user_id}\n"
                f"🛎 الخدمة: {service}\n"
                f"💳 الطريقة: {method}"
            )
        )

        # إرسال الصورة إذا موجودة
        if is_photo:
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=msg.photo[-1].file_id,
                caption="📎 صورة الإيصال"
            )

        await msg.reply_text("📨 تم استلام الإيصال وسيتم مراجعته.")

        context.user_data["state"] = None
        return
    # ── الأولوية 3: أوامر الأدمن النصية ─────────────
    if user_id == ADMIN_ID and text:
        if text.startswith("code "):
            code = text[5:].strip()
            gift_codes.add(code)
            save_data()
            await msg.reply_text(f"🎁 تم إنشاء كود: {code}")
            return
        parts = text.split("|")
        if len(parts) == 2:
            try:
                target = int(parts[0].strip())
                await context.bot.send_message(chat_id=target, text=f"🔮 {parts[1].strip()}")
            except Exception as e:
                await msg.reply_text(f"❌ فشل الإرسال: {e}")
        return
        
    # ===== استقبال الإيصال =====
    if context.user_data.get("state") == "awaiting_receipt":
        if not (text or is_photo):
            return

        service = context.user_data.get("pay_service", "غير معروف")
        method  = context.user_data.get("pay_method", "غير معروف")

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📥 إيصال دفع جديد\n\n"
                f"👤 المستخدم: {user_id}\n"
                f"🛎 الخدمة: {service}\n"
                f"💳 الطريقة: {method}\n\n"
                f"📎 تم إرسال إيصال (صورة أو نص)"
            )
        )

        await msg.reply_text("📨 تم استلام الإيصال وسيتم مراجعته.")

        context.user_data["state"] = None
        return
        
    # ── الأولوية 4: التوجيه بناءً على الحالة ─────────
    
    state = context.user_data.get("state")

    # حالة: انتظار كود الهدية
    if state == "gift_code":
        if not text:
            await msg.reply_text("🎁 أرسل الكود نصياً من فضلك.")
            return
        context.user_data["state"] = None
        if text in used_codes:
            await msg.reply_text("❌ الكود مستخدم مسبقاً.")
            return
        if text in gift_codes:
            gift_codes.remove(text)
            used_codes.add(text)
            save_data()
            svc = context.user_data.get("selected_service", "consult")
            context.user_data["state"] = svc   # تفعيل حالة الخدمة مباشرة
            prompts = {
                "fanjan":  "🔮 تم قبول الكود!\nأرسل وصف فنجانك أو صورة منه:",
                "dream":   "🌙 تم قبول الكود!\nأرسل تفاصيل حلمك وسأفسره لك:",
                "consult": "💬 تم قبول الكود!\nاكتب موضوع استشارتك:",
            }
            await msg.reply_text(prompts.get(svc, "🎉 تم قبول الكود! أرسل طلبك 🔮"))
        else:
            await msg.reply_text("❌ كود غير صحيح.")
        return

    # حالة: قراءة فنجان (نص أو صورة)
    if state == "fanjan":
        context.user_data["state"] = None
        if is_photo:
            response = generate_fanjan_response("")
            await msg.reply_text(
                "🔮 استقبلت صورة فنجانك...\n\n" + response,
                parse_mode="Markdown"
            )
        elif text:
            await msg.reply_text(
                generate_fanjan_response(text),
                parse_mode="Markdown"
            )
        else:
            context.user_data["state"] = "fanjan"   # إعادة الحالة
            await msg.reply_text("🔮 أرسل وصفاً أو صورة من فنجانك.")
        return

    # حالة: تفسير الحلم (أي نص بدون قيود)
    if state == "dream":
        if not text:
            await msg.reply_text("🌙 أرسل وصف حلمك نصياً.")
            return
        context.user_data["state"] = None
        await msg.reply_text(
            generate_dream_response(text),
            parse_mode="Markdown"
        )
        return

    # حالة: استشارة عامة
    if state == "consult":
        if not text:
            await msg.reply_text("💬 اكتب موضوع استشارتك.")
            return
        context.user_data["state"] = None
        await msg.reply_text(
            generate_general_response(text),
            parse_mode="Markdown"
        )
        return

    # ── الأولوية 5: لا توجد حالة نشطة ───────────────
    if text:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🧠 رسالة بدون جلسة\n👤 {user_id}\n📝 {text}"
        )
    await msg.reply_text(
        "💳 اختر خدمة وأتمم الدفع أولاً.",
        reply_markup=main_menu_keyboard()
    )

# ===== APP =====
app = ApplicationBuilder().token(TOKEN).build()

# جلب سعر الصرف مباشرة عند الإطلاق ثم كل ساعة
app.job_queue.run_once(rate_updater_job, when=0)
app.job_queue.run_repeating(rate_updater_job, interval=3600, first=60)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_admin))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("delcode", delcode))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("removeuser", removeuser))
app.add_handler(CommandHandler("search", search))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("listbanned", listbanned))
app.add_handler(CommandHandler("listusers", listusers))
app.add_handler(CommandHandler("resetspam", resetspam))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("setrate", setrate))
app.add_handler(CommandHandler("rate", rate))
app.add_handler(CommandHandler("cancel", cancel))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.ALL, handle))

app.run_polling()
