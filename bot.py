import os
import re
import random
import asyncio
import threading
import time
import logging
from flask import Flask, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# ========== تنظیمات ==========
TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")

# ========== پاسخ‌های از پیش تعیین‌شده ==========
RESPONSES = {
    r"\bسلام\b|\bدرود\b|\bهی\b|\bسلامت\b": [
        "سلام! چطور می‌تونم کمکت کنم؟ 😊",
        "درود! خوش اومدی! 🌟",
        "سلام علیک! چه خبر؟ 👋",
        "سلام! وقت بخیر! ☀️",
    ],
    r"\bچطوری\b|\bحالت چطوره\b|\bچطورین\b|\bچه خبر\b": [
        "خوبم، ممنون! تو چطوری؟ 😄",
        "عالی! ممنون که پرسیدی. 🌈",
        "خوبم از اینکه پرسیدی خوشحالم! 💫",
        "خوبه! تو چی؟ 🎯",
    ],
    r"\bاسم\b|\bنام\b|\bاسمت\b": [
        "اسم من رباته! تو چی؟ 🤖",
        "منو صدا کن ربات! 📱",
        "اسم من ربات هوشمنده! 🧠",
        "من ربات بدون نامم! 😅",
    ],
    r"\bخداحافظ\b|\bبای\b|\bفعلا\b|\bخدا نگهدار\b": [
        "خداحافظ! بازم بیا! 👋",
        "بای! خوش باشی! 🌟",
        "فعلا! مواظب خودت باش! 🤗",
        "قربانت! بعداً می‌بینمت! 😘",
    ],
    r"\bمتشکرم\b|\bمرسی\b|\bممنون\b|\bسپاس\b": [
        "خواهش می‌کنم! 🤗",
        "قابل شما رو نداشت! 🙏",
        "خوشحالم که مفید بودم! 😊",
        "وظیفه‌ست! 🌺",
    ],
    r"\bچکار\b|\bچه کار\b|\bتوانایی\b|\bقابلیت\b": [
        "من می‌تونم باهات حرف بزنم و به سوالات ساده جواب بدم! 💪",
        "قدرت من در حرف زدنه! هر چی بپرسی جواب می‌دم. 🎯",
        "می‌تونم باهات چت کنم! سوال بپرس. 🤖",
        "تخصص من گفتگوه! بپرس تا جواب بدم. 💬",
    ],
    r"\bعشق\b|\bدوستت دارم\b|\bدوس\b": [
        "آها! ممنون! منم دوستت دارم! ❤️",
        "چه لطفی! منم بهت علاقه‌مندم! 💖",
        "خوشحالم که اینو گفتی! 🥰",
    ],
}

DEFAULT_RESPONSES = [
    "متوجه نشدم! می‌تونی دوباره بگی؟ 🤔",
    "اینو بلد نیستم! یه چیز دیگه بپرس. 😅",
    "آها! راستی چی گفتی؟ من حواسم پرت بود! 🙃",
    "جالب بود! ولی جوابش رو نمی‌دونم. 🤷",
    "اگه ساده‌تر بپرسی شاید بفهمم! 😊",
    "این سوال برام جدید بود! شاید دفعه بعد بتونم جواب بدم. 📚",
    "متاسفم! هنوز یادگیری رو تموم نکردم! 🧠",
]

