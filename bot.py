import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

# ==============================
# 🔴 اعدادات
# ==============================

TOKEN = "8611712972:AAGKAqIV8CSUXI_E5t9nEOnbf-DzQCSLjQg"
ADMIN_ID = 123456789  # 🔴 حط الايدي مالك

bot = telebot.TeleBot(TOKEN)

SUBJECTS = [
    "grammar",
    "phonetics",
    "reading",
    "speaking",
    "psychology",
    "education",
    "arabic",
    "human_rights",
    "computer",
    "writing"
]

NAMES = {
    "grammar": "📘 Grammar",
    "phonetics": "🔊 Phonetics",
    "reading": "📖 Reading",
    "speaking": "🗣 Speaking",
    "psychology": "🧠 علم نفس",
    "education": "🏫 اسس تربية",
    "arabic": "✍️ عربي",
    "human_rights": "⚖️ حقوق الانسان",
    "computer": "💻 حاسبات",
    "writing": "📝 Writing"
}

TYPES = {
    "files": "📄 ملفات",
    "questions": "❓ اسئلة"
}

# ==============================
# 📦 DB
# ==============================

conn = sqlite3.connect("files.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT,
    type TEXT,
    file_id TEXT
)
""")
conn.commit()

user_state = {}

# ==============================
# 🚀 start
# ==============================

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup(row_width=2)

    buttons = [InlineKeyboardButton(NAMES[s], callback_data=s) for s in SUBJECTS]
    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "📚 *اختر المادة:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ==============================
# 📚 مادة
# ==============================

@bot.callback_query_handler(func=lambda call: call.data in SUBJECTS)
def subject_menu(call):
    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton("📄 ملفات", callback_data=f"{call.data}_files"),
        InlineKeyboardButton("❓ اسئلة", callback_data=f"{call.data}_questions")
    )

    bot.edit_message_text(
        "📂 *اختر النوع:*",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ==============================
# 📤 عرض المحتوى بشكل جميل
# ==============================

@bot.callback_query_handler(func=lambda call: "_files" in call.data or "_questions" in call.data)
def show_content(call):
    subject, type_ = call.data.split("_")

    cursor.execute(
        "SELECT file_id FROM files WHERE subject=? AND type=?",
        (subject, type_)
    )
    results = cursor.fetchall()

    if not results:
        bot.answer_callback_query(call.id, "🚫 ماكو محتوى حالياً", show_alert=True)
        return

    bot.send_message(
        call.message.chat.id,
        f"📥 *{TYPES[type_]} - {NAMES[subject]}*\n\nجارٍ الإرسال...",
        parse_mode="Markdown"
    )

    for i, row in enumerate(results, 1):
        bot.send_document(call.message.chat.id, row[0])

# ==============================
# 🔐 لوحة التحكم
# ==============================

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ إضافة ملف", callback_data="add_file"))

    bot.send_message(message.chat.id, "⚙️ لوحة التحكم:", reply_markup=markup)

# ==============================
# ➕ اختيار مادة للإضافة
# ==============================

@bot.callback_query_handler(func=lambda call: call.data == "add_file")
def choose_subject(call):
    if call.from_user.id != ADMIN_ID:
        return

    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(NAMES[s], callback_data=f"add_{s}") for s in SUBJECTS]
    markup.add(*buttons)

    bot.send_message(call.message.chat.id, "📚 اختر المادة:", reply_markup=markup)

# ==============================
# ➕ اختيار نوع
# ==============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_"))
def choose_type(call):
    if call.from_user.id != ADMIN_ID:
        return

    subject = call.data.split("_")[1]

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📄 ملفات", callback_data=f"upload_{subject}_files"),
        InlineKeyboardButton("❓ اسئلة", callback_data=f"upload_{subject}_questions")
    )

    bot.send_message(call.message.chat.id, "📂 اختر النوع:", reply_markup=markup)

# ==============================
# 📥 انتظار رفع ملف
# ==============================

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_"))
def wait_file(call):
    if call.from_user.id != ADMIN_ID:
        return

    _, subject, type_ = call.data.split("_")

    user_state[call.from_user.id] = (subject, type_)

    bot.send_message(call.message.chat.id, "📤 ارسل الملف الآن")

# ==============================
# 📎 استلام الملف من الادمن
# ==============================

@bot.message_handler(content_types=['document'])
def receive_file(message):
    if message.from_user.id != ADMIN_ID:
        return

    if message.from_user.id not in user_state:
        return

    subject, type_ = user_state[message.from_user.id]

    file_id = message.document.file_id

    cursor.execute(
        "INSERT INTO files (subject, type, file_id) VALUES (?, ?, ?)",
        (subject, type_, file_id)
    )
    conn.commit()

    bot.send_message(message.chat.id, "✅ تم حفظ الملف")

    del user_state[message.from_user.id]

# ==============================
# ▶️ تشغيل
# ==============================

print("✅ Bot running...")
bot.infinity_polling()
