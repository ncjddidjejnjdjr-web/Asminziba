️:
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# === تنظیمات ===
TOKEN = os.environ.get("TOKEN")
ADMIN_IDS = [123456789, 987654321]  # آیدی عددی ادمین‌ها

logging.basicConfig(level=logging.INFO)

# === کیبورد مدیریتی ===
def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚫 بن", callback_data="ban")],
        [InlineKeyboardButton("🔓 آنبن", callback_data="unban")],
        [InlineKeyboardButton("🧹 پاک کردن", callback_data="purge")],
        [InlineKeyboardButton("📢 همگانی", callback_data="broadcast")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# === استارت ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return
    await update.message.reply_text("👋 سلام ادمین!", reply_markup=admin_keyboard())

# === مدیریت دکمه‌ها ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.edit_message_text("⛔ شما ادمین نیستید.")
        return

    data = query.data
    actions = {
        "ban": "👤 آیدی یا یوزرنیم رو برای بن بفرست:",
        "unban": "👤 آیدی یا یوزرنیم رو برای آنبن بفرست:",
        "purge": "🔢 تعداد پیام‌ها رو وارد کن (حداکثر ۱۰۰):",
        "broadcast": "📝 متن پیام همگانی رو بفرست:"
    }
    
    if data in actions:
        await query.edit_message_text(actions[data])
        context.user_data['action'] = data
    elif data == "stats":
        try:
            members = await context.bot.get_chat_member_count(update.effective_chat.id)
            await query.edit_message_text(
                f"📊 آمار گروه:\n"
                f"نام: {update.effective_chat.title}\n"
                f"تعداد: {members} نفر"
            )
        except:
            await query.edit_message_text("❌ خطا در دریافت آمار.")

# === پردازش متن ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    action = context.user_data.get('action')
    if not action:
        await update.message.reply_text("先从 دکمه‌های منو استفاده کن.")
        return

    chat_id = update.effective_chat.id
    text = update.message.text

    try:
        if action == "ban":
            await context.bot.ban_chat_member(chat_id, int(text))
            await update.message.reply_text(f"✅ کاربر {text} بن شد.")
        
        elif action == "unban":
            await context.bot.unban_chat_member(chat_id, int(text))
            await update.message.reply_text(f"✅ کاربر {text} آنبن شد.")
        
        elif action == "purge":
            count = min(int(text), 100)
            for i in range(count):
                await context.bot.delete_message(chat_id, update.message.message_id - i - 1)
            await update.message.reply_text(f"🧹 {count} پیام پاک شد.")
        
        elif action == "broadcast":
            await context.bot.send_message(chat_id, f"📢 {text}")
            await update.message.reply_text("✅ پیام همگانی ارسال شد.")
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً عدد یا آیدی معتبر وارد کن.")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
    
    context.user_data['action'] = None

# === اجرا ===
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # ====== روش دیپلوی روی Render ======
    port = int(os.environ.get("PORT", 8443))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    )
    
    # برای تست لوکال این خط رو جایگزین کن:
    # app.run_polling()

if name == "main":
    main()