# ========== اپلیکیشن Flask برای وب‌سایت ==========
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ربات تلگرام</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Vazir', Tahoma, Arial, sans-serif;
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        .emoji-big {
            font-size: 4em;
            display: block;
            margin-bottom: 20px;
        }
        p {
            color: #34495e;
            font-size: 1.1em;
            line-height: 1.8;
            margin: 15px 0;
        }
        .status {
            background: #27ae60;
            color: white;
            padding: 12px 30px;
            border-radius: 50px;
            display: inline-block;
            font-weight: bold;
            margin: 20px 0;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .info {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            text-align: right;
        }
        .info li {
            list-style: none;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .info li:last-child {
            border-bottom: none;
        }
        .footer {
            margin-top: 30px;
            color: #6c757d;
            font-size: 0.9em;
        }
        .badge {
            background: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <span class="emoji-big">🤖</span>
        <h1>ربات تلگرام</h1>
        <p>ربات هوشمند من با موفقیت روی Render راه‌اندازی شده!</p>
        <div class="status">✅ وضعیت: فعال و آماده به کار</div>
        
        <div class="info">
            <h3 style="color: #2c3e50; margin-bottom: 15px;">📋 اطلاعات ربات:</h3>
            <ul>
                <li>🔹 پشتیبانی از گفتگوی ساده</li>
                <li>🔹 انیمیشن پردازش پیام‌ها</li>
                <li>🔹 پاسخ به دستور /start</li>
                <li>🔹 پینگ خودکار هر ۵ دقیقه</li>
            </ul>
        </div>
        
        <p style="color: #2c3e50; font-weight: bold;">
            🚀 برای استفاده، ربات را در تلگرام پیدا کن و <code style="background: #f1f3f4; padding: 4px 8px; border-radius: 4px;">/start</code> بزن.
        </p>
        
        <div class="footer">
            <p>⚡ پینگ خودکار هر ۵ دقیقه برای جلوگیری از خوابیدن</p>
            <p><span class="badge">Python 3.14</span> <span class="badge" style="background: #3498db;">Telegram Bot API</span></p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}, 200

def run_flask():
    """اجرای Flask در یک ترد جداگانه"""
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ========== پینگ زدن به خود ==========
def ping_self():
    """هر ۵ دقیقه به خود درخواست می‌زند تا از خوابیدن جلوگیری کند"""
    while True:
        time.sleep(300)  # ۵ دقیقه
        try:
            # درخواست به آدرس محلی
            requests.get(f"http://localhost:{PORT}/ping", timeout=10)
            # درخواست به آدرس عمومی (اگر در Render باشد)
            if RENDER_URL and "your-app-name" not in RENDER_URL:
                requests.get(f"{RENDER_URL}/ping", timeout=10)
            logging.info("✅ Ping sent successfully")
        except Exception as e:
            logging.error(f"❌ Ping failed: {e}")

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
        "👋 **سلام! به ربات من خوش اومدی!**\n\n"
        "✨ این ربات می‌تونه با تو حرف بزنه! فقط کافیه یه پیام بدی تا جوابتو بده.\n\n"
        "📌 **چجوری کار می‌کنه؟**\n"
        "• هر پیامی که بفرستی، من پردازشش می‌کنم.\n"
        "• حین پردازش، یه انیمیشن کوچیک می‌بینی (۶ ثانیه با نقاط متحرک).\n"
        "• بعدش جوابتو می‌دم! (اگه بلد باشم 😅)\n\n"
        "💡 **نکته:** من یه ربات ساده‌ام، پس سوالات ساده بپرس.\n\n"
        "حالا بگو چطور می‌تونم کمکت کنم؟ 🚀"
    )
    keyboard = [
        [InlineKeyboardButton("📱 کانال ما", url="https://t.me/your_channel")],
        [InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/your_support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')

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

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به دستورات ناشناخته"""
    await update.message.reply_text(
        "متاسفم! این دستور رو نمی‌شناسم. 😅\n"
        "برای راهنمایی /start رو بزن."
    )

# ========== اجرای اصلی ==========
def main():
    # تنظیم لاگ
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.info("🚀 Starting bot...")
    
    # اجرای Flask در ترد جداگانه
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info(f"🌐 Flask server started on port {PORT}")
    
    # اجرای پینگ در ترد جداگانه
    ping_thread = threading.Thread(target=ping_self, daemon=True)
    ping_thread.start()
    logging.info("⏰ Ping thread started")
    
    # راه‌اندازی ربات تلگرام با نسخه جدید
    application = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .build()
    )
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    logging.info("🤖 Bot started polling...")
    
    # شروع polling با تنظیمات مناسب
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == "__main__":
    main()
