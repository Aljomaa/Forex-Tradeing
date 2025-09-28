import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# --- تحميل متغيرات البيئة ---
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is not set! Check your .env or Render environment variables.")
if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL is not set! Check your .env or Render environment variables.")

# ---- التحقق من وجود الملفات المهمة ----
try:
    from config import TELEGRAM_TOKEN as _TT  # للتحقق فقط
    from admin import manage_users
    from analysis import twelve_api, technical, fundamental, elliott_waves
    from image_analysis import analyze_image
except ImportError as e:
    raise ImportError(f"❌ ملف مفقود أو غير صحيح: {e}. تأكد أن كل الوحدات موجودة.")

import pandas as pd

# --- رسائل ثابتة ---
MSG_UNAUTHORIZED = "❌ ليس لديك صلاحية استخدام البوت."
MSG_ADMIN_ONLY = "❌ هذا الأمر حصري للمشرفين."
MSG_COMMAND_FORMAT = "❌ استخدم: {usage}"
MSG_ADDED_USER = "✅ تم إضافة المستخدم {uid}"
MSG_REMOVED_USER = "✅ تم إزالة المستخدم {uid}"
MSG_USER_EXISTS = "المستخدم موجود بالفعل"
MSG_USER_NOT_FOUND = "❌ المستخدم غير موجود"
MSG_NO_DATA = "لا توجد بيانات حالياً. انتظر قليلاً ثم أعد المحاولة."
MSG_INVALID_IMAGE = "❌ لا توجد صورة صالحة."

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- صلاحيات ---
def is_authorized(user_id):
    return user_id in manage_users.list_users()

def is_super_admin(user_id):
    return manage_users.is_super_admin(user_id)

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(MSG_UNAUTHORIZED)
        return

    keyboard = [
        [InlineKeyboardButton("EUR/USD", callback_data='analyze_EUR/USD'),
         InlineKeyboardButton("GBP/USD", callback_data='analyze_GBP/USD')],
        [InlineKeyboardButton("USD/JPY", callback_data='analyze_USD/JPY'),
         InlineKeyboardButton("USD/CHF", callback_data='analyze_USD/CHF')],
        [InlineKeyboardButton("AUD/USD", callback_data='analyze_AUD/USD'),
         InlineKeyboardButton("NZD/USD", callback_data='analyze_NZD/USD')],
        [InlineKeyboardButton("USD/CAD", callback_data='analyze_USD/CAD'),
         InlineKeyboardButton("EUR/GBP", callback_data='analyze_EUR/GBP')],
        [InlineKeyboardButton("EUR/JPY", callback_data='analyze_EUR/JPY'),
         InlineKeyboardButton("GBP/JPY", callback_data='analyze_GBP/JPY')],
        [InlineKeyboardButton("AUD/JPY", callback_data='analyze_AUD/JPY'),
         InlineKeyboardButton("EUR/CHF", callback_data='analyze_EUR/CHF')],
        [InlineKeyboardButton("GBP/CHF", callback_data='analyze_GBP/CHF'),
         InlineKeyboardButton("NZD/JPY", callback_data='analyze_NZD/JPY')],
        [InlineKeyboardButton("CAD/JPY", callback_data='analyze_CAD/JPY')],
        [InlineKeyboardButton("الذهب", callback_data='analyze_XAU/USD'),
         InlineKeyboardButton("الفضة", callback_data='analyze_XAG/USD'),
         InlineKeyboardButton("النفط", callback_data='analyze_USOIL')]
    ]

    await update.message.reply_text(
        "اختر الأداة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 بوت التحليل الفني والفوندمنتال للمتابعة السريعة!\n\n"
        "/start - القائمة الرئيسية\n"
        "/add_user <user_id> - إضافة مستخدم (أدمن فقط)\n"
        "/remove_user <user_id> - إزالة مستخدم (أدمن فقط)\n"
        "/help - عرض هذه الرسالة\n\n"
        "يمكنك إرسال صورة شارت وسيتم تحليلها تلقائياً."
    )
    await update.message.reply_text(msg)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.answer(MSG_UNAUTHORIZED, show_alert=True)
        return
    await query.answer()
    data = query.data

    if data.startswith('analyze_'):
        symbol = data.split('_', 1)[1]
        await query.edit_message_text(f"جاري تحليل {symbol}... يرجى الانتظار.")
        ohlc_data = twelve_api.get_ohlc(symbol)
        if ohlc_data:
            df = pd.DataFrame(ohlc_data)
            try:
                df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
                tech_analysis = technical.full_technical_analysis(df)
                fund_analysis = fundamental.get_fundamental_analysis(symbol)
                elliott = elliott_waves.analyze_elliott(df)
                message = (
                    f"✅ التحليل الكامل لـ {symbol}:\n\n"
                    f"{tech_analysis}\n"
                    f"{fund_analysis}\n"
                    f"{elliott}\n"
                    "💡 الصفقة المقترحة: ...\n- نقطة الدخول: ...\n- وقف الخسارة: ...\n- جني الأرباح: ..."
                )
            except Exception as ex:
                logging.error(f"Error in analysis: {ex}")
                message = "⚠️ حصل خطأ أثناء التحليل! تأكد من صحة البيانات أو حاول لاحقاً."
        else:
            message = MSG_NO_DATA
        await query.message.reply_text(message)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text(MSG_UNAUTHORIZED)
        return
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"temp_chart_{user_id}.jpg"
    await photo_file.download_to_drive(photo_path)
    analysis_result = analyze_image.analyze_chart(photo_path)
    await update.message.reply_text(analysis_result)

async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await update.message.reply_text(MSG_ADMIN_ONLY)
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(MSG_COMMAND_FORMAT.format(usage="/add_user <user_id>"))
        return
    new_user_id = int(context.args[0])
    if manage_users.add_user(new_user_id):
        await update.message.reply_text(MSG_ADDED_USER.format(uid=new_user_id))
    else:
        await update.message.reply_text(MSG_USER_EXISTS)

async def remove_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await update.message.reply_text(MSG_ADMIN_ONLY)
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(MSG_COMMAND_FORMAT.format(usage="/remove_user <user_id>"))
        return
    rem_user_id = int(context.args[0])
    if manage_users.remove_user(rem_user_id):
        await update.message.reply_text(MSG_REMOVED_USER.format(uid=rem_user_id))
    else:
        await update.message.reply_text(MSG_USER_NOT_FOUND)

# ---- Webhook & Flask ----
flask_app = Flask(__name__)

def create_application():
    """إنشاء تطبيق Telegram مرة واحدة"""
    return Application.builder().token(TELEGRAM_TOKEN).build()

def setup_handlers(app):
    """إعداد handlers للتطبيق"""
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("remove_user", remove_user_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

@flask_app.route("/")
def index():
    return "Bot is alive!"

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # إنشاء التطبيق إذا لم يكن موجوداً
        if 'app' not in globals():
            global app
            app = create_application()
            setup_handlers(app)
            # بدء الاستماع للتحديثات
            app.initialize()
        
        update = Update.de_json(request.get_json(force=True), app.bot)
        app.update_queue.put(update)
        return "ok"
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return "error", 500

def main():
    global app
    
    try:
        # إنشاء وتجهيز التطبيق
        app = create_application()
        setup_handlers(app)
        
        # إعداد webhook
        PORT = int(os.environ.get("PORT", 10000))
        
        # التأكد من أن التطبيق جاهز
        app.initialize()
        
        # تشغيل webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
            web_app=flask_app
        )
        
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
