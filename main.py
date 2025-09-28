import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import TELEGRAM_TOKEN
from admin import manage_users
from analysis import twelve_api, technical, fundamental, elliott_waves
from image_analysis import analyze_image
import pandas as pd

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# رسائل موحدة
MSG_UNAUTHORIZED = "❌ ليس لديك صلاحية استخدام البوت."
MSG_ADMIN_ONLY = "❌ هذا الأمر حصري للمشرفين."
MSG_COMMAND_FORMAT = "❌ استخدم: {usage}"
MSG_ADDED_USER = "✅ تم إضافة المستخدم {uid}"
MSG_REMOVED_USER = "✅ تم إزالة المستخدم {uid}"
MSG_USER_EXISTS = "المستخدم موجود بالفعل"
MSG_USER_NOT_FOUND = "❌ المستخدم غير موجود"
MSG_NO_DATA = "لا توجد بيانات حالياً. انتظر قليلاً ثم أعد المحاولة."
MSG_INVALID_IMAGE = "❌ لا توجد صورة صالحة."

def is_authorized(user_id):
    return user_id in manage_users.list_users()

def is_super_admin(user_id):
    return manage_users.is_super_admin(user_id)

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        update.message.reply_text(MSG_UNAUTHORIZED)
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

def help_cmd(update: Update, context: CallbackContext):
    msg = (
        "🤖 بوت التحليل الفني والفوندمنتال للمتابعة السريعة!\n\n"
        "/start - القائمة الرئيسية\n"
        "/add_user <user_id> - إضافة مستخدم (أدمن فقط)\n"
        "/remove_user <user_id> - إزالة مستخدم (أدمن فقط)\n"
        "/help - عرض هذه الرسالة\n\n"
        "يمكنك إرسال صورة شارت وسيتم تحليلها تلقائياً."
    )
    update.message.reply_text(msg)

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_authorized(user_id):
        query.answer(MSG_UNAUTHORIZED, show_alert=True)
        return
    query.answer()
    data = query.data

    if data.startswith('analyze_'):
        symbol = data.split('_', 1)[1]
        query.edit_message_text(f"جاري تحليل {symbol}... يرجى الانتظار.")
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
        query.message.reply_text(message)

def handle_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        update.message.reply_text(MSG_UNAUTHORIZED)
        return
    photo_file = update.message.photo[-1].get_file()
    photo_path = f"temp_chart_{user_id}.jpg"
    photo_file.download(photo_path)
    analysis_result = analyze_image.analyze_chart(photo_path)
    update.message.reply_text(analysis_result)

def add_user_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        update.message.reply_text(MSG_ADMIN_ONLY)
        return
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text(MSG_COMMAND_FORMAT.format(usage="/add_user <user_id>"))
        return
    new_user_id = int(context.args[0])
    if manage_users.add_user(new_user_id):
        update.message.reply_text(MSG_ADDED_USER.format(uid=new_user_id))
    else:
        update.message.reply_text(MSG_USER_EXISTS)

def remove_user_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        update.message.reply_text(MSG_ADMIN_ONLY)
        return
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text(MSG_COMMAND_FORMAT.format(usage="/remove_user <user_id>"))
        return
    rem_user_id = int(context.args[0])
    if manage_users.remove_user(rem_user_id):
        update.message.reply_text(MSG_REMOVED_USER.format(uid=rem_user_id))
    else:
        update.message.reply_text(MSG_USER_NOT_FOUND)

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("add_user", add_user_cmd))
    dp.add_handler(CommandHandler("remove_user", remove_user_cmd))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
