import os
import re
import random
import asyncio
import threading
import time
import logging
from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# ========== تنظیمات ==========
TOKEN = os.environ.get("BOT_TOKEN")  # توکن را در Render به عنوان متغیر محیطی تنظیم کن
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")

# ========== پاسخ‌های از پیش تعیین‌شده ==========
RESPONSES = {
    r"\bسلام\b|\bدرود\b|\bهی\b": [
        "سلام! چطور می‌تونم کمکت کنم؟",
        "درود! خوش اومدی!",
        "سلام علیک! چه خبر؟",
    ],
    r"\bچطوری\b|\bحالت چطوره\b|\bچطورین\b": [
        "خوبم، ممنون! تو چطوری؟",
        "عالی! ممنون که پرسیدی.",
        "خوبم از اینکه پرسیدی خوشحالم!",
    ],
    r"\bاسم\b|\bنام\b": [
        "اسم من رباته! تو چی؟",
        "منو صدا کن ربات!",
        "اسم من ربات هوشمنده!",
    ],
    r"\bخداحافظ\b|\bبای\b|\bفعلا\b": [
        "خداحافظ! بازم بیا!",
        "بای! خوش باشی!",
        "فعلا! مواظب خودت باش!",
    ],
    r"\bمتشکرم\b|\bمرسی\b|\bممنون\b": [
        "خواهش می‌کنم!",
        "قابل شما رو نداشت!",
        "خوشحالم که مفید بودم!",
    ],
    r"\bچکار\b|\bچه کار\b|\bتوانایی\b": [
        "من می‌تونم باهات حرف بزنم و به سوالات ساده جواب بدم!",
        "قدرت من در حرف زدنه! هر چی بپرسی جواب می‌دم.",
        "می‌تونم باهات چت کنم! سوال بپرس.",
    ],
}

DEFAULT_RESPONSES = [
    "متوجه نشدم! می‌تونی دوباره بگی؟",
    "اینو بلد نیستم! یه چیز دیگه بپرس.",
    "آها! راستی چی گفتی؟ من حواسم پرت بود!",
    "جالب بود! ولی جوابش رو نمی‌دونم.",
    "اگه ساده‌تر بپرسی شاید بفهمم!",
]

# ========== اپلیکیشن Flask برای وب‌سایت ==========
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>ربات تلگرام</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
        h1 { color: #2c3e50; }
        p { color: #34495e; }
        .status { background: #27ae60; color: white; padding: 10px; border-radius: 5px; display: inline-block; }
    </style>
</head>
<body>
    <h1>🤖 ربات تلگرام در حال اجراست!</h1>
    <p>ربات با موفقیت روی Render راه‌اندازی شده.</p>
    <div class="status">✅ وضعیت: فعال</div>
    <p style="margin-top: 20px;">برای استفاده، ربات را در تلگرام پیدا کن و /start بزن.</p>
    <p><small>پینگ خودکار هر ۵ دقیقه برای جلوگیری از خوابیدن.</small></p>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/ping')
def ping():
    return "pong", 200

def run_flask():
    """اجرای Flask در یک ترد جداگانه"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ========== پینگ زدن به خود ==========
def ping_self():
    """هر ۵ دقیقه به خود درخواست می‌زند تا از خوابیدن جلوگیری کند"""
    while True:
        time.sleep(300)  # ۵ دقیقه
        try:
            # ابتدا آدرس محلی (برای اطمینان از اینکه سرور پاسخ می‌دهد)
            requests.get(f"http://localhost:{PORT}/ping", timeout=5)
            # سپس آدرس عمومی (اگر در Render باشد)
            if RENDER_URL and "your-app-name" not in RENDER_URL:
                requests.get(f"{RENDER_URL}/ping", timeout=5)
            logging.info("Ping sent successfully")
        except Exception as e:
            logging.error(f"Ping failed: {e}")

# ========== توابع ربات ==========
def get_response(text: str) -> str:
    """پیدا کردن پاسخ مناسب بر اساس متن ورودی"""
    text = text.strip()
    for pattern, responses in RESPONSES.items():
        if re.search(pattern, text, re.IGNORECASE):
            return random.choice(responses)
    return random.choice(DEFAULT_RESPONSES)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    welcome_msg = (
        "👋 سلام! به ربات من خوش اومدی!\n\n"
        "✨ این ربات می‌تونه با تو حرف بزنه! فقط کافیه یه پیام بدی تا جوابتو بده.\n\n"
        "📌 **چجوری کار می‌کنه؟**\n"
        "• هر پیامی که بفرستی، من پردازشش می‌کنم.\n"
        "• حین پردازش، یه انیمیشن کوچیک می‌بینی (۶ ثانیه با نقاط متحرک).\n"
        "• بعدش جوابتو می‌دم! (اگه بلد باشم 😅)\n\n"
        "💡 **نکته:** من یه ربات ساده‌ام، پس سوالات ساده بپرس.\n\n"
        "حالا بگو چطور می‌تونم کمکت کنم؟ 🚀"
    )
    await update.message.reply_text(welcome_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر با انیمیشن"""
    user_text = update.message.text
    
    # ===== انیمیشن پردازش (۶ ثانیه) =====
    # پیام اولیه با یک نقطه
    msg = await update.message.reply_text("در حال پردازش.")
    
    # به‌روزرسانی هر ثانیه با اضافه کردن نقطه
    for i in range(2, 7):  # از ۲ تا ۶ (چون اولی یک نقطه داشت)
        await asyncio.sleep(1)
        dots = "." * i
        await msg.edit_text(f"در حال پردازش{dots}")
    
    # ===== پاسخ نهایی =====
    response = get_response(user_text)
    await msg.edit_text(response)

# ========== اجرای اصلی ==========
def main():
    # تنظیم لاگ
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # اجرای Flask در ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask server started on port %s", PORT)
    
    # اجرای پینگ در ترد جداگانه
    ping_thread = threading.Thread(target=ping_self, daemon=True)
    ping_thread.start()
    logging.info("Ping thread started")
    
    # راه‌اندازی ربات تلگرام
    application = Application.builder().token(TOKEN).build()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot started polling...")
    # اجرای polling (non-blocking نیست، اما چون در ترد اصلی اجرا می‌شود اشکالی ندارد)
    application.run_polling()

if __name__ == "__main__":
    main()
