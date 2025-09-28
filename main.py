import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import TELEGRAM_TOKEN
from admin import manage_users
from analysis import twelve_api, technical, fundamental, elliott_waves
from image_analysis import analyze_image
import pandas as pd

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def is_authorized(user_id):
    users = manage_users.list_users()
    return user_id in users

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        update.message.reply_text("❌ ليس لديك صلاحية استخدام البوت.")
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

    update.message.reply_text("اختر الأداة:", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_authorized(user_id):
        query.answer("❌ ليس لديك صلاحية.")
        return
    query.answer()
    data = query.data

    if data.startswith('analyze_'):
        symbol = data.split('_')[1]
        query.edit_message_text(f"جاري تحليل {symbol}... يرجى الانتظار.")
        ohlc_data = twelve_api.get_ohlc(symbol)
        if ohlc_data:
            df = pd.DataFrame(ohlc_data)
            df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
            tech_analysis = technical.full_technical_analysis(df)
            fund_analysis = fundamental.get_fundamental_analysis(symbol)
            elliott = elliott_waves.analyze_elliott(df)
            message = f"✅ التحليل الكامل لـ {symbol}:\n\n{tech_analysis}\n{fund_analysis}\n{elliott}\n💡 الصفقة المقترحة: ...\n- نقطة الدخول: ...\n- وقف الخسارة: ...\n- الأهداف: ...\n- سبب الدخول: تحليل متعدد المؤشرات"
        else:
            message = "لا توجد بيانات حالياً. انتظر لحظة ثم أعد المحاولة."
        query.message.reply_text(message)

def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        update.message.reply_text("❌ ليس لديك صلاحية استخدام البوت.")
        return
    photo_file = update.message.photo[-1].get_file()
    photo_path = f"temp_chart_{user_id}.jpg"
    photo_file.download(photo_path)
    analysis_result = analyze_image.analyze_chart(photo_path)
    update.message.reply_text(analysis_result)

def add_user_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != manage_users.list_users()[0]:
        update.message.reply_text("❌ لا يمكنك استخدام هذا الأمر.")
        return
    try:
        new_user_id = int(context.args[0])
        if manage_users.add_user(new_user_id):
            update.message.reply_text(f"✅ تم إضافة المستخدم {new_user_id}")
        else:
            update.message.reply_text("المستخدم موجود بالفعل")
    except:
        update.message.reply_text("❌ استخدم: /add_user <user_id>")

def remove_user_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != manage_users.list_users()[0]:
        update.message.reply_text("❌ لا يمكنك استخدام هذا الأمر.")
        return
    try:
        rem_user_id = int(context.args[0])
        if manage_users.remove_user(rem_user_id):
            update.message.reply_text(f"✅ تم إزالة المستخدم {rem_user_id}")
        else:
            update.message.reply_text("❌ المستخدم غير موجود")
    except:
        update.message.reply_text("❌ استخدم: /remove_user <user_id>")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_user", add_user_cmd))
    dp.add_handler(CommandHandler("remove_user", remove_user_cmd))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()